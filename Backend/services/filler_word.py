import re


FILLER_WORDS = [
    "um", "uh", "erm", "hmm", "mm",
    "you know", "i mean", "basically",
    "actually", "literally", "like", "well"
]


def analyze_fillers(transcript: str) -> dict:
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty")

    text = transcript.lower()
    filler_counts = {}

    for filler in FILLER_WORDS:
        pattern = rf"(?<!\w){re.escape(filler)}(?!\w)"
        count = len(re.findall(pattern, text))
        if count:
            filler_counts[filler] = count

    total_fillers = sum(filler_counts.values())
    word_count = len(re.findall(r"\b[\w']+\b", text))

    return {
        "filler_count": total_fillers,
        "filler_words": filler_counts,
        "filler_rate_percent": round(
            total_fillers / max(word_count, 1) * 100, 2
        ),
    }