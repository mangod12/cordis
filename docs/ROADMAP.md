# Cordis Roadmap

## v0.2 — Visual Impact (Next Release)

### Frontend Dashboard
- [ ] React/Next.js app with real-time crisis dashboard
- [ ] Interactive map (Leaflet) showing crisis locations, routes, resources
- [ ] Voice input with live waveform visualization
- [ ] Agent pipeline visualization (animated flow showing each agent's status)
- [ ] Logistics route visualization with ETA overlays
- [ ] Dark mode, responsive design

### Demo & Documentation
- [ ] 60-second demo GIF showing full pipeline
- [ ] Architecture diagram (Mermaid/SVG)
- [ ] README redesign with hero image, badges, comparison table
- [ ] API usage examples with screenshots

## v0.3 — Production Hardening

### Testing
- [ ] Logistics pipeline integration tests
- [ ] Pipeline connector unit tests
- [ ] API endpoint integration tests (mocked ML)
- [ ] WebSocket tests
- [ ] Coverage target: 80%+

### Infrastructure
- [ ] GitHub Actions CI/CD (lint, test, coverage, Docker build)
- [ ] Docker image published to GHCR
- [ ] One-click deploy (Railway, Render)
- [ ] Kubernetes manifests + Helm chart
- [ ] Health check with full dependency status

### Reliability
- [ ] Retry logic for logistics pipeline (replace bare asyncio.create_task)
- [ ] Dead letter queue for failed logistics triggers
- [ ] Circuit breaker on Gemini API calls
- [ ] Graceful degradation metrics

## v0.4 — Advanced Features

### Real-time Capabilities
- [ ] Live voice streaming via WebSocket (running Whisper)
- [ ] Real-time severity updates as audio streams in
- [ ] Agent observability UI (trace every tool call, reasoning step)

### Intelligence
- [ ] Digital twin simulator (pre-loaded disaster scenarios)
- [ ] Multi-language auto-detect and routing (Whisper 99 languages)
- [ ] Local LLM support (Ollama) for zero-cost logistics mode
- [ ] Community crisis reporting (crowdsourced data integration)

### Platform
- [ ] Multi-tenant enforcement middleware
- [ ] Audit logging (wire up existing AuditLog model)
- [ ] API rate limiting per tenant
- [ ] Webhook notifications for dispatch events

## v1.0 — Production Release

- [ ] HIPAA/GDPR compliance documentation
- [ ] Performance benchmarks and comparison to commercial alternatives
- [ ] Disaster recovery documentation (backup/restore, RTO/RPO)
- [ ] Load testing results (k6/locust)
- [ ] Security audit completed
- [ ] 3+ real-world deployment case studies

## Future Ideas
- Drone dispatch integration (simulated)
- Satellite imagery for disaster assessment
- SMS/WhatsApp intake (Twilio integration)
- Mobile app for field teams
- Federated deployment (multi-region)
