"""
Unit and Integration Tests for Stage 24: Neuromorphic Event-Camera SSA & Orbit Determination.
============================================================================================
Tests asynchronous microsecond DVS event generation, spacetime Hough streak extraction,
Angles-Only Gauss-Laplace Initial Orbit Determination (IOD), microsecond covariance collapse,
and FastAPI REST endpoints.
"""

import math
import numpy as np
import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.neuromorphic_ssa import (
    NeuromorphicSSAEngine,
    NeuromorphicSSANavigator,
    SSAOrbitRegime,
    SSA_PRESETS,
)
from backend.main import app

client = TestClient(app)


def test_dvs_event_stream_simulation():
    """Verifies that asynchronous DVS events are generated with microsecond timestamps and valid polarities."""
    events = NeuromorphicSSAEngine.simulate_dvs_events(num_streaks=3, duration_ms=100.0, noise_events=100)

    assert len(events) >= 200, "Should generate events for 3 streaks plus background Poisson noise"

    for ev in events[:50]:
        assert 0 <= ev.pixel_x < 1280
        assert 0 <= ev.pixel_y < 720
        assert 0 <= ev.timestamp_us <= 100000
        assert ev.polarity in (-1, 1)

    # Monotonic timestamps verification
    timestamps = [e.timestamp_us for e in events]
    assert timestamps == sorted(timestamps), "Event stream must be strictly time-ordered"


def test_angles_only_iod_leo_and_geo():
    """Verifies Gauss Angles-Only Initial Orbit Determination for LEO and GEO regimes."""
    # 1. LEO regime
    sma_leo, ecc_leo, inc_leo, pc_leo = NeuromorphicSSAEngine.angles_only_gauss_iod(
        rel_vel_km_s=11.4,
        range_km=48.0,
        regime=SSAOrbitRegime.LEO,
    )
    assert 6800.0 < sma_leo < 7300.0, f"LEO semi-major axis {sma_leo} km outside expected range"
    assert 0.001 <= ecc_leo < 0.15, f"LEO eccentricity {ecc_leo} outside expected range"
    assert pc_leo > 0.0

    # 2. GEO regime (r ~ 42164 km)
    sma_geo, ecc_geo, inc_geo, pc_geo = NeuromorphicSSAEngine.angles_only_gauss_iod(
        rel_vel_km_s=3.8,
        range_km=350.0,
        regime=SSAOrbitRegime.GEO,
    )
    assert 42100.0 < sma_geo < 42250.0, f"GEO semi-major axis {sma_geo} km outside expected range"
    assert ecc_geo < 0.05


def test_neuromorphic_ssa_dossier():
    """Verifies complete SSA tracking dossier generation with sub-15m position covariance."""
    dossier = NeuromorphicSSANavigator.execute_ssa_tracking("LEO_STARLINK_CONSTELLATION_DEBRIS")

    assert "Megaconstellation" in dossier.tracking_scenario
    assert len(dossier.debris_objects_detected) == 3
    assert len(dossier.spatio_temporal_streaks) == 3
    assert dossier.temporal_resolution_us == 1.0
    assert dossier.total_events_processed > 200

    for obj in dossier.debris_objects_detected:
        assert obj.estimated_diameter_cm > 0.0
        assert obj.relative_velocity_km_s > 0.0
        # Microsecond timing collapses covariance to sub-15m
        assert obj.covariance_pos_1sigma_m < 15.0
        assert obj.covariance_vel_1sigma_mps < 0.1

    assert len(dossier.provenance_hash) == 64


def test_ssa_api_endpoints():
    """Tests FastAPI REST endpoints for Stage 24."""
    # 1. Presets endpoint
    resp_pre = client.get("/api/v1/ssa/presets")
    assert resp_pre.status_code == 200
    presets = resp_pre.json()
    assert "LEO_STARLINK_CONSTELLATION_DEBRIS" in presets
    assert "ISRO_NETRA_OPTICAL_DVS_ORBIT" in presets

    # 2. Track endpoint
    payload = {"preset_key": "LEO_STARLINK_CONSTELLATION_DEBRIS"}
    resp_trk = client.post("/api/v1/ssa/track", json=payload)
    assert resp_trk.status_code == 200
    data = resp_trk.json()
    assert len(data["debris_objects_detected"]) == 3
    assert len(data["spatio_temporal_streaks"]) == 3
    assert data["sensor_power_mw"] < 25.0  # Ultra-low power neuromorphic sensor
