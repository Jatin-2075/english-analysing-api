def analyze_fluency(transcript: str, pause_count: int, pause_duration: float) -> dict:
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty")

    word_count = len(transcript.split())

    pauses_per_100_words = pause_count / max(word_count, 1) * 100

    score = max(0, min(100, 100 - pauses_per_100_words * 5 - pause_duration * 2))

    if score >= 80:
        level = "Fluent"
    elif score >= 60:
        level = "Moderately fluent"
    else:
        level = "Needs improvement"

    return {
        "fluency_score": round(score, 2),
        "fluency_level": level,
        "pauses_per_100_words": round(pauses_per_100_words, 2),
    }