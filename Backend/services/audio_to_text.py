import os
import tempfile
import whisper

_model = whisper.load_model("base")

def speech_to_text(audio_bytes: bytes, language: str = "en") -> str:
    if not audio_bytes:
        raise ValueError("Audio data is empty")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = _model.transcribe(tmp_path, language=language)
    finally:
        os.remove(tmp_path)

    return result["text"].strip()
