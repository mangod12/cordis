"""API schema validation tests.

Verifies that API endpoint response models have all required fields
and correct types.
"""
import pytest
from pydantic import ValidationError
from app.api.v1.endpoints.emergency import EmergencyResponse, EmergencyJSONRequest
from app.api.v1.endpoints.logistics import LogisticsExecuteRequest, LogisticsExecuteResponse


class TestEmergencyResponseSchema:
    def test_valid_response(self):
        resp = EmergencyResponse(
            call_id="test-123",
            transcript="fire at building",
            intent="fire",
            intent_confidence=0.85,
            emotion="fear",
            severity="critical",
            responder="fire_dispatch",
            latency_ms=50,
            caller_id=None,
        )
        assert resp.call_id == "test-123"
        assert resp.severity == "critical"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            EmergencyResponse(
                call_id="test",
                # missing transcript and other required fields
            )


class TestEmergencyRequestSchema:
    def test_valid_json_request(self):
        req = EmergencyJSONRequest(transcript="help there is a fire")
        assert req.transcript == "help there is a fire"
        assert req.caller_id is None

    def test_transcript_max_length(self):
        with pytest.raises(ValidationError):
            EmergencyJSONRequest(transcript="x" * 10001)

    def test_with_caller_id(self):
        req = EmergencyJSONRequest(transcript="fire", caller_id="caller-001")
        assert req.caller_id == "caller-001"


class TestLogisticsRequestSchema:
    def test_valid_request(self):
        req = LogisticsExecuteRequest(query="Flood in Odisha causing food shortage")
        assert len(req.query) > 0

    def test_too_short_query(self):
        with pytest.raises(ValidationError):
            LogisticsExecuteRequest(query="hi")

    def test_too_long_query(self):
        with pytest.raises(ValidationError):
            LogisticsExecuteRequest(query="x" * 2001)


class TestLogisticsResponseSchema:
    def test_valid_response(self):
        resp = LogisticsExecuteResponse(
            task_id="abc-123",
            status="PENDING",
            message="Pipeline started",
        )
        assert resp.task_id == "abc-123"
