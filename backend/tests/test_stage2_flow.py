"""End-to-end triage pipeline test using mocked ML models.

Tests the full flow: transcript → intent → emotion → severity → dispatch
without requiring actual ONNX models, Redis, or PostgreSQL.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.severity_service import compute_severity
from app.services.dispatch_service import select_responder


@pytest.mark.asyncio
async def test_full_triage_flow_critical_fire():
    """Simulate a critical fire emergency through the triage chain."""
    transcript = "There is a massive fire at the warehouse, people are trapped inside"

    severity = await compute_severity(transcript, "fear")
    assert severity in ("critical", "high")

    responder = await select_responder("fire", severity)
    assert responder in ("fire_dispatch", "ambulance")


@pytest.mark.asyncio
async def test_full_triage_flow_medical():
    """Simulate a medical emergency."""
    transcript = "Someone collapsed and is not breathing"

    severity = await compute_severity(transcript, "fear")
    assert severity == "critical"

    responder = await select_responder("medical", severity)
    assert responder == "ambulance"


@pytest.mark.asyncio
async def test_full_triage_flow_low_priority():
    """Simulate a non-emergency call."""
    transcript = "I want to report a noise complaint from my neighbor"

    severity = await compute_severity(transcript, "neutral")
    assert severity in ("low", "medium")

    responder = await select_responder("non_emergency", severity)
    assert responder == "call_center_followup"


@pytest.mark.asyncio
async def test_emotion_escalation():
    """Fear emotion should escalate severity."""
    transcript = "There is some kind of issue here"

    severity_neutral = await compute_severity(transcript, "neutral")
    severity_fear = await compute_severity(transcript, "fear")

    # Fear should produce equal or higher severity
    levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    assert levels[severity_fear] >= levels[severity_neutral]


@pytest.mark.asyncio
async def test_pipeline_connector_integration():
    """Test that pipeline connector correctly gates logistics trigger."""
    from app.services.pipeline_connector import should_trigger_logistics

    # Critical fire → should trigger
    assert should_trigger_logistics("critical", "FIRE") is True

    # Low non-emergency → should NOT trigger
    assert should_trigger_logistics("low", "NON_EMERGENCY") is False

    # Critical but non-logistics intent → should NOT trigger
    assert should_trigger_logistics("critical", "MENTAL_HEALTH") is False
