"""Tests for pipeline_connector — bridges triage to logistics."""
import pytest
from unittest.mock import patch

from app.services.pipeline_connector import (
    should_trigger_logistics,
    build_crisis_query,
)


class TestShouldTriggerLogistics:
    def test_critical_fire_triggers(self):
        assert should_trigger_logistics("critical", "FIRE") is True

    def test_critical_medical_triggers(self):
        assert should_trigger_logistics("critical", "MEDICAL") is True

    def test_high_accident_triggers(self):
        assert should_trigger_logistics("high", "ACCIDENT") is True

    def test_high_gas_hazard_triggers(self):
        assert should_trigger_logistics("high", "GAS_HAZARD") is True

    def test_low_fire_does_not_trigger(self):
        assert should_trigger_logistics("low", "FIRE") is False

    def test_critical_noise_complaint_does_not_trigger(self):
        assert should_trigger_logistics("critical", "NON_EMERGENCY") is False

    def test_medium_medical_does_not_trigger(self):
        assert should_trigger_logistics("medium", "MEDICAL") is False

    def test_auto_dispatch_false_blocks(self):
        assert should_trigger_logistics("critical", "FIRE", auto_dispatch=False) is False

    @patch("app.services.pipeline_connector.settings")
    def test_logistics_disabled_blocks(self, mock_settings):
        mock_settings.LOGISTICS_ENABLED = False
        assert should_trigger_logistics("critical", "FIRE") is False


class TestBuildCrisisQuery:
    def test_contains_severity(self):
        query = build_crisis_query("fire at warehouse", "FIRE", "critical", "fear", "fire_dispatch")
        assert "Critical" in query

    def test_contains_intent(self):
        query = build_crisis_query("fire at warehouse", "FIRE", "critical", "fear", "fire_dispatch")
        assert "Fire" in query

    def test_contains_transcript_excerpt(self):
        query = build_crisis_query("massive fire at 5th street", "FIRE", "high", "fear", "fire_dispatch")
        assert "massive fire at 5th street" in query

    def test_critical_adds_expedite(self):
        query = build_crisis_query("fire", "FIRE", "critical", "fear", "fire_dispatch")
        assert "CRITICAL" in query
        assert "expedite" in query.lower()

    def test_high_no_expedite(self):
        query = build_crisis_query("fire", "FIRE", "high", "fear", "fire_dispatch")
        assert "expedite" not in query.lower()

    def test_truncates_long_transcript(self):
        long_text = "x" * 1000
        query = build_crisis_query(long_text, "FIRE", "high", "fear", "fire_dispatch")
        assert len(query) < 1100
