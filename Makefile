.PHONY: help setup test lint run docker demo-fire demo-flood demo-medical clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies and configure environment
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd backend && cp -n .env.example .env || true
	@echo "Edit backend/.env to set SECRET_KEY"

test: ## Run all tests
	cd backend && SECRET_KEY=test USE_SQLITE=true LOGISTICS_ENABLED=true python -m pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	cd backend && SECRET_KEY=test USE_SQLITE=true LOGISTICS_ENABLED=true python -m pytest tests/ -v --cov=app --cov-report=term-missing

lint: ## Run linter
	cd backend && ruff check app/

lint-fix: ## Auto-fix lint errors
	cd backend && ruff check app/ --fix

run: ## Start development server
	cd backend && TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker: ## Start with Docker Compose (PostgreSQL + Redis + Backend)
	docker compose up --build

TOKEN ?= $(shell cd backend && python -c "from app.core.security import create_access_token; from datetime import timedelta; print(create_access_token('demo', tenant_id='demo', role='admin', expires_delta=timedelta(hours=24)))")

demo-fire: ## Simulate a critical fire emergency
	@curl -s -X POST http://localhost:8000/process-emergency \
		-H "Authorization: Bearer $(TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{"transcript": "Massive fire at warehouse in Bhubaneswar, people trapped inside, building collapsing"}' | python -m json.tool

demo-flood: ## Simulate a flood logistics scenario
	@curl -s -X POST http://localhost:8000/process-emergency \
		-H "Authorization: Bearer $(TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{"transcript": "Severe flooding in Odisha, three districts cut off, thousands need food and water immediately"}' | python -m json.tool

demo-medical: ## Simulate a medical emergency
	@curl -s -X POST http://localhost:8000/process-emergency \
		-H "Authorization: Bearer $(TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{"transcript": "Person collapsed and not breathing at Delhi metro station, cardiac arrest suspected"}' | python -m json.tool

demo-accident: ## Simulate a highway accident
	@curl -s -X POST http://localhost:8000/process-emergency \
		-H "Authorization: Bearer $(TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{"transcript": "Major multi-vehicle pileup on Mumbai-Pune expressway, multiple injuries, road completely blocked"}' | python -m json.tool

demo-gas: ## Simulate a gas leak
	@curl -s -X POST http://localhost:8000/process-emergency \
		-H "Authorization: Bearer $(TOKEN)" \
		-H "Content-Type: application/json" \
		-d '{"transcript": "Strong gas smell in residential building in Chennai, residents evacuating, possible pipeline rupture"}' | python -m json.tool

demo-all: demo-fire demo-flood demo-medical demo-accident demo-gas ## Run all demo scenarios

clean: ## Remove generated files
	cd backend && rm -f cordis.db
	cd backend && rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
