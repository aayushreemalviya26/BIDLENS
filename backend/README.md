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

Copy `.env.example` values into your environment as needed. SQLite is the development default. Set `DATABASE_URL` to a PostgreSQL URL for Render or Railway. Uploaded PDFs use `StorageService`; the supplied Render Blueprint mounts a persistent disk for uploads and the Hugging Face model cache.

The AI stages require the Python packages in the repository root, the `all-MiniLM-L6-v2` embedding model, and an Ollama-compatible chat model. Local development defaults to `qwen2.5:3b` at `http://localhost:11434`. Production can set `OLLAMA_BASE_URL=https://ollama.com`, provide `OLLAMA_API_KEY` as a secret, and select a hosted model with `OLLAMA_MODEL`. The supplied `render.yaml` uses `qwen3-coder:480b-cloud` because `qwen2.5:3b` is not an Ollama Cloud model.

Frontend configuration:

```text
VITE_API_URL=http://localhost:8000
```

Deploy `frontend/` to Vercel and the repository-root `render.yaml` Blueprint to Render. In Vercel, set `VITE_API_URL` to the public Render backend URL. In Render, enter `OLLAMA_API_KEY` when the Blueprint prompts for it. Keep secrets in the hosting dashboards; never commit them.
