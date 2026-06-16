# FireWatch AI: Fire and Smoke Detection Dashboard

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-00A6ED?style=for-the-badge)](https://ultralytics.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](./LICENSE)

FireWatch AI is a fire and smoke monitoring system with a FastAPI backend, YOLO-based video analysis, a React tactical dashboard, optional RAG-assisted safety guidance, and demo-safe alert workflows.

![System Demo](./demo.gif)

## Features

- Video upload and frame sampling for fire/smoke analysis.
- React + Vite dashboard with animated overlays, timeline metrics, response controls, and a floating safety assistant.
- FastAPI backend with SQLite-backed zones, detections, incidents, and safety procedures.
- Optional YOLO model weights for real detection, with a heuristic fallback when no local model is available.
- Optional Groq-powered RAG answer synthesis.
- Demo-safe Gmail alert modes with confirmation frames and cooldown guards.

## Repository Layout

```text
.
├── fire_backend.py            # FastAPI API, detection pipeline, alert orchestration
├── fire_agent.py              # Agent tools, Gmail helpers, emergency response logic
├── real_rag_system.py         # FAISS/sentence-transformers RAG implementation
├── frontend/                  # React + Vite dashboard
├── docs/ALERTING.md           # Alert modes and safety guardrails
├── tests/                     # Manual integration/demo scripts
├── .env.example               # Safe environment template
└── requirements.txt           # Python dependencies
```

Local runtime files such as `.env`, `credentials.json`, `token.json`, `fire_system.db`, `best.pt`, `models/*.pt`, and generated detection images are intentionally ignored by git.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Optional: a YOLO model weight file such as `best.pt`
- Optional: a Groq API key for generated RAG responses
- Optional: Gmail API OAuth credentials for live email alerting

## Setup

1. Create and activate a Python environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Install frontend dependencies.

```bash
npm install --prefix frontend
```

3. Create local environment settings.

```bash
cp .env.example .env
```

Keep the default safe alert settings for demos:

```env
ALERT_MODE=demo
AUTO_ALERTS_ENABLED=false
ALERT_CONFIRMATION_FRAMES=3
ALERT_COOLDOWN_SECONDS=300
```

4. Add a local model file if you have one.

```env
FIRE_DETECT_MODEL=./best.pt
```

Large model files should stay outside git. Use Git LFS, a release asset, or a model registry if you need to share them.

## Run Locally

Start the backend:

```bash
uvicorn fire_backend:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend in another terminal:

```bash
npm run dev --prefix frontend
```

Then open the Vite URL, usually `http://localhost:5173`.

Useful backend URLs:

- API health: `http://localhost:8000/api/health`
- API docs: `http://localhost:8000/docs`

## Deployment

Recommended split:

- Frontend: Vercel static Vite deployment.
- Backend: Render Python web service.

Vercel frontend settings:

- Root directory: `frontend`
- Framework preset: `Vite`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_BACKEND_URL=https://your-backend.onrender.com`

Render backend settings:

- Language: `Python 3`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn fire_backend:app --host 0.0.0.0 --port $PORT`

Backend environment variables:

```env
ALERT_MODE=demo
AUTO_ALERTS_ENABLED=false
CORS_ORIGINS=https://your-frontend.vercel.app
GROQ_API_KEY=your_key_here
```

For live Gmail alerts, add the Gmail variables from `.env.example` and keep OAuth files out of git.

Production notes:

- SQLite and generated detection images are local runtime files. Use persistent storage or a hosted database for anything beyond a demo.
- Model weights are intentionally not committed. Add them through persistent storage, a release artifact, or another model delivery flow.
- Vite exposes `VITE_*` values in browser code, so do not put secrets in frontend environment variables.

## Alerts

The default configuration does not contact real people. For live alerts, configure `.env` intentionally and read [docs/ALERTING.md](./docs/ALERTING.md).

Do not configure this project to contact real emergency services.

## Checks

```bash
npm run lint
npm run build
python3 -m compileall fire_backend.py fire_agent.py real_rag_system.py tests
```

The scripts in `tests/` are manual integration/demo scripts. They expect the backend to be running and may create local database/image state, so they are not run automatically in CI.

## GitHub Hygiene

- Commit source, docs, lockfiles, and small static assets.
- Do not commit `.env`, OAuth tokens, credentials, local databases, generated captures, or model weights.
- Rotate any credential that was ever committed or shared publicly.
- Keep live alerting disabled unless you are deliberately testing with verified recipients.

## Credits

Designed and developed by Muhammad Umar Farooq.

[Portfolio](https://omerfarooq223.github.io)
