# English Assessment Frontend

React + TypeScript + Vite UI for the FastAPI backend.

Run `npm install`, copy `.env.example` to `.env`, then `npm run dev`.

Audio uses `POST /transcribe` multipart field `file`. Text uses `POST /analyze-text` JSON `{ "text": "..." }`.

The backend accepts browser recordings and common audio uploads including WebM,
MP3, WAV, M4A, MP4, OGG, and FLAC. FastAPI CORS is configured for the local
Vite origins (`http://localhost:5173` and `http://127.0.0.1:5173`).
