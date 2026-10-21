import shutil
import subprocess
import tempfile
from pathlib import Path


def webm_to_mp3(audio_bytes: bytes) -> bytes:
    if not audio_bytes:
        raise ValueError("Audio data is empty")

    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "FFmpeg is required to convert audio. Install FFmpeg and add it to PATH."
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "input.webm"
        output_path = Path(temp_dir) / "output.mp3"

        input_path.write_bytes(audio_bytes)

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i", str(input_path),
                    "-vn",
                    "-codec:a", "libmp3lame",
                    "-b:a", "128k",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.decode(errors="replace").strip()
            raise ValueError(f"Unable to convert audio to MP3: {detail}") from exc

        return output_path.read_bytes()
