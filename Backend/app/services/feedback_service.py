from sqlalchemy import func
from sqlalchemy.orm import Session

from ..schemas.models import WordFeedback, AssessmentFeedback


def save_word_feedback(db: Session, original_word: str, suggested_word: str | None = None, confirmed_word: str | None = None, accepted: bool | None = None, context: str | None = None, is_name: bool = False) -> WordFeedback:
    normalized_original = original_word.strip()
    db.query(WordFeedback).filter(
        func.lower(WordFeedback.original_word) == normalized_original.lower(),
    ).delete(synchronize_session=False)
    feedback = WordFeedback(
        original_word=normalized_original,
        suggested_word=suggested_word.strip() if suggested_word else None,
        confirmed_word=confirmed_word.strip() if confirmed_word else None,
        accepted=accepted,
        context=context,
        is_name=is_name,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


def save_assessment_feedback(db: Session, assessment_id: str, rating: int, original_score: float | None = None, suggested_score: float | None = None, reason: str | None = None) -> AssessmentFeedback:
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5.")

    feedback = AssessmentFeedback(
        assessment_id=assessment_id,
        rating=rating,
        original_score=original_score,
        suggested_score=suggested_score,
        reason=reason,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback


def get_confirmed_word_corrections(db: Session, original_word: str) -> list[WordFeedback]:
    return (
        db.query(WordFeedback)
        .filter(
            WordFeedback.original_word.ilike(original_word.strip()),
            WordFeedback.confirmed_word.isnot(None),
        )
        .order_by(WordFeedback.created_at.desc())
        .all()
    )
