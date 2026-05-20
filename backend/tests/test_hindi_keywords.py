"""Tests for Hindi/Hinglish emergency keyword recognition."""
import pytest
from app.services.severity_service import compute_severity


class TestHindiKeywords:
    @pytest.mark.asyncio
    async def test_aag_fire(self):
        severity = await compute_severity("bahut badi aag lagi hai", "fear")
        assert severity in ("high", "critical")

    @pytest.mark.asyncio
    async def test_baadh_flood(self):
        severity = await compute_severity("bahut badi baadh aa gayi hai", "fear")
        assert severity in ("high", "critical")

    @pytest.mark.asyncio
    async def test_bhookamp_earthquake(self):
        severity = await compute_severity("bhookamp aa gaya bahut tez", "fear")
        assert severity in ("high", "critical")

    @pytest.mark.asyncio
    async def test_goli_shot(self):
        severity = await compute_severity("kisi ne goli maar di", "fear")
        assert severity == "critical"

    @pytest.mark.asyncio
    async def test_madad_help(self):
        severity = await compute_severity("madad chahiye please", "neutral")
        assert severity == "medium"

    @pytest.mark.asyncio
    async def test_mixed_hindi_english(self):
        severity = await compute_severity("yahan pe fire lag gayi hai madad bhejo", "fear")
        assert severity in ("high", "critical")

    @pytest.mark.asyncio
    async def test_hadsa_accident(self):
        severity = await compute_severity("bada hadsa ho gaya highway pe", "fear")
        assert severity in ("high", "critical")
