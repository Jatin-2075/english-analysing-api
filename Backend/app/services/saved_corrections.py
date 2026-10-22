import re
from collections import Counter

from sqlalchemy.orm import Session

from ..schemas.models import WordFeedback

NAMES_ONLY = True
MIN_CONFIRMATIONS = 1


def build_correction_map(rows) -> dict[str, str]:
    """rows: iterable of (original_word, confirmed_word), newest first.
    Returns {original_lowercase: most_confirmed_spelling}; ties go to the newest."""
    votes: dict[str, Counter] = {}
    newest: dict[tuple[str, str], int] = {}
    for position, (original, confirmed) in enumerate(rows):
        key = original.strip().lower()
        confirmed = confirmed.strip()
        if not key or not confirmed or original.strip() == confirmed:
            continue
        votes.setdefault(key, Counter())[confirmed] += 1
        newest.setdefault((key, confirmed), position)

    result = {}
    for key, counter in votes.items():
        best = max(counter.items(), key=lambda item: (item[1], -newest[(key, item[0])]))
        if best[1] >= MIN_CONFIRMATIONS:
            result[key] = best[0]
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
    """Replace words the transcriber got wrong with the spelling users confirmed before."""
    query = db.query(WordFeedback.original_word, WordFeedback.confirmed_word).filter(
        WordFeedback.confirmed_word.isnot(None),
        WordFeedback.accepted.isnot(False),
    )
    if NAMES_ONLY:
        query = query.filter(WordFeedback.is_name.is_(True))

    rows = query.order_by(WordFeedback.created_at.desc()).all()
    corrections = build_correction_map(rows)
    if not corrections:
        return transcript, []
    return replace_words(transcript, corrections)
