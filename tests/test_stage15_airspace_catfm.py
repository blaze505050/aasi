"""
Test Suite for Stage 15: Sovereign Airspace 4D Trajectory Negotiation Engine (AAI C-ATFM).
==========================================================================================
Validates:
1. Haversine distance calculation and great-circle waypoint interpolation.
2. ICAO wake vortex separation spacing enforcement across aircraft wake classes (Heavy, Medium, Light/eVTOL).
3. Controlled Time of Arrival (CTA) slot optimizer resolving runway arrival bank congestion.
4. Convective monsoon weather storm cell detection and fuel-optimal dogleg avoidance rerouting.
5. FastAPI integration endpoints (/api/catfm/presets, /api/catfm/negotiate).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from aasi_aero_fno.airspace_catfm import (
    SovereignCatfmEngine,
    ConvectiveWeatherCell,
    CATFM_SCENARIO_PRESETS,
    INDIAN_AIRPORTS,
    WAKE_SEPARATION_MINIMA_NM,
)

client = TestClient(app)


def test_haversine_and_interpolation():
    """Validates great-circle distance calculation between Delhi (VIDP) and Mumbai (VABB)."""
    delhi = INDIAN_AIRPORTS["VIDP"]
    mumbai = INDIAN_AIRPORTS["VABB"]

    dist_km = SovereignCatfmEngine.haversine_distance_km(
        delhi["lat"], delhi["lon"], mumbai["lat"], mumbai["lon"]
    )
    # True Delhi-Mumbai great-circle distance is approx 1140-1160 km
    assert 1100.0 < dist_km < 1200.0, f"Expected Delhi-Mumbai distance ~1150 km, got {dist_km}"

    # Halfway interpolation
    mid_lat, mid_lon = SovereignCatfmEngine.interpolate_coordinates(
        delhi["lat"], delhi["lon"], mumbai["lat"], mumbai["lon"], 0.5
    )
    assert 22.0 < mid_lat < 25.0
    assert 74.0 < mid_lon < 76.0


def test_wake_vortex_separation_minima_matrix():
    """Validates ICAO wake vortex separation standards between Super/Heavy/Medium/Light aircraft."""
    # Heavy leading Medium must have at least 5.0 NM separation
    assert WAKE_SEPARATION_MINIMA_NM["HEAVY"]["MEDIUM"] >= 5.0
    # Medium leading Light must have at least 4.0 NM separation
    assert WAKE_SEPARATION_MINIMA_NM["MEDIUM"]["LIGHT"] >= 4.0


def test_convective_weather_collision_detection():
    """Validates hazard detection inside a convective storm cell radius."""
    storm = ConvectiveWeatherCell(
        cell_id="TEST_STORM",
        center_lat=14.0,
        center_lon=76.0,
        radius_km=30.0,
        top_altitude_ft=40000.0,
        severity="SEVERE",
    )

    # Position inside radius (10 km away)
    hit = SovereignCatfmEngine.check_weather_collision(14.05, 76.05, [storm])
    assert hit is not None
    assert hit.cell_id == "TEST_STORM"

    # Position outside radius (150 km away)
    miss = SovereignCatfmEngine.check_weather_collision(15.5, 76.0, [storm])
    assert miss is None


def test_cta_optimization_resolves_runway_congestion():
    """Validates that CTA optimization resolves arrival wake conflicts and prevents holding stack fuel waste."""
    # 1. Unoptimized run (CTA optimization OFF)
    res_unoptimized = SovereignCatfmEngine.negotiate_airspace_scenario(
        scenario_key="BENGALURU_VOBL_MONSOON_RUSH",
        enable_cta_optimization=False,
        enable_weather_avoidance=False,
    )
    assert res_unoptimized.residual_conflicts > 0, "Unoptimized rush bank must yield wake conflicts"
    assert res_unoptimized.catfm_efficiency_index_pct < 95.0

    # 2. Optimized run (AAI C-ATFM CTA optimization ON)
    res_optimized = SovereignCatfmEngine.negotiate_airspace_scenario(
        scenario_key="BENGALURU_VOBL_MONSOON_RUSH",
        enable_cta_optimization=True,
        enable_weather_avoidance=True,
    )
    assert res_optimized.residual_conflicts == 0, "CTA optimization must eliminate all wake conflicts"
    assert res_optimized.resolved_conflicts > 0, "Conflicts should be successfully metered and resolved"
    assert res_optimized.weather_reroutes_executed > 0, "Monsoon squall cell should trigger avoidance reroute"
    assert res_optimized.catfm_efficiency_index_pct >= 90.0
    assert len(res_optimized.merkle_provenance_hash) == 64


def test_mumbai_single_runway_crunch_scenario():
    """Validates Mumbai single-runway peak arrival metering including BKC AAM vertiport flight."""
    res = SovereignCatfmEngine.negotiate_airspace_scenario(
        scenario_key="MUMBAI_VABB_SINGLE_RUNWAY_CRUNCH",
        enable_cta_optimization=True,
        enable_weather_avoidance=False,
    )
    assert res.total_flights == 4
    assert res.residual_conflicts == 0
    # Every flight must have an allocated conflict-free CTA
    for flt in res.flights:
        assert flt.negotiated_cta_s >= flt.original_eta_s
        assert len(flt.trajectory_points) == 35


def test_api_catfm_routes():
    """Validates FastAPI /api/catfm/presets and /api/catfm/negotiate endpoints."""
    # Presets
    res_presets = client.get("/api/catfm/presets")
    assert res_presets.status_code == 200
    presets_data = res_presets.json()
    assert "presets" in presets_data
    assert "airports" in presets_data
    assert "VOBL" in presets_data["airports"]
    assert "VIDP" in presets_data["airports"]

    # Negotiation POST
    payload = {
        "scenario_key": "DELHI_VIDP_WINTER_FOG_GDP",
        "enable_cta_optimization": True,
        "enable_weather_avoidance": False,
        "time_compression": 1.0,
    }
    res_neg = client.post("/api/catfm/negotiate", json=payload)
    assert res_neg.status_code == 200
    neg_data = res_neg.json()
    assert neg_data["destination_hub"] == "VIDP"
    assert neg_data["total_flights"] == 3
    assert neg_data["residual_conflicts"] == 0
    assert neg_data["regulatory_standard"] == "AAI_CATFM_ICAO_DOC_9971_COMPLIANT"
    assert len(neg_data["flights"]) == 3

