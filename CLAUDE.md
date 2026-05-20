# Cordis — AI Crisis Coordination Platform

## Project Overview
End-to-end AI crisis coordination: voice/text distress → ML triage → multi-agent logistics dispatch.
Built for NGOs, disaster relief orgs, and emergency operations centers.

## Architecture
- **Backend**: Python 3.11+ / FastAPI / async SQLAlchemy
- **Triage Pipeline**: Whisper STT → IntentAgent (ONNX) → EmotionAgent (ONNX) → SeverityAgent → DispatchAgent
- **Logistics Pipeline**: ResourceAgent → PlanningAgent → ReplanningAgent → ExecutionAgent (Gemini 2.5 Flash)
- **Database**: PostgreSQL + pgvector (SQLite for dev)
- **Cache**: Redis (pub/sub + caching)

## Key Files
- `backend/app/main.py` — FastAPI entry point, lifespan, middleware
- `backend/app/core/config.py` — All configuration (Pydantic Settings)
- `backend/app/agents/logistics/orchestrator.py` — Central pipeline coordinator
- `backend/app/api/v1/endpoints/emergency.py` — POST /process-emergency
- `backend/app/api/v1/endpoints/logistics.py` — Logistics API
- `backend/app/services/pipeline_connector.py` — Bridges triage → logistics

## Commands
```bash
# Dev setup
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env

# Run
uvicorn app.main:app --reload --port 8000

# Test
cd backend && pytest tests/ -v

# Docker
docker compose up

# Syntax check
cd backend && python -c "import ast, os; [ast.parse(open(os.path.join(r,f)).read()) for r,_,fs in os.walk('app') for f in fs if f.endswith('.py')]"
```

## Code Conventions
- Immutability preferred, no mutation of shared state
- Type hints on all public functions (`from __future__ import annotations`)
- Files < 500 lines (orchestrator.py is exception at ~1100)
- Fallback chains: ML model → keyword heuristic → deterministic default
- All agents must work offline (deterministic fallback required)
- structlog for logging (JSON format), never print()
- Pydantic v2 for all schemas
- async/await throughout, no blocking IO on event loop

## Testing
- pytest + pytest-asyncio
- Mock ML models in tests (don't require ONNX/Whisper)
- Test files: `backend/tests/test_*.py`
- Current coverage: ~40% (triage agents tested, logistics pipeline untested)

## Environment Variables
- `SECRET_KEY` (required) — JWT signing
- `GEMINI_API_KEY` (optional) — enables LLM logistics pipeline
- `USE_SQLITE=true` — dev mode; `false` for PostgreSQL
- `LOGISTICS_ENABLED=true` — toggle logistics pipeline
- `WHISPER_MODEL_SIZE=small` — tiny|base|small|medium|large
