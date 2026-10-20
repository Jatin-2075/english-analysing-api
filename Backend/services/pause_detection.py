import io
import librosa


def analyze_pauses(audio_bytes: bytes, sample_rate: int = 16000, min_pause_duration: float = 0.25) -> dict:
    if not audio_bytes:
        raise ValueError("Audio data is empty")

    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=sample_rate, mono=True)

    if len(audio) == 0:
        raise ValueError("Audio contains no samples")

    intervals = librosa.effects.split(audio, top_db=35, frame_length=2048, hop_length=512)
    total_duration = len(audio) / sr
    pauses = []
    previous_end = 0.0

    for start_sample, end_sample in intervals:
        start_time, end_time = start_sample / sr, end_sample / sr
        gap = start_time - previous_end

        if gap >= min_pause_duration:
            pauses.append(round(gap, 3))

        previous_end = end_time

    trailing_pause = total_duration - previous_end

    if trailing_pause >= min_pause_duration:
        pauses.append(round(trailing_pause, 3))

    count = len(pauses)

    return {
        "pause_count": count,
        "average_pause_duration_seconds": round(sum(pauses) / count if count else 0.0, 3),
        "pause_durations_seconds": pauses,
    }