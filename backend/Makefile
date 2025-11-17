# ChefGPT Backend Makefile
# Simplifies common development and deployment tasks

.PHONY: help dev prod staging build up down logs migrate seed clean test

# Default target
help:
	@echo "ChefGPT Backend - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment"
	@echo "  make build        - Build development images"
	@echo "  make logs         - View development logs"
	@echo "  make shell        - Open backend shell"
	@echo "  make db-shell     - Open database shell"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Deploy to production"
	@echo "  make staging      - Deploy to staging"
	@echo ""
	@echo "Database:"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-create NAME=migration_name - Create new migration"
	@echo "  make seed         - Seed database with sample data"
	@echo "  make backup       - Backup production database"
	@echo ""
	@echo "Maintenance:"
	@echo "  make down         - Stop all services"
	@echo "  make clean        - Remove containers and volumes"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make health       - Check service health"

# Development
dev:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development environment started"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Adminer: http://localhost:8080"

build:
	docker-compose -f docker-compose.dev.yml build

logs:
	docker-compose -f docker-compose.dev.yml logs -f

shell:
	docker-compose -f docker-compose.dev.yml exec backend bash

db-shell:
	docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d chefgpt

# Production
prod:
	./scripts/deploy.sh production

staging:
	./scripts/deploy.sh staging

# Database
migrate:
	docker-compose -f docker-compose.dev.yml run --rm backend alembic upgrade head

migrate-create:
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required. Usage: make migrate-create NAME=migration_name"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.dev.yml run --rm backend alembic revision --autogenerate -m "$(NAME)"

seed:
	docker-compose -f docker-compose.dev.yml exec backend python scripts/seed_recipes.py
	docker-compose -f docker-compose.dev.yml exec backend python scripts/reindex_recipes.py

backup:
	./scripts/backup.sh production

# Maintenance
down:
	docker-compose -f docker-compose.dev.yml down

clean:
	docker-compose -f docker-compose.dev.yml down -v
	docker image prune -f

test:
	docker-compose -f docker-compose.dev.yml run --rm backend pytest

lint:
	docker-compose -f docker-compose.dev.yml run --rm backend ruff check .
	docker-compose -f docker-compose.dev.yml run --rm backend black --check .

health:
	./scripts/health-check.sh development

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Security
security-scan:
	docker-compose -f docker-compose.dev.yml run --rm backend safety check
	docker-compose -f docker-compose.dev.yml run --rm backend bandit -r app/
