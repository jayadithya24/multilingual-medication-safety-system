# Static demo deployment

This branch deploys only the React/Vite frontend. It uses bundled English,
Kannada, and Tulu CSVs plus predefined example records. It does not require
FastAPI, Neo4j, MongoDB, Render, credentials, or Vercel environment variables.
The dashboards are public and read-only; sample patient details are synthetic.
OCR, voice transcription, text-to-speech, notifications, and saved changes are
not provided by this static demo.

## Deploy to Vercel

1. Import the `demo/static-frontend` branch into Vercel.
2. Set **Root Directory** to `frontend`.
3. Use the Vite defaults: install with `npm install`, build with `npm run build`,
   and publish `dist`.
4. Leave environment variables empty and deploy.

`frontend/vercel.json` sends client-side routes to `index.html`; data requests
are served from `frontend/public/demo-data/` and handled locally in the browser.
No API proxy or backend service is configured on this branch.

## Local preview

From `frontend/`, run `npm install`, then `npm run dev`. The same bundled data
and read-only demo behavior are used locally and on Vercel.
