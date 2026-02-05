# Vihaan Web (React)

This folder contains a React UI that talks to the Python API in `Streamlit/api_server.py`.

## Run (dev)

Backend (from `Streamlit/`):

```bash
uvicorn api_server:app --reload --port 8000
```

Frontend (from `web/`):

```bash
npm install
npm run dev
```

Set `VITE_API_BASE` (optional) via `web/.env` (see `web/.env.example`).

