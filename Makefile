.PHONY: help up down build restart logs shell db-shell redis-shell \
        celery-shell superuser migrate test clean fresh

help:
	@echo "🐳 Internet Banking Docker Commands"
	@echo ""
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make build       - Rebuild all images"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View all logs"
	@echo "  make logs-be     - View backend logs"
	@echo "  make logs-ai     - View AI service logs"
	@echo "  make logs-fe     - View frontend logs"
	@echo "  make shell       - Django shell"
	@echo "  make db-shell    - PostgreSQL shell"
	@echo "  make redis-shell - Redis CLI"
	@echo "  make migrate     - Run migrations"
	@echo "  make superuser   - Create superuser"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Stop + remove volumes"
	@echo "  make fresh       - Full rebuild from scratch"

up:
	docker-compose up -d
	@echo "✅ All services started"
	@echo "   Frontend: http://localhost:3000"
	@echo "   Backend:  http://localhost:8000"
	@echo "   AI Docs:  http://localhost:9000/docs"
	@echo "   Swagger:  http://localhost:8000/api/docs/"

down:
	docker-compose down

build:
	docker-compose build --no-cache

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-be:
	docker-compose logs -f backend

logs-ai:
	docker-compose logs -f ai-service

logs-fe:
	docker-compose logs -f frontend

shell:
	docker-compose exec backend python manage.py shell

db-shell:
	docker-compose exec db psql -U bank_admin -d internet_banking

redis-shell:
	docker-compose exec redis redis-cli

celery-shell:
	docker-compose exec celery_worker python manage.py shell

migrate:
	docker-compose exec backend python manage.py makemigrations
	docker-compose exec backend python manage.py migrate

superuser:
	docker-compose exec backend python manage.py createsuperuser

test:
	docker-compose exec backend python manage.py test

clean:
	docker-compose down -v

fresh:
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d