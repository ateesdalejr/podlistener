# PodListener

PodListener is a podcast social listening MVP. It monitors RSS feeds, transcribes episodes with Whisper, detects keyword mentions, and enriches matches with an LLM.

This README explains how to run the full stack locally using Docker, aimed at beginners.

## What You Need

- Docker Desktop (or Docker Engine + Docker Compose)
- Git

## Quick Start (Docker)

1. Clone the repo and enter it.

```bash
git clone <your-repo-url>
cd podlistener
```

2. Create your environment file.

```bash
cp .env.example .env
```

3. (Optional but recommended) Update `.env`.

- `NGINX_BASIC_AUTH_USERNAME` / `NGINX_BASIC_AUTH_PASSWORD` for the web UI login
- `OLLAMA_MODEL` if you want a different local model
- `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` if you want to use OpenRouter instead of local Ollama
- `LLM_ENRICH_MIN_INTERVAL_SECONDS`, `LLM_ENRICH_MAX_RETRIES`, and retry delay settings to tune LLM enrichment pacing/backoff

4. Start everything.

```bash
make up
```

5. Pull the Ollama model (first run only).

```bash
make pull-model
```

6. Open the app.

- Web UI: `http://localhost/`
- Login uses the basic auth credentials from `.env`

That’s it. The app should now be running with all services.

## What’s Running

Docker Compose starts these services:

- `postgres` (database)
- `redis` (queue)
- `whisper` (transcription service)
- `ollama` (LLM for enrichment)
- `api` (FastAPI backend)
- `worker` (Celery background jobs)
- `flower` (Celery dashboard)
- `frontend` (Next.js UI)
- `nginx` (reverse proxy + basic auth)

## Useful Commands

```bash
# Stop everything
make down

# View logs
make logs          # all services
make logs-api      # API only
make logs-worker   # worker only

# Database migrations
make migrate

# Show running containers
make ps
```

## Common URLs & Ports

- App (via Nginx): `http://localhost/`
- API (internal): `http://localhost:8000/`
- Flower (Celery): `http://localhost:5555/`
- Whisper server: `http://localhost:9000/`
- Ollama: `http://localhost:11434/`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

## Troubleshooting

- **The app asks for a login**: It’s protected by Nginx basic auth. Update `NGINX_BASIC_AUTH_USERNAME` and `NGINX_BASIC_AUTH_PASSWORD` in `.env` and restart:

```bash
make down
make up
```

- **First run is slow**: Whisper and Ollama models are downloaded on first use. Give it time and check logs with `make logs`.

- **Ollama model not found**: Run `make pull-model` to download the configured model.

- **Container health issues**: Check `docker compose ps` and `make logs` for details.

## Notes

- All persistent data is stored in Docker volumes (`pgdata`, `ollama_models`, `audio_data`).
- The backend auto-runs database migrations on startup.

## Project Layout

- `backend/` FastAPI app + Celery worker
- `frontend/` Next.js UI
- `nginx/` Nginx config and basic auth
- `docker-compose.yml` Service definitions

If you want me to tailor this README to a specific deployment target (cloud VM, NAS, etc.), tell me which platform.
