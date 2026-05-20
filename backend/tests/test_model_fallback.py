"""Tests that the system degrades gracefully when ML models are unavailable."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.severity_service import compute_severity
from app.services.dispatch_service import select_responder


class TestSeverityWithoutML:
    """Severity should work purely from keywords when ML is unavailable."""

    @pytest.mark.asyncio
    async def test_keyword_only_fire(self):
        """Fire keyword should score high even without ML emotion."""
        severity = await compute_severity("fire in the building", "neutral")
        assert severity in ("high", "critical")

    @pytest.mark.asyncio
    async def test_keyword_only_medical(self):
        severity = await compute_severity("person not breathing cardiac arrest", "neutral")
        assert severity == "critical"

    @pytest.mark.asyncio
    async def test_no_keywords_returns_low(self):
        severity = await compute_severity("hello world", "neutral")
        assert severity == "low"

    @pytest.mark.asyncio
    async def test_unknown_emotion_doesnt_crash(self):
        severity = await compute_severity("fire", "completely_fake_emotion")
        assert severity in ("high", "critical")


class TestDispatchWithoutML:
    """Dispatch should always return a valid responder."""

    @pytest.mark.asyncio
    async def test_always_returns_string(self):
        for intent in ["fire", "medical", "accident", "gas_hazard", "violent_crime",
                       "mental_health", "non_emergency", "unknown", "", "garbage"]:
            for severity in ["critical", "high", "medium", "low", "unknown"]:
                result = await select_responder(intent, severity)
                assert isinstance(result, str), f"Non-string for {intent}/{severity}"
                assert len(result) > 0, f"Empty for {intent}/{severity}"

    @pytest.mark.asyncio
    async def test_critical_always_dispatches(self):
        for intent in ["fire", "medical", "accident"]:
            result = await select_responder(intent, "critical")
            assert result != "call_center_followup", f"Critical {intent} got followup"


class TestPipelineConnectorFallback:
    """Pipeline connector should handle edge cases gracefully."""

    def test_disabled_logistics_never_triggers(self):
        from app.services.pipeline_connector import should_trigger_logistics
        with patch("app.services.pipeline_connector.settings") as mock:
            mock.LOGISTICS_ENABLED = False
            assert should_trigger_logistics("critical", "FIRE") is False

    def test_query_building_handles_empty_transcript(self):
        from app.services.pipeline_connector import build_crisis_query
        query = build_crisis_query("", "FIRE", "critical", "fear", "fire_dispatch")
        assert isinstance(query, str)
        assert len(query) > 0
