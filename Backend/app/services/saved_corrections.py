import re

from sqlalchemy.orm import Session

from ..schemas.models import WordFeedback

def build_correction_map(rows) -> dict[str, str]:
    result = {}
    for original, confirmed in rows:
        key = original.strip().lower()
        confirmed = confirmed.strip()
        if key and confirmed and original.strip() != confirmed and key not in result:
            result[key] = confirmed
    return result


def replace_words(transcript: str, corrections: dict[str, str]) -> tuple[str, list[dict]]:
    applied: dict[str, dict] = {}

    def swap(match: re.Match) -> str:
        heard = match.group(0)
        suffix = ""
        fixed = corrections.get(heard.lower())
        if not fixed:
            base = re.sub(r"['’]s$", "", heard, flags=re.IGNORECASE)
            if base != heard:
                suffix = heard[len(base):]
                heard, fixed = base, corrections.get(base.lower())
        if not fixed or fixed == heard:
            return heard + suffix
        entry = applied.setdefault(heard.lower(), {"original": heard, "corrected": fixed, "count": 0})
        entry["count"] += 1
        return fixed + suffix

    corrected = re.sub(r"[^\W_]\w*(?:['’]\w+)?", swap, transcript)
    return corrected, list(applied.values())


def apply_saved_corrections(db: Session, transcript: str) -> tuple[str, list[dict]]:
    query = db.query(WordFeedback.original_word, WordFeedback.confirmed_word).filter(
        WordFeedback.confirmed_word.isnot(None),
        WordFeedback.accepted.isnot(False),
    )
    rows = query.order_by(WordFeedback.created_at.desc(), WordFeedback.id.desc()).all()
    corrections = build_correction_map(rows)
    if not corrections:
        return transcript, []
    return replace_words(transcript, corrections)
