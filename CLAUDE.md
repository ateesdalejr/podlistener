# PodListener

Podcast social listening MVP. Monitors RSS feeds, transcribes episodes with Whisper, detects keyword mentions, enriches matches with Ollama (sentiment, buying signals, pain points).

## Stack
- **Backend**: Python/FastAPI, SQLAlchemy (async), Celery + Redis, PostgreSQL
- **Frontend**: Next.js 15, Tailwind CSS 4, TypeScript
- **ML**: faster-whisper-server (transcription), Ollama (LLM enrichment)

## Development Commands

```bash
# Start everything
make up

# Pull the Ollama model (required first time)
make pull-model

# View logs
make logs          # all services
make logs-api      # API only
make logs-worker   # worker only

# Database
make migrate               # run migrations
make makemigrations msg="description"  # create new migration

# Restart worker after code changes
make restart-worker

# Run backend tests
docker compose exec api pytest -v

# Or locally (needs venv):
cd backend && pip install -r requirements.txt && pytest -v
```

## Architecture

6 Docker services: postgres, redis, whisper, ollama, api, worker, frontend

Pipeline: poll RSS → download audio → transcribe (Whisper) → detect keywords → enrich (Ollama) → store mentions

## Project Structure
- `backend/app/api/v1/` - REST endpoints (feeds, episodes, keywords, mentions, dashboard)
- `backend/app/models/` - SQLAlchemy ORM models
- `backend/app/services/` - Business logic (feed parsing, transcription, detection, enrichment)
- `backend/app/worker/tasks/` - Celery tasks (poll.py, process.py)
- `backend/tests/` - pytest tests
- `frontend/src/app/` - Next.js pages (dashboard, feeds, keywords, mentions)
- `frontend/src/lib/api.ts` - API client

## Key Env Vars
See `.env.example` for all config. Main ones:
- `DATABASE_URL` / `DATABASE_URL_SYNC` - PostgreSQL connection
- `REDIS_URL` - Celery broker
- `WHISPER_API_URL` - faster-whisper-server endpoint
- `OLLAMA_BASE_URL` / `OLLAMA_MODEL` - LLM for enrichment
- `NGINX_BASIC_AUTH_USERNAME` / `NGINX_BASIC_AUTH_PASSWORD` - credentials for HTTP basic auth at reverse proxy
