# Cordis

**Open-source AI crisis coordination — from distress call to resource dispatch.**

Cordis is an end-to-end platform that takes a voice or text distress report, triages it using on-device ML (Whisper, ONNX), and — for critical emergencies — automatically coordinates logistics response using a multi-agent pipeline powered by Gemini.

Built for NGOs, disaster relief organizations, and emergency operations centers that need fast, free, and deployable crisis tooling.

```
Voice/Text → Whisper STT → Intent (ONNX) → Emotion (ONNX) → Severity
                                                                 ↓ (critical/high)
                                                    ResourceAgent → PlanningAgent
                                                        → ReplanningAgent (if crisis)
                                                        → ExecutionAgent (dispatch)
```

---

## What It Does

### Emergency Triage

| Step | Agent | How |
|------|-------|-----|
| Transcription | Whisper STT | Local, 99 languages, no API costs |
| Intent Classification | IntentAgent | ONNX DistilBERT — 8 types (medical, fire, violent crime, accident, etc.) |
| Emotion Detection | EmotionAgent | ONNX model — 7 emotions with circuit breaker fallback |
| Severity Assessment | SeverityAgent | Deterministic scoring: intent + keywords + emotion + reasoning |
| Dispatch | DispatchAgent | Routes to responder (ambulance, fire, police) based on intent + severity |

### Logistics Coordination

| Step | Agent | How |
|------|-------|-----|
| Resource Audit | ResourceAgent | Warehouse inventory + live weather (Open-Meteo) + NASA disaster feeds |
| Route Planning | PlanningAgent | Depot selection, cost/ETA comparison, dispatch strategy |
| Crisis Replanning | ReplanningAgent | Reroutes when roads blocked — uses real airports/ports + alternative routes |
| Execution | ExecutionAgent | Creates subtasks, schedules deliveries, assigns truck counts |

All logistics agents use **Gemini 2.5 Flash** with function calling. Each has deterministic fallbacks that produce realistic output without any LLM — the system works offline.

### Pipeline Connector

When triage produces a **critical or high severity** result for fire, medical, accident, or gas hazard intents, the logistics pipeline auto-triggers in the background. Emergency response returns immediately.

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/process-emergency` | Full triage — accepts audio file or text transcript |
| POST | `/api/v1/logistics/execute` | Run logistics pipeline for a crisis scenario |
| GET | `/api/v1/logistics/tasks/{id}` | Get task with plan, schedule, and reasoning |
| GET | `/api/v1/logistics/tasks/{id}/logs` | Agent execution logs (every tool call, every decision) |
| POST | `/api/v1/auth/login` | JWT authentication |
| GET | `/api/v1/calls/live` | Live dashboard feed |
| WS | `/ws/calls/{call_id}` | Real-time call event stream |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

---

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
# Set your Gemini API key (optional — logistics works without it via fallbacks)
export GEMINI_API_KEY=your-key-here

docker compose up
```

This starts PostgreSQL (with pgvector), Redis, and the backend.

### Option 2: Local Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: set SECRET_KEY (required), GEMINI_API_KEY (optional)

# Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for the Swagger UI.

### Test the triage pipeline

```bash
curl -X POST http://localhost:8000/process-emergency \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transcript": "There is a massive fire at the warehouse on 5th street, people are trapped inside", "caller_id": "test-001"}'
```

### Test the logistics pipeline

```bash
curl -X POST http://localhost:8000/api/v1/logistics/execute \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Flood in Odisha causing food shortage across 3 districts"}'
```

---

## Architecture

