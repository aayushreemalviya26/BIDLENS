# BIDLENS backend

The FastAPI backend wraps the existing tender and bidder AI scripts; it does not duplicate their extraction, classification, retrieval, or evidence logic. Each adapter runs a private copy of the scripts in a temporary directory because the existing pipelines use fixed relative filenames.

## Local run

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Copy `.env.example` values into your environment as needed. SQLite is the development default. Set `DATABASE_URL` to a PostgreSQL URL for Render or Railway. Uploaded PDFs use `StorageService` and local disk by default; production should replace it with durable object storage.

The AI stages currently require the Python packages in the repository root, the `all-MiniLM-L6-v2` model, and an Ollama service running `qwen2.5:3b`. Production therefore needs either a reachable hosted Ollama instance (`OLLAMA_BASE_URL`) or a provider replacement behind the adapters. The web/API and deterministic evaluation layers can run without Ollama, but extraction and bidder processing cannot.

Frontend configuration:

```text
VITE_API_URL=http://localhost:8000
```

Deploy `frontend/` to Vercel and `backend/` to Render/Railway. Set `CORS_ORIGINS` to the deployed frontend origin.
