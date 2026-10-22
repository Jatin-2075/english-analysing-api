def word_per_min(transcript: str, audio_duration_seconds: float) -> dict:
    if audio_duration_seconds <= 0:
        raise ValueError("Audio duration must be greater than zero")

    word_count = len(transcript.split())
    wpm = (word_count / audio_duration_seconds) * 60

    return {
        "word_count": word_count,
        "audio_duration_seconds": round(audio_duration_seconds, 2),
        "words_per_minute": round(wpm, 2),
    }