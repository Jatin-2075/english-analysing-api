# English Assessment API

An audio-based English speaking assessment service built with Python and FastAPI.
The API accepts an English audio recording, transcribes it, and returns a
structured assessment of speaking pace, pauses, grammar, filler words, and
fluency. Browser recordings and common formats including WebM, MP3, WAV, M4A,
MP4, OGG, and FLAC are supported.

## Features

- Audio upload through a FastAPI endpoint.
- Speech-to-text transcription using OpenAI Whisper (`base` model).
- Words-per-minute calculation based on the transcript and audio duration.
- Silence/pause detection using `librosa`.
- Grammar checking using LanguageTool (`en-US`).
- Filler-word detection for common hesitations such as `um`, `uh`, and
  `you know`.
- A combined fluency score based on pause frequency and pause duration.
- Automatic interactive API documentation through Swagger UI and ReDoc.
  
## Project status

This repository currently contains the backend API only. There is no web or
mobile frontend included. A client can call the API using `curl`, Postman, or
any HTTP client capable of sending a multipart file upload.

## Requirements

### Software

- Python 3.10 or newer (the project has been developed with Python 3.12).
- `pip`.
- FFmpeg available on the system `PATH`. Whisper and audio libraries use it to
  decode audio.
- Java Runtime Environment (JRE) 8 or newer for the local LanguageTool server
  used by `language-tool-python`.

### Hardware

The Whisper `base` model runs on CPU, but transcription is faster with a
compatible GPU. The first transcription starts by loading and, if necessary,
downloading the Whisper model, so an internet connection may be required on
first run.

## Directory structure

```text
english_asssement/
├── Backend/
│   ├── main.py
│   └── services/
│       ├── audio_to_text.py
│       ├── filler_word.py
│       ├── fluency.py
│       ├── grammer_analysis.py
│       ├── pause_detection.py
│       └── word_per_min.py
├── requirements.txt
├── .gitignore
└── readme.md
```

### Service responsibilities

| Module | Responsibility |
| --- | --- |
| `Backend/main.py` | Creates the FastAPI application and exposes the HTTP endpoints. |
| `audio_to_text.py` | Saves the uploaded bytes temporarily and transcribes them with Whisper. |
| `word_per_min.py` | Calculates word count, duration, and words per minute. |
| `pause_detection.py` | Finds silent gaps in the audio and calculates pause statistics. |
| `grammer_analysis.py` | Finds English grammar issues and provides suggestions. |
| `filler_word.py` | Counts configured filler words and calculates their rate. |
| `fluency.py` | Converts pause frequency and duration into a fluency score and level. |

## Installation

Open PowerShell in the project directory:

```powershell
cd C:\Jatin\codes\Production_level_project\only_idea\english_asssement
```

Create and activate a virtual environment:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either allow scripts for the current user or
activate the environment with the batch script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install FFmpeg separately and confirm both required tools are available:

```powershell
ffmpeg -version
java -version
```

On the first application run, Whisper may download its `base` model. Keep the
machine connected to the internet until that download completes.

## Running the API

From the project root, with the virtual environment activated:

```powershell
python -m uvicorn Backend.app.main:app --reload
```

The server is then available at:

- API base URL: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

For a production-style local run without the file watcher:

```powershell
python -m uvicorn Backend.app.main:app --host 0.0.0.0 --port 8000
```

## API reference

### `GET /`

Health-style endpoint used to confirm that the application is running.

Example:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

Response:

```json
{
  "message": "running"
}
```

### `POST /transcribe`

Uploads an audio file and returns the transcript plus the complete assessment.

#### Request

Send the file as a multipart form field named `file`. The filename must end in
`.mp3`, `.wav`, `.m4a`, `.mp4`, `.webm`, `.ogg`, or `.flac` (the extension
check is case-insensitive).

PowerShell:

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/transcribe `
  -Method Post `
  -Form @{ file = Get-Item .\sample.mp3 }
```

`curl`:

```bash
curl -X POST "http://127.0.0.1:8000/transcribe" \
  -F "file=@sample.mp3"
```

#### Successful response

```json
{
  "transcript": "This is an example of spoken English.",
  "analysis": {
    "pace": {
      "word_count": 8,
      "audio_duration_seconds": 4.2,
      "words_per_minute": 114.29
    },
    "pauses": {
      "pause_count": 1,
      "average_pause_duration_seconds": 0.6,
      "pause_durations_seconds": [0.6]
    },
    "grammar": {
      "word_count": 8,
      "grammar_error_count": 0,
      "grammar_score": 100.0,
      "errors": []
    },
    "filler_words": {
      "filler_count": 0,
      "filler_words": {},
      "filler_rate_percent": 0.0
    },
    "fluency": {
      "fluency_score": 95.0,
      "fluency_level": "Fluent",
      "pauses_per_100_words": 12.5
    }
  }
}
```

The exact values depend on the uploaded audio, Whisper transcription, and
LanguageTool results.

#### Error responses

| Status | Cause |
| ---: | --- |
| `400` | The upload format is unsupported or the file is empty. |
| `422` | The audio contains no recognizable speech. |
| `500` | An unexpected processing failure occurred, such as a missing runtime dependency or an unreadable audio file. |

Errors are returned using FastAPI's standard shape:

```json
{
  "detail": "upload a mp3"
}
```

## How the assessment is calculated

### Pace

`words_per_minute = word_count / audio_duration_seconds * 60`

The word count is calculated from the Whisper transcript using whitespace
separation. Audio is decoded through FFmpeg at 16 kHz for consistent duration
and pause calculations across supported formats.

### Pauses

The audio is loaded as mono audio at 16 kHz. `librosa.effects.split` identifies
non-silent intervals using `top_db=35`, a frame length of `2048`, and a hop
length of `512`. Gaps of at least `0.25` seconds are counted as pauses,
including a qualifying trailing pause.

The response contains:

- `pause_count`: number of detected pauses.
- `average_pause_duration_seconds`: average duration of detected pauses.
- `pause_durations_seconds`: duration of every detected pause.

These values are signal-processing estimates and can change with background
noise, microphone quality, and recording volume.

### Grammar

LanguageTool checks the transcript using the `en-US` language. Each reported
issue includes the original mistake, a message, up to five replacement
suggestions, and its category.

The current score is:

`max(0, 100 - grammar_error_count / word_count * 100)`

### Filler words

The service currently checks these case-insensitive terms:

```text
um, uh, erm, hmm, mm, you know, i mean, basically,
actually, literally, like, well
```

Matching is bounded by word characters, so a filler is not counted when it is
only part of another word. The response includes the total count, per-term
counts, and the percentage of transcript words that are fillers.

### Fluency

The fluency score starts at `100` and is reduced by:

- `5` points for every pause per 100 words.
- `2` points for every second of total pause duration.

The result is clamped to the range `0` to `100`:

```text
score = max(0, min(100, 100 - pauses_per_100_words * 5 - total_pause_duration * 2))
```

Levels are assigned as follows:

| Score | Level |
| ---: | --- |
| `80–100` | `Fluent` |
| `60–79.99` | `Moderately fluent` |
| Below `60` | `Needs improvement` |

## Configuration and customization

There is currently no `.env`-based configuration. The main tuning values are
defined in the service modules:

- Whisper model and language: `Backend/services/audio_to_text.py`.
- Pause threshold and signal-processing settings:
  `Backend/services/pause_detection.py`.
- Filler vocabulary: `Backend/services/filler_word.py`.
- Grammar language: `Backend/services/grammer_analysis.py`.
- Fluency scoring weights and levels: `Backend/services/fluency.py`.

To use another Whisper model, change `whisper.load_model("base")` to a
supported model such as `tiny`, `small`, or `medium`. Larger models generally
improve accuracy but require more download size and memory.

## Development

Run the application with automatic reload while developing:

```powershell
python -m uvicorn Backend.app.main:app --reload
```

The service modules expose small Python functions, so they can also be tested
individually with unit tests for transcripts, pause thresholds, filler-word
boundaries, and scoring edge cases. When adding tests, keep test audio outside
the repository or use generated fixtures because audio files are ignored by
`.gitignore`.

Before opening a change, verify:

```powershell
python -m compileall Backend
python -m pip check
```

## Troubleshooting

### `ffmpeg` is not recognized

Install FFmpeg and add its `bin` directory to `PATH`. Restart PowerShell and
confirm with `ffmpeg -version`.

### LanguageTool or Java errors

Install a JRE, make sure `java -version` succeeds, and restart the API. The
first grammar request may take longer while the local LanguageTool process
starts.

### Whisper model download or memory problems

Confirm internet access for the initial model download. If the machine has
limited memory, use the `tiny` model in `audio_to_text.py`; if transcription
quality is insufficient, use a larger model on a machine with adequate
resources.

### An audio file cannot be decoded

Confirm that the file is valid and can be opened by FFmpeg. The endpoint
supports common browser and uploaded audio formats, but still requires FFmpeg
to be installed and available on `PATH`.

### Slow requests

Transcription, pause analysis, and grammar checking all run synchronously
inside one request. Long recordings and CPU-only machines will take longer.
For production workloads, consider request-size and duration limits, a job
queue, background workers, and persistent model initialization.

## Security and production considerations

This project is a development-oriented API and should be hardened before
internet exposure:

- Add authentication and authorization.
- Restrict upload size and maximum recording duration.
- Validate content by inspecting the file rather than trusting only its
  filename extension.
- Avoid returning raw internal exception messages to external clients.
- Add rate limiting and request timeouts.
- Store temporary uploads safely and remove them after processing.
- Run behind HTTPS and a production ASGI deployment.
- Pin dependency versions and scan them regularly.

## License

No license file is currently included. Add a license before distributing this
project or accepting external contributions.