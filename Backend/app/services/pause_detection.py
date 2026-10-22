import io

import librosa
import numpy as np


def analyze_pauses(
    audio_bytes: bytes,
    sample_rate: int = 16000,
    min_pause_duration: float = 0.25,
    frame_length: int = 1024,
    hop_length: int = 256,
) -> dict:
    """Count silent gaps between speech.

    The silence threshold adapts to each recording (its own noise floor and
    speech level), so a noisy room or a mic with background hiss no longer hides
    pauses. Silence before the first word and after the last word is ignored,
    because that is only the recording start/stop, not a pause in speech.
    """
    if not audio_bytes:
        raise ValueError("Audio data is empty")

    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=sample_rate, mono=True)

    if len(audio) == 0:
        raise ValueError("Audio contains no samples")

    empty = {
        "pause_count": 0,
        "average_pause_duration_seconds": 0.0,
        "pause_durations_seconds": [],
    }

    rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
    db = librosa.amplitude_to_db(rms, ref=1.0, amin=1e-8)

    if len(db) < 3:
        return empty

    noise_floor = np.percentile(db, 10)
    speech_level = np.percentile(db, 90)
    dynamic_range = speech_level - noise_floor


    if dynamic_range < 6:
        return empty


    threshold = noise_floor + min(max(0.25 * dynamic_range, 4.0), 12.0)
    silent = db < threshold

    voiced = np.flatnonzero(~silent)
    if len(voiced) == 0:
        return empty

    first, last = voiced[0], voiced[-1]  # ignore leading and trailing silence
    frame_time = hop_length / sr
    pauses = []
    run = 0

    for is_silent in silent[first : last + 1]:
        if is_silent:
            run += 1
            continue
        if run:
            gap = run * frame_time
            if gap >= min_pause_duration:
                pauses.append(round(gap, 3))
            run = 0

    count = len(pauses)

    return {
        "pause_count": count,
        "average_pause_duration_seconds": round(sum(pauses) / count if count else 0.0, 3),
        "pause_durations_seconds": pauses,
    }
