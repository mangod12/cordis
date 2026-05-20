"""Contract tests — verify all agents return expected output shapes.

Ensures agent outputs match the schemas downstream consumers depend on.
"""
import pytest
from app.core.schemas.intent import IntentType
from app.core.schemas.severity import SeverityAssessment, SeverityLevel
from app.core.schemas.emotion import EmotionAnalysis


class TestIntentTypeContract:
    def test_all_intent_types_defined(self):
        """Intent enum must have all expected emergency types."""
        expected = {"medical", "fire", "violent_crime", "accident",
                    "gas_hazard", "mental_health", "non_emergency", "unknown"}
        actual = {e.value for e in IntentType}
        assert expected.issubset(actual), f"Missing intents: {expected - actual}"


class TestSeverityAssessmentContract:
    def test_severity_levels_defined(self):
        expected = {"critical", "high", "medium", "low"}
        actual = {e.value for e in SeverityLevel}
        assert expected == actual

    def test_severity_assessment_has_required_fields(self):
        sa = SeverityAssessment(
            level=SeverityLevel.HIGH,
            score=0.75,
            factors={"test": 1.0},
            reasoning="test reasoning",
            confidence=0.9,
        )
        assert sa.level == SeverityLevel.HIGH
        assert 0 <= sa.score <= 1
        assert isinstance(sa.factors, dict)
        assert isinstance(sa.reasoning, str)
        assert 0 <= sa.confidence <= 1


class TestCrisisTypesContract:
    def test_all_indian_disaster_types_covered(self):
        """Orchestrator must handle all common Indian disaster types."""
        from app.agents.logistics.orchestrator import _CRISIS_TYPES
        required_disasters = ["flood", "cyclone", "earthquake", "tsunami",
                             "landslide", "drought", "famine", "fire"]
        for disaster in required_disasters:
            assert disaster in _CRISIS_TYPES, f"Missing disaster type: {disaster}"

    def test_all_resource_types_covered(self):
        """Orchestrator must handle key relief resource types."""
        from app.agents.logistics.orchestrator import _RESOURCES
        required_resources = ["food", "water", "medicine", "shelter", "fuel"]
        for resource in required_resources:
            assert resource in _RESOURCES, f"Missing resource type: {resource}"


class TestGeodataContract:
    def test_minimum_airport_count(self):
        from app.services.logistics.tools.route_tool import AIRPORTS
        assert len(AIRPORTS) >= 19

    def test_minimum_port_count(self):
        from app.services.logistics.tools.route_tool import PORTS
        assert len(PORTS) >= 13

    def test_minimum_city_count(self):
        from app.services.logistics.tools.weather_tool import _CITY_COORDS
        assert len(_CITY_COORDS) >= 60, f"Only {len(_CITY_COORDS)} cities, need 60+"

    def test_disaster_prone_states_covered(self):
        from app.services.logistics.tools.weather_tool import _CITY_COORDS
        required_states = ["odisha", "bihar", "assam", "kerala", "uttarakhand",
                          "tamil nadu", "andhra pradesh", "gujarat", "rajasthan",
                          "west bengal", "karnataka", "maharashtra"]
        for state in required_states:
            assert state in _CITY_COORDS, f"Missing state: {state}"
