"""Unit tests for orchestrator helper functions — no LLM, no DB required."""
import pytest


class TestComputeSeverity:
    def test_critical_threshold(self):
        from app.agents.logistics.orchestrator import _compute_severity
        assert _compute_severity(300) == "Critical"
        assert _compute_severity(500) == "Critical"

    def test_moderate_threshold(self):
        from app.agents.logistics.orchestrator import _compute_severity
        assert _compute_severity(100) == "Moderate"
        assert _compute_severity(200) == "Moderate"
        assert _compute_severity(299) == "Moderate"

    def test_low_threshold(self):
        from app.agents.logistics.orchestrator import _compute_severity
        assert _compute_severity(50) == "Low"
        assert _compute_severity(99) == "Low"


class TestShouldForceReplan:
    def test_flood_triggers_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Massive flood in coastal region") is True

    def test_cyclone_triggers_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Cyclone warning for eastern coast") is True

    def test_earthquake_triggers_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Earthquake magnitude 7.2") is True

    def test_normal_query_no_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Routine supply delivery to depot") is False

    def test_war_triggers_replan(self):
        from app.agents.logistics.orchestrator import _should_force_replan
        assert _should_force_replan("Armed conflict in border region") is True


class TestCrisisTypeLookup:
    def test_known_crisis_types(self):
        from app.agents.logistics.orchestrator import _CRISIS_TYPES
        assert _CRISIS_TYPES["flood"] == "Flood"
        assert _CRISIS_TYPES["earthquake"] == "Earthquake"
        assert _CRISIS_TYPES["cyclone"] == "Cyclone"
        assert _CRISIS_TYPES["tsunami"] == "Tsunami"
        assert _CRISIS_TYPES["war"] == "Armed Conflict"

    def test_resource_lookup(self):
        from app.agents.logistics.orchestrator import _RESOURCES
        assert _RESOURCES["food"] == "Food Supply"
        assert _RESOURCES["medicine"] == "Medical Supplies"
        assert _RESOURCES["water"] == "Drinking Water"


class TestComputeRealMetrics:
    def test_known_route_produces_valid_metrics(self):
        from app.agents.logistics.orchestrator import _compute_real_metrics
        fb = {
            "source": "Rourkela Depot",
            "destination": "Bhubaneswar",
            "quantity": 200,
            "route": "NH-49",
        }
        metrics = _compute_real_metrics(fb)
        assert "eta_hrs" in metrics
        assert "truck_count" in metrics
        assert metrics["truck_count"] >= 2
        assert metrics["eta_hrs"] > 0

    def test_unknown_city_uses_defaults(self):
        from app.agents.logistics.orchestrator import _compute_real_metrics
        fb = {
            "source": "UnknownCity Depot",
            "destination": "NowhereLand",
            "quantity": 100,
            "route": "NH-1",
        }
        metrics = _compute_real_metrics(fb)
        assert metrics["eta_hrs"] == 2.5
        assert metrics["truck_count"] >= 2
