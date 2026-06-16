# FireWatch AI Frontend

React + Vite dashboard for the FireWatch AI backend.

## Local Development

```bash
npm install
npm run dev
```

By default, the frontend talks to `http://localhost:8000`.

To point it at a deployed backend, set:

```env
VITE_BACKEND_URL=https://your-backend.example.com
```

Only use `VITE_` variables for values that are safe to expose in browser code.

## Production Build

```bash
npm run lint
npm run build
```

The production files are written to `dist/`.

## Vercel Settings

When importing this repository into Vercel, use:

- Framework preset: `Vite`
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_BACKEND_URL=https://your-render-backend.onrender.com`

After the backend URL changes, redeploy the frontend so Vite bakes the new value into the static build.
