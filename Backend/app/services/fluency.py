IDEAL_WPM_LOW = 110
IDEAL_WPM_HIGH = 160


def analyze_fluency(
    transcript: str,
    pause_count: int,
    pause_duration: float,
    audio_duration: float | None = None,
    words_per_minute: float | None = None,
    filler_rate_percent: float | None = None,
) -> dict:
    """Fluency estimate from pauses, speaking pace and filler words.

    pause_duration is the TOTAL seconds of pauses. The last three arguments are
    optional, so the old 3-argument call still works (it then scores on pauses only).
    """
    if not transcript or not transcript.strip():
        raise ValueError("Transcript is empty")

    word_count = len(transcript.split())
    pauses_per_100_words = pause_count / max(word_count, 1) * 100

    pause_frequency_penalty = min(40.0, pauses_per_100_words * 4)

    if audio_duration and audio_duration > 0:
        pause_ratio = min(1.0, pause_duration / audio_duration)
        pause_time_penalty = min(30.0, pause_ratio * 100)
    else:
        pause_time_penalty = min(30.0, pause_duration * 2)

    pace_penalty = 0.0
    if words_per_minute is not None and words_per_minute > 0:
        if words_per_minute < IDEAL_WPM_LOW:
            pace_penalty = min(25.0, (IDEAL_WPM_LOW - words_per_minute) * 0.3)
        elif words_per_minute > IDEAL_WPM_HIGH:
            pace_penalty = min(15.0, (words_per_minute - IDEAL_WPM_HIGH) * 0.2)

    filler_penalty = min(15.0, (filler_rate_percent or 0.0) * 1.5)

    score = 100 - pause_frequency_penalty - pause_time_penalty - pace_penalty - filler_penalty
    score = max(0.0, min(100.0, score))

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
        "penalties": {
            "pause_frequency": round(pause_frequency_penalty, 2),
            "pause_time": round(pause_time_penalty, 2),
            "pace": round(pace_penalty, 2),
            "fillers": round(filler_penalty, 2),
        },
    }
