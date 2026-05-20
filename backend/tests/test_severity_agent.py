"""Async unit tests for the hybrid SeverityAgent.

Verifies:
- Hybrid formula output and weight distribution
- Level classification thresholds
- Critical keyword short-circuit
- Keyword scoring ranges
"""

from __future__ import annotations

import pytest

from app.agents.severity.severity_agent import (
    SeverityAgent,
    _keyword_score,
    _severity_level,
)
from app.core.schemas import ReasoningOutput, SeverityLevel
from app.core.schemas.severity import SeverityAssessment


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_reasoning(
    risk_factors: list[str] | None = None,
    context: str = "Caller needs assistance",
    confidence: float = 0.9,
    emotion_intensity: float = 0.7,
    intent: str = "UNKNOWN",
    keyword_text: str = "",
) -> ReasoningOutput:
    return ReasoningOutput(
        key_insights=["insight"],
        risk_factors=risk_factors or [],
        context_summary=context,
        confidence=confidence,
        metadata={
            "transcript": keyword_text or context,
            "intent": intent,
            "emotion_intensity": emotion_intensity,
            "reasoning_score": confidence,
        },
    )


# ---------------------------------------------------------------------------
# Pure function tests
# ---------------------------------------------------------------------------


class TestKeywordScore:
    def test_high_keyword(self):
        score = _keyword_score("there is a fire and burning car")
        assert score >= 0.5

    def test_critical_keywords(self):
        score = _keyword_score("active shooter on site")
        assert score >= 0.9

    def test_medium_keyword(self):
        score = _keyword_score("minor accident with injury")
        assert score >= 0.4

    def test_no_match_returns_zero(self):
        score = _keyword_score("hello how are you")
        assert score == 0.0

    def test_empty_text_returns_zero(self):
        score = _keyword_score("")
        assert score == 0.0


class TestSeverityLevel:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.90, SeverityLevel.CRITICAL),
            (0.85, SeverityLevel.CRITICAL),
            (0.70, SeverityLevel.HIGH),
            (0.65, SeverityLevel.HIGH),
            (0.50, SeverityLevel.MEDIUM),
            (0.40, SeverityLevel.MEDIUM),
            (0.30, SeverityLevel.LOW),
            (0.00, SeverityLevel.LOW),
        ],
    )
    def test_threshold_mapping(self, score: float, expected: SeverityLevel):
        assert _severity_level(score) == expected


# ---------------------------------------------------------------------------
# Integration tests – SeverityAgent
# ---------------------------------------------------------------------------


class TestSeverityAgentHybridFormula:
    @pytest.mark.asyncio
    async def test_returns_severity_assessment(self):
        agent = SeverityAgent()
        reasoning = _make_reasoning(
            keyword_text="help fire shooting",
            emotion_intensity=0.8,
            intent="FIRE",
        )
        result = await agent.process(reasoning)
        assert isinstance(result, SeverityAssessment)

    @pytest.mark.asyncio
    async def test_high_intensity_emotion_increases_score(self):
        agent = SeverityAgent()
        low_em = _make_reasoning(keyword_text="accident", emotion_intensity=0.1, intent="ACCIDENT")
        high_em = _make_reasoning(keyword_text="accident", emotion_intensity=0.9, intent="ACCIDENT")

        low_result = await agent.process(low_em)
        high_result = await agent.process(high_em)

        assert high_result.score > low_result.score

    @pytest.mark.asyncio
    async def test_critical_keyword_drives_critical_level(self):
        agent = SeverityAgent()
        reasoning = _make_reasoning(
            keyword_text="patient is not breathing cardiac arrest",
            emotion_intensity=0.5,
            intent="MEDICAL",
        )
        result = await agent.process(reasoning)
        assert result.level == SeverityLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_factors_dict_contains_all_components(self):
        agent = SeverityAgent()
        reasoning = _make_reasoning(keyword_text="injury accident", intent="ACCIDENT")
        result = await agent.process(reasoning)
        assert "keyword_score" in result.factors
        assert "emotion_intensity" in result.factors
        assert "reasoning_score" in result.factors
        assert "intent_score" in result.factors

    @pytest.mark.asyncio
    async def test_score_clamped_0_to_1(self):
        agent = SeverityAgent()
        reasoning = _make_reasoning(
            risk_factors=["violence", "weapon"],
            keyword_text="not breathing cardiac arrest active shooter bomb",
            emotion_intensity=1.0,
            intent="VIOLENT_CRIME",
        )
        result = await agent.process(reasoning)
        assert 0.0 <= result.score <= 1.0

    @pytest.mark.asyncio
    async def test_low_risk_produces_low_or_medium_level(self):
        agent = SeverityAgent()
        reasoning = _make_reasoning(
            keyword_text="lost my cat in the parking lot",
            emotion_intensity=0.1,
            intent="NON_EMERGENCY",
        )
        result = await agent.process(reasoning)
        assert result.level in {SeverityLevel.LOW, SeverityLevel.MEDIUM}


class TestSeverityAgentReasoningText:
    @pytest.mark.asyncio
    async def test_reasoning_text_includes_formula(self):
        agent = SeverityAgent()
        reasoning = _make_reasoning(keyword_text="help fire", intent="FIRE")
        result = await agent.process(reasoning)
        assert "0.5*" in result.reasoning
        assert "0.25*" in result.reasoning
