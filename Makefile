# AI Teaching Platform — удобные команды
# Использование: make <команда>

.PHONY: help dev prod stop logs test migrate build clean

# По умолчанию показать список команд
help:
	@echo ""
	@echo "  AI Teaching Platform"
	@echo ""
	@echo "  make dev        — запустить в режиме разработки"
	@echo "  make prod       — запустить в production режиме"
	@echo "  make stop       — остановить все контейнеры"
	@echo "  make logs       — показать логи (dev)"
	@echo "  make logs-prod  — показать логи (prod)"
	@echo "  make build      — пересобрать образы (prod)"
	@echo "  make migrate    — запустить миграции БД"
	@echo "  make test       — запустить тесты backend"
	@echo "  make health     — проверить состояние сервисов"
	@echo "  make clean      — удалить контейнеры и volumes"
	@echo ""

# --- Development ---

dev:
	docker compose -f docker-compose.dev.yml up

dev-bg:
	docker compose -f docker-compose.dev.yml up -d

stop:
	docker compose -f docker-compose.dev.yml down
	docker compose -f docker-compose.prod.yml down

# --- Production ---

prod:
	docker compose -f docker-compose.prod.yml up

prod-bg:
	docker compose -f docker-compose.prod.yml up -d

build:
	docker compose -f docker-compose.prod.yml build --no-cache

# --- Logs ---

logs:
	docker compose -f docker-compose.dev.yml logs -f

logs-prod:
	docker compose -f docker-compose.prod.yml logs -f

logs-backend:
	docker compose -f docker-compose.dev.yml logs -f backend

logs-frontend:
	docker compose -f docker-compose.dev.yml logs -f frontend

# --- Database ---

migrate:
	docker compose -f docker-compose.dev.yml exec backend alembic upgrade head

migrate-prod:
	docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# --- Tests ---

test:
	cd backend && python -m pytest tests/ -v

test-cov:
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

# --- Health check ---

health:
	@curl -s http://localhost:8000/api/v1/health | python -m json.tool || echo "Backend недоступен"

health-prod:
	@curl -s http://localhost/api/v1/health | python -m json.tool || echo "Production недоступен"

# --- Cleanup ---

clean:
	docker compose -f docker-compose.dev.yml down -v
	docker compose -f docker-compose.prod.yml down -v
