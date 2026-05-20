"""Load tests for the triage pipeline.

Tests concurrent request handling and latency under load.
Run with: pytest tests/test_load.py -v
"""
import asyncio
import time
import pytest
from app.services.severity_service import compute_severity
from app.services.dispatch_service import select_responder


SCENARIOS = [
    ("Massive fire at warehouse, people trapped", "fear", "fire"),
    ("Person not breathing, cardiac arrest", "fear", "medical"),
    ("Car accident on highway, multiple injuries", "neutral", "accident"),
    ("Gas leak in building, evacuation underway", "fear", "gas_hazard"),
    ("Flooding in district, thousands displaced", "fear", "unknown"),
    ("Noise complaint from neighbor", "neutral", "non_emergency"),
    ("Someone collapsed at metro station", "fear", "medical"),
    ("Building on fire, smoke everywhere", "fear", "fire"),
    ("Cyclone approaching coast, winds 150kmph", "fear", "unknown"),
    ("Earthquake shaking buildings", "fear", "unknown"),
]


class TestTriageThroughput:
    @pytest.mark.asyncio
    async def test_10_concurrent_triages(self):
        """10 concurrent triage operations should complete within 1 second."""
        start = time.perf_counter()

        async def triage(transcript, emotion, intent):
            severity = await compute_severity(transcript, emotion)
            responder = await select_responder(intent, severity)
            return severity, responder

        tasks = [triage(t, e, i) for t, e, i in SCENARIOS]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

        assert len(results) == 10
        assert all(r[0] in ("critical", "high", "medium", "low") for r in results)
        assert all(r[1] is not None for r in results)
        assert elapsed < 1.0, f"10 triages took {elapsed:.2f}s, should be < 1s"

    @pytest.mark.asyncio
    async def test_100_sequential_triages(self):
        """100 sequential triages should complete within 2 seconds."""
        start = time.perf_counter()
        for i in range(100):
            t, e, intent = SCENARIOS[i % len(SCENARIOS)]
            severity = await compute_severity(t, e)
            responder = await select_responder(intent, severity)
            assert severity in ("critical", "high", "medium", "low")
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0, f"100 triages took {elapsed:.2f}s, should be < 2s"

    @pytest.mark.asyncio
    async def test_severity_deterministic(self):
        """Same input should always produce same output (no randomness)."""
        results = []
        for _ in range(50):
            severity = await compute_severity("massive fire at warehouse people trapped", "fear")
            results.append(severity)
        assert len(set(results)) == 1, f"Non-deterministic severity: {set(results)}"
