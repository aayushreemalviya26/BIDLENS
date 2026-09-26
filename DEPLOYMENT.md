# Zero-cost judge deployment

Frontend: Vercel Hobby. Backend: Render Free. Database: Render Free PostgreSQL.
Online AI: Groq `openai/gpt-oss-120b`, with JSON output and pipeline validation.
Offline AI: local-only Ollama Qwen + MiniLM, unchanged.

Build: `pip install -r backend/requirements-cloud.txt`
Start: `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT`
No Torch, MiniLM, Qwen weights or Ollama is installed on Render. Hosted retrieval
is explicitly labelled lexical hashing + existing category reranking.

Enter `GROQ_API_KEY` and `PROTOTYPE_ADMIN_PASSWORD` only in Render Environment.
The Blueprint wires PostgreSQL DATABASE_URL. Set CORS_ORIGINS to the exact
Vercel production domain. Never commit secrets or put them in VITE_ variables.
Use a Vercel same-origin /api rewrite to Render so HttpOnly SameSite cookies
work with third-party cookies blocked. Leave VITE_API_BASE_URL empty.

## Preprocessed Demo

The fixture excludes sessions, secrets and local paths. The tender is public
procurement material and may include public institutional/contact information.
Every bidder PDF is fictional, marked synthetic, with invented identifiers.
Authenticated document-ID endpoints serve only the associated original files.

Bharat evidence comes from the saved local Ollama acceptance run. Orange and
SecureByte evidence is curated from literal PDF fields, not fresh AI output.
Seeding recomputes all findings with the unchanged compliance engine and mock
registries; its origin is recorded in audit. SEED_JUDGE_DEMO=true imports once,
without overwriting existing state. Officer decisions remain separate from
machine status. Hosted reset is disabled. Login is shared prototype access,
not a production or multi-tenant identity system.

## Limitations

- Render sleeps after 15 minutes idle; waking can take about one minute.
- Startup retries are bounded; long AI processing uses a polled job record.
- Fresh uploads disappear on restart. Records may remain, but files require
  re-upload. Packaged demo PDFs survive rebuilds.
- Free PostgreSQL expires after 30 days. It is not permanent archival storage.
- Groq free quotas may reject requests. No fake output or silent fallback.
- Saved demo browsing does not require a working AI key.
- One AI job at a time; server restarts mark interrupted jobs failed.
- Scanned PDFs requiring Tesseract may not work on the native free host.

Local startup: configure ignored backend/.env, install backend/requirements.txt,
start Ollama with qwen2.5:3b and cache MiniLM. Run
`backend/.venv/Scripts/python.exe scripts/start_local_preview.py` and `npm run dev`
in frontend. Tests: `backend/.venv/Scripts/python.exe -m pytest backend/tests -q`.
