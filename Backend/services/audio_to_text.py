import os
import shutil
import tempfile
import whisper

_model = whisper.load_model("base")


def _ensure_ffmpeg() -> None:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg is required to decode audio. Install FFmpeg and add it to PATH."
        )

    ffmpeg_directory = os.path.dirname(ffmpeg_path)
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    if ffmpeg_directory not in path_entries:
        os.environ["PATH"] = ffmpeg_directory + os.pathsep + os.environ.get("PATH", "")


def speech_to_text(audio_bytes: bytes, language: str = "en") -> str:
    if not audio_bytes:
        raise ValueError("Audio data is empty")

    _ensure_ffmpeg()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        try:
            result = _model.transcribe(tmp_path, language=language, fp16=False)
        except RuntimeError as exc:
            raise ValueError(f"Unable to decode the MP3 audio: {exc}") from exc
    finally:
        os.remove(tmp_path)

    return result["text"].strip()


def audio_duration_seconds(audio_bytes: bytes) -> float:
    if not audio_bytes:
        raise ValueError("Audio data is empty")

    _ensure_ffmpeg()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        try:
            audio = whisper.load_audio(tmp_path)
        except RuntimeError as exc:
            raise ValueError(f"Unable to decode the MP3 audio: {exc}") from exc
    finally:
        os.remove(tmp_path)

    return len(audio) / whisper.audio.SAMPLE_RATE
