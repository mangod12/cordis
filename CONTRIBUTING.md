# Contributing to Cordis

Thanks for considering a contribution. This project helps NGOs and emergency responders coordinate crisis response — every improvement has real impact.

## Getting Started

1. Fork the repo
2. Clone your fork
3. Set up the dev environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set SECRET_KEY in .env
```

4. Run the tests:

```bash
pytest tests/ -v
```

5. Start the dev server:

```bash
uvicorn app.main:app --reload --port 8000
```

## What to Work On

### High Impact

- **Multilingual support** — Whisper translate mode, multilingual prompts for Gemini agents
- **Offline mode hardening** — ensure full pipeline works without internet
- **One-click deploy** — Render, Railway, or Cloud Run deploy button
- **Frontend dashboard** — React/Next.js UI for the combined triage + logistics view

### Medium Impact

- **More test coverage** — especially for the logistics pipeline and connector
- **Local LLM support** — Ollama integration for zero-cost logistics mode
- **Docker image on GHCR** — pre-built image so NGOs don't need to build from source
- **i18n for UI** — localized interface for field teams

### Good First Issues

- Add more crisis keywords to the severity engine
- Add more Indian cities to the route tool coordinate lookup
- Write tests for the pipeline connector
- Improve error messages in the logistics API

## Code Style

- Python 3.11+
- Type hints on public functions
- Keep files under 500 lines
- No hardcoded secrets or credentials
- Run tests before submitting PRs

## Pull Requests

1. Create a branch from `master`
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Push and open a PR with a clear description
5. Link any related issues

## Reporting Issues

Open an issue on GitHub. Include:
- What you expected
- What happened
- Steps to reproduce
- Environment (OS, Python version, etc.)

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
