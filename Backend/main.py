import requests

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

if __package__:
    from .services.audio_to_text import audio_duration_seconds, speech_to_text
    from .services.audio_converter import webm_to_mp3
    from .services.word_per_min import word_per_min
    from .services.pause_detection import analyze_pauses
    from .services.grammer_analysis import analyze_grammar
    from .services.filler_word import analyze_fillers
    from .services.fluency import analyze_fluency
else:
    from services.audio_to_text import audio_duration_seconds, speech_to_text
    from services.audio_converter import webm_to_mp3
    from services.word_per_min import word_per_min
    from services.pause_detection import analyze_pauses
    from services.grammer_analysis import analyze_grammar
    from services.filler_word import analyze_fillers
    from services.fluency import analyze_fluency

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="English Assessment")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://frontend-xi-one-33.vercel.app/",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "running"}


@app.post("/transcribe")
async def transcribe_audio_api(file: UploadFile = File(...)):
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
        if not file.filename.lower().endswith(".mp3"):
            audio_bytes = webm_to_mp3(audio_bytes)

        audio_duration = audio_duration_seconds(audio_bytes)
        transcript = speech_to_text(audio_bytes)

        if not transcript.strip():
            raise HTTPException(status_code=422, detail="No speech found")

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
        )

        return {
            "transcript": transcript,
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