"""Tests for route_tool — haversine, city resolution, airport/port data."""
import pytest


class TestHaversine:
    def test_same_point_is_zero(self):
        from app.services.logistics.tools.route_tool import _haversine_km
        assert _haversine_km(20.0, 85.0, 20.0, 85.0) == 0.0

    def test_bhubaneswar_to_kolkata(self):
        from app.services.logistics.tools.route_tool import _haversine_km
        dist = _haversine_km(20.2961, 85.8245, 22.5726, 88.3639)
        assert 350 < dist < 500

    def test_delhi_to_mumbai(self):
        from app.services.logistics.tools.route_tool import _haversine_km
        dist = _haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
        assert 1100 < dist < 1400


class TestResolveCity:
    def test_known_city(self):
        from app.services.logistics.tools.route_tool import _resolve_city
        coords = _resolve_city("Bhubaneswar")
        assert coords is not None
        lat, lon = coords
        assert 20.0 < lat < 21.0
        assert 85.0 < lon < 86.5

    def test_unknown_city_returns_none(self):
        from app.services.logistics.tools.route_tool import _resolve_city
        assert _resolve_city("Atlantis") is None

    def test_kolkata(self):
        from app.services.logistics.tools.route_tool import _resolve_city
        coords = _resolve_city("Kolkata")
        assert coords is not None


class TestStaticData:
    def test_airports_have_required_fields(self):
        from app.services.logistics.tools.route_tool import AIRPORTS
        assert len(AIRPORTS) >= 19
        for ap in AIRPORTS:
            assert "name" in ap
            assert "code" in ap
            assert "lat" in ap
            assert "lon" in ap
            assert "runway_m" in ap

    def test_ports_have_required_fields(self):
        from app.services.logistics.tools.route_tool import PORTS
        assert len(PORTS) >= 13
        for pt in PORTS:
            assert "name" in pt
            assert "city" in pt
            assert "lat" in pt
            assert "lon" in pt
            assert "capacity_mt_yr" in pt
