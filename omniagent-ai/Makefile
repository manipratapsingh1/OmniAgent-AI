.PHONY: up down logs api web test fmt seed migrate models

up:
	docker compose -f docker/docker-compose.yml --env-file .env up -d --build

down:
	docker compose -f docker/docker-compose.yml down -v

logs:
	docker compose -f docker/docker-compose.yml logs -f --tail=200

api:
	cd backend && python run_server.py

api-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd frontend && npm run dev

test:
	cd backend && pytest -q

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.db.init_db

models:
	bash scripts/pull_models.sh