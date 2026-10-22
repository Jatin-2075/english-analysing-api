import uuid
import re
from difflib import SequenceMatcher

import requests

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database.database import Base, engine, get_db
from .schemas.models import AssessmentFeedback, DictionaryWord, WordFeedback
from .schemas.schemas import (
    AssessmentFeedbackCreate,
    DictionaryWordCreate,
    WordFeedbackCreate,
)
from .services.audio_to_text import audio_duration_seconds, speech_to_text
from .services.web_mp3_audio_converter import webm_to_mp3
from .services.word_per_min import word_per_min
from .services.pause_detection import analyze_pauses
from .services.grammer_analysis import analyze_grammar
from .services.filler_word import analyze_fillers
from .services.fluency import analyze_fluency
from .services.feedback_service import (
    get_confirmed_word_corrections,
    save_assessment_feedback,
    save_word_feedback,
)
from .services.name_correction import build_word_suggestion, confirm_word
from .services.saved_corrections import apply_saved_corrections

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="English Assessment")


@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://frontend-xi-one-33.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "running"}


@app.post("/transcribe")
async def transcribe_audio_api(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    supported_extensions = (
        ".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg", ".flac"
    )
    if not file.filename or not file.filename.lower().endswith(supported_extensions):
        raise HTTPException(
            status_code=400,
            detail="Upload an MP3, WAV, M4A, MP4, WebM, OGG, or FLAC file",
        )

    audio_bytes = await file.read()
    await file.close()

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Audio file is empty")

    try:
        if file.filename.lower().endswith(".webm"):
            audio_bytes = webm_to_mp3(audio_bytes)

        dictionary_words = db.query(DictionaryWord).order_by(DictionaryWord.word).all()
        prompt = ", ".join(word.word for word in dictionary_words)
        audio_duration = audio_duration_seconds(audio_bytes)
        transcript = speech_to_text(audio_bytes, initial_prompt=prompt or None)

        if not transcript.strip():
            raise HTTPException(status_code=422, detail="No speech found")


        original_transcript = transcript
        transcript, corrections_applied = apply_saved_corrections(db, transcript)
        dictionary_suggestions = _dictionary_suggestions(transcript, dictionary_words)

        pace_result = word_per_min(transcript, audio_duration)
        pause_result = analyze_pauses(audio_bytes)
        grammar_result = analyze_grammar(transcript)
        filler_result = analyze_fillers(transcript)

        total_pause_duration = sum(
            pause_result["pause_durations_seconds"]
        )

        fluency_result = analyze_fluency(
            transcript,
            pause_result["pause_count"],
            total_pause_duration,
            audio_duration,
            pace_result["words_per_minute"],
            filler_result["filler_rate_percent"],
        )

        return {
            "assessment_id": uuid.uuid4().hex,
            "transcript": transcript,
            "original_transcript": original_transcript,
            "corrections_applied": corrections_applied,
            "dictionary_suggestions": dictionary_suggestions,
            "analysis": {
                "pace": pace_result,
                "pauses": pause_result,
                "grammar": grammar_result,
                "filler_words": filler_result,
                "fluency": fluency_result,
            },
        }

    except HTTPException:
        raise
    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="External analysis service unavailable",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as e:
        logger.exception("Audio analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


class TextRequest(BaseModel):
    text: str


@app.post("/analyze-text")
def analyze_text(request: TextRequest):
    transcript = request.text.strip()

    if not transcript:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        grammar_result = analyze_grammar(transcript)
        filler_result = analyze_fillers(transcript)

        return {
            "assessment_id": uuid.uuid4().hex,
            "text": transcript,
            "analysis": {
                "grammar": grammar_result,
                "filler_words": filler_result,
            },
        }

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Grammar analysis service unavailable",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dictionary")
def read_dictionary(db: Session = Depends(get_db)):
    return [
        {"id": item.id, "word": item.word, "created_at": item.created_at}
        for item in db.query(DictionaryWord).order_by(DictionaryWord.word).all()
    ]


@app.post("/dictionary", status_code=201)
def create_dictionary_word(
    request: DictionaryWordCreate,
    db: Session = Depends(get_db),
):
    word = request.word.strip()
    normalized_word = word.casefold()
    if not word:
        raise HTTPException(status_code=400, detail="Word cannot be empty")
    existing = db.query(DictionaryWord).filter(
        DictionaryWord.normalized_word == normalized_word
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Word already exists")
    entry = DictionaryWord(word=word, normalized_word=normalized_word)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "word": entry.word, "created_at": entry.created_at}


@app.delete("/dictionary/{word_id}", status_code=204)
def delete_dictionary_word(word_id: int, db: Session = Depends(get_db)):
    entry = db.query(DictionaryWord).filter(DictionaryWord.id == word_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Dictionary word not found")
    db.delete(entry)
    db.commit()


def _dictionary_suggestions(
    transcript: str,
    dictionary_words: list[DictionaryWord],
) -> list[dict]:
    transcript_words = re.findall(
        r"[^\W\d_]+(?:['’-][^\W\d_]+)*",
        transcript,
        re.UNICODE,
    )
    suggestions = []
    seen = set()
    for token in transcript_words:
        for entry in dictionary_words:
            if token.casefold() == entry.normalized_word:
                continue
            similarity = SequenceMatcher(
                None,
                token.casefold(),
                entry.normalized_word,
            ).ratio()
            if similarity >= 0.82 and entry.normalized_word not in seen:
                suggestions.append({
                    "heard": token,
                    "suggested": entry.word,
                    "confidence": round(similarity, 2),
                })
                seen.add(entry.normalized_word)
    return suggestions


class WordSuggestionRequest(BaseModel):
    original_word: str
    suggested_word: str | None = None


class WordConfirmationRequest(BaseModel):
    original_word: str
    suggested_word: str | None = None
    confirmed_word: str


@app.post("/name-suggestion")
def name_suggestion(request: WordSuggestionRequest):
    try:
        return build_word_suggestion(
            request.original_word,
            request.suggested_word,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/name-confirmation")
def name_confirmation(request: WordConfirmationRequest):
    try:
        return confirm_word(
            request.original_word,
            request.suggested_word,
            request.confirmed_word,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/feedback/words")
def create_word_feedback(
    feedback: WordFeedbackCreate,
    db: Session = Depends(get_db),
):
    saved_feedback = save_word_feedback(
        db,
        original_word=feedback.original_word,
        suggested_word=feedback.suggested_word,
        confirmed_word=feedback.confirmed_word,
        accepted=feedback.accepted,
        context=feedback.context,
        is_name=feedback.is_name,
    )
    return _word_feedback_response(saved_feedback)


@app.get("/feedback/words/{original_word}")
def read_word_feedback(original_word: str, db: Session = Depends(get_db)):
    corrections = get_confirmed_word_corrections(db, original_word)
    return [_word_feedback_response(correction) for correction in corrections]


@app.post("/feedback/assessments")
def create_assessment_feedback(
    feedback: AssessmentFeedbackCreate,
    db: Session = Depends(get_db),
):
    try:
        saved_feedback = save_assessment_feedback(
            db,
            assessment_id=feedback.assessment_id,
            rating=feedback.rating,
            original_score=feedback.original_score,
            suggested_score=feedback.suggested_score,
            reason=feedback.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _assessment_feedback_response(saved_feedback)


def _word_feedback_response(feedback: WordFeedback) -> dict:
    return {
        "id": feedback.id,
        "original_word": feedback.original_word,
        "suggested_word": feedback.suggested_word,
        "confirmed_word": feedback.confirmed_word,
        "accepted": feedback.accepted,
        "context": feedback.context,
        "is_name": feedback.is_name,
        "created_at": feedback.created_at,
    }


def _assessment_feedback_response(feedback: AssessmentFeedback) -> dict:
    return {
        "id": feedback.id,
        "assessment_id": feedback.assessment_id,
        "rating": feedback.rating,
        "original_score": feedback.original_score,
        "suggested_score": feedback.suggested_score,
        "reason": feedback.reason,
        "created_at": feedback.created_at,
    }