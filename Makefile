up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

migrate:
	docker compose exec api alembic upgrade head

makemigrations:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

pull-model:
	docker compose exec ollama ollama pull llama3.2:3b

restart-worker:
	docker compose restart worker

ps:
	docker compose ps