```
backend/
├── app/
│   ├── agents/
│   │   ├── intent/              # ONNX DistilBERT intent classification
│   │   ├── emotion/             # ONNX emotion detection + circuit breaker
│   │   ├── severity/            # Deterministic severity scoring
│   │   ├── dispatch/            # Responder routing
│   │   ├── stt/                 # Whisper speech-to-text
│   │   ├── reasoning/           # Groq LLM reasoning (optional)
│   │   ├── safety/              # Safety assessment
│   │   └── logistics/           # Gemini multi-agent pipeline
│   │       ├── resource.py      #   Inventory + weather + disaster feeds
│   │       ├── planner.py       #   Route planning + dispatch strategy
│   │       ├── replanning.py    #   Crisis rerouting (airports, ports, alt routes)
│   │       ├── execution.py     #   Task creation + delivery scheduling
│   │       └── orchestrator.py  #   Pipeline coordinator
│   ├── api/v1/endpoints/
│   │   ├── emergency.py         # Triage endpoint
│   │   └── logistics.py         # Logistics endpoint
│   ├── services/
│   │   ├── logistics/
│   │   │   ├── tools/           # 10 tools: weather, routes, disaster feeds, etc.
│   │   │   ├── llm/             # Gemini client (API key or Vertex AI)
│   │   │   ├── memory/          # pgvector-backed agent memory
│   │   │   └── mcp_server.py    # Model Context Protocol server
│   │   ├── pipeline_connector.py # Bridges triage → logistics
│   │   ├── whisper_service.py
│   │   └── severity_service.py
│   ├── models/                  # SQLAlchemy models (triage + logistics)
│   ├── core/                    # Config, security, database, Redis
│   └── main.py                  # FastAPI entry point
├── tests/
└── requirements.txt
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI + async SQLAlchemy |
| Triage ML | Whisper (local STT), ONNX Runtime (intent + emotion), Groq (optional reasoning) |
| Logistics LLM | Google Gemini 2.5 Flash via function calling |
| Database | PostgreSQL + pgvector (SQLite for dev) |
| Cache | Redis (pub/sub, caching, dashboard) |
| Real-time | WebSockets + Redis pub/sub |
| External Data | Open-Meteo (weather), NASA EONET (disasters), OpenRouteService (routes) |
| Auth | JWT (HS256) + rate limiting + tenant isolation |
| Observability | structlog (JSON), Prometheus metrics |
| Protocol | MCP (Model Context Protocol) for tool exposure |

---

## Configuration

All config via environment variables or `.env` file. See [`backend/.env.example`](backend/.env.example).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | JWT signing key |
| `USE_SQLITE` | No | `true` | Use SQLite for dev (set `false` + configure Postgres for production) |
| `GEMINI_API_KEY` | No | — | Enables logistics LLM pipeline (works without via fallbacks) |
| `LOGISTICS_ENABLED` | No | `true` | Toggle logistics pipeline on/off |
| `WHISPER_MODEL_SIZE` | No | `small` | Whisper model: tiny, base, small, medium, large |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection |
| `GROQ_API_KEY` | No | — | Optional reasoning agent LLM |

---

## Offline / Zero-Cost Mode

Cordis works without any paid APIs:

- **Whisper** runs locally (no OpenAI API)
- **Intent + Emotion** use local ONNX models (no cloud ML)
- **Logistics agents** have deterministic fallbacks that produce realistic dispatch plans without Gemini
- **Weather data** from Open-Meteo (free, no key)
- **Disaster feeds** from NASA EONET (free, no key)
- **Route planning** from OpenRouteService (free tier: 2000 req/day)

Set `LOGISTICS_ENABLED=true` without `GEMINI_API_KEY` — the system uses fallback logic automatically.

---

## Real Data Sources

The logistics pipeline uses real geographic and operational data:

- **19 airports** with coordinates, runway lengths, and IAF base indicators
- **13 major ports** with capacity data (MT/year)
- **Haversine distance** calculations for realistic ETAs
- **Live weather** via Open-Meteo API
- **River discharge / flood alerts** via Open-Meteo Flood API
- **Active natural events** via NASA EONET (Earth Observatory Natural Event Tracker)
- **Road routing** via OpenRouteService with blocked-road avoidance

---

## Contributing

Contributions welcome. This project exists to help people in crisis — every improvement matters.

```bash
# Run tests
cd backend
pytest tests/ -v

# Check syntax
python -c "import ast, os; [ast.parse(open(os.path.join(r,f)).read()) for r,_,fs in os.walk('app') for f in fs if f.endswith('.py')]"
```

See [LICENSE](LICENSE) for terms (Apache 2.0).

---

## History

Cordis began as two separate projects:

- **Redline-AI** — an AI-powered emergency triage system (voice → intent → severity → dispatch)
- **TaskForge** — a multi-agent logistics coordination engine for crisis supply chains

In May 2026, both were merged into **Cordis** — a single end-to-end platform that connects distress calls directly to resource dispatch. The name comes from the Latin word for "heart."

---

## License

Apache License 2.0 — free to use, modify, and distribute. See [LICENSE](LICENSE).
