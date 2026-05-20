"""Golden scenario tests — validates triage pipeline against known emergency scenarios.

Each JSON file in tests/scenarios/ defines an emergency with expected outputs.
Tests verify intent classification, severity scoring, dispatch routing, and
logistics trigger decisions match expectations.
"""
import json
import pytest
from pathlib import Path

from app.services.severity_service import compute_severity
from app.services.dispatch_service import select_responder
from app.services.pipeline_connector import should_trigger_logistics

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


def _load_scenarios():
    """Load all JSON scenario files."""
    scenarios = []
    for f in sorted(SCENARIOS_DIR.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
            data["_file"] = f.name
            scenarios.append(data)
    return scenarios


SCENARIOS = _load_scenarios()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["_file"])
@pytest.mark.asyncio
async def test_severity_matches_expected(scenario):
    """Severity should fall within expected range for each scenario."""
    if "expected_severity" not in scenario:
        pytest.skip("No expected_severity in scenario")

    transcript = scenario.get("transcript", scenario.get("logistics_query", ""))
    # Use fear emotion for critical scenarios, neutral otherwise
    emotion = "fear" if "critical" in scenario["expected_severity"] else "neutral"

    severity = await compute_severity(transcript, emotion)
    expected = scenario["expected_severity"]
    if isinstance(expected, list):
        assert severity in expected, f"Got {severity}, expected one of {expected} for {scenario['_file']}"
    else:
        assert severity == expected


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if "expected_intent" in s], ids=lambda s: s["_file"])
@pytest.mark.asyncio
async def test_dispatch_matches_expected(scenario):
    """Responder should match expected for each triage scenario."""
    transcript = scenario["transcript"]
    emotion = "fear" if "critical" in scenario.get("expected_severity", []) else "neutral"

    severity = await compute_severity(transcript, emotion)
    responder = await select_responder(scenario["expected_intent"], severity)

    expected = scenario["expected_responder"]
    if isinstance(expected, list):
        assert responder in expected, f"Got {responder}, expected one of {expected}"
    else:
        assert responder == expected


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if "expected_logistics_trigger" in s], ids=lambda s: s["_file"])
@pytest.mark.asyncio
async def test_logistics_trigger_matches_expected(scenario):
    """Logistics pipeline trigger decision should match scenario expectation."""
    transcript = scenario["transcript"]
    emotion = "fear" if "critical" in scenario.get("expected_severity", []) else "neutral"

    severity = await compute_severity(transcript, emotion)
    intent = scenario.get("expected_intent", "UNKNOWN").upper()

    should_trigger = should_trigger_logistics(severity, intent)
    expected = scenario["expected_logistics_trigger"]

    assert should_trigger == expected, f"Logistics trigger: got {should_trigger}, expected {expected} for {scenario['_file']}"


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if "expected_crisis_type" in s], ids=lambda s: s["_file"])
def test_crisis_type_detection(scenario):
    """Orchestrator should detect the correct crisis type from query."""
    from app.agents.logistics.orchestrator import _CRISIS_TYPES

    query = scenario.get("logistics_query", scenario.get("transcript", "")).lower()
    detected = None
    for keyword, crisis_type in _CRISIS_TYPES.items():
        if keyword in query:
            detected = crisis_type
            break

    assert detected == scenario["expected_crisis_type"], f"Got {detected}, expected {scenario['expected_crisis_type']}"


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if "expected_replan" in s], ids=lambda s: s["_file"])
def test_replan_trigger(scenario):
    """Scenarios with disruptions should trigger replanning."""
    from app.agents.logistics.orchestrator import _should_force_replan

    query = scenario.get("logistics_query", scenario.get("transcript", ""))
    result = _should_force_replan(query)
    assert result == scenario["expected_replan"], f"Replan: got {result}, expected {scenario['expected_replan']}"
