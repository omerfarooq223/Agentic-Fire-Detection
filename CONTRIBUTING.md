# Contributing

Thanks for improving FireWatch AI.

## Local Setup

1. Create a Python environment and install `requirements.txt`.
2. Install the frontend with `npm install --prefix frontend`.
3. Copy `.env.example` to `.env` and keep alerting in demo mode unless you are deliberately testing live integrations.
4. Keep model weights, databases, generated images, OAuth tokens, and credentials out of git.

## Checks Before Opening a Pull Request

```bash
npm run lint
npm run build
python3 -m compileall fire_backend.py fire_agent.py real_rag_system.py tests
```

The `tests/` scripts are manual integration demos. Run them only after starting the backend and using local demo data.

## Pull Request Notes

- Describe user-facing behavior changes.
- Mention new environment variables or setup steps.
- Include screenshots or short clips for dashboard UI changes.
- Document any alerting behavior changes in `docs/ALERTING.md`.
