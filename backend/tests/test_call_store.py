"""Tests for the Redis-backed call store."""
import pytest
from app.dashboard.call_store import add_call


class TestCallStore:
    def test_add_call_returns_id(self):
        call_id = add_call(
            transcript="test call",
            intent="fire",
            intent_confidence=0.9,
            emotion="fear",
            emotion_confidence=0.8,
            severity="high",
            severity_score=0.75,
            responder="fire_dispatch",
            fallback_used=False,
            intent_fallback=False,
            emotion_fallback=False,
            latency_ms=50.0,
            tenant_id="test",
        )
        assert isinstance(call_id, str)
        assert len(call_id) == 8  # hex UUID prefix

    def test_add_call_unique_ids(self):
        ids = set()
        for _ in range(100):
            cid = add_call(
                transcript="test",
                intent="fire",
                intent_confidence=0.5,
                emotion="neutral",
                emotion_confidence=0.5,
                severity="low",
                severity_score=0.3,
                responder="general",
                fallback_used=False,
                intent_fallback=False,
                emotion_fallback=False,
                latency_ms=10.0,
            )
            ids.add(cid)
        assert len(ids) == 100  # All unique
