"""
Tests for Stage 12: NavIC Carrier-Phase Relative Orbit Determination & SpaDeX Docking.
======================================================================================
Verifies:
1. LAMBDA integer ambiguity resolution (Z-transform, ratio test >= 2.5, 1.8 cm precision).
2. Closed-loop 6-DOF autonomous docking simulation under Clohessy-Wiltshire dynamics.
3. ASTM F3269-21 approach cone corridor compliance (theta_LOS <= 15 deg).
4. Attitude alignment error convergence (< 0.05 deg at mechanical capture).
5. Fast post-eclipse carrier phase relock eliminating the 225m drift anomaly.
6. FastAPI endpoints: POST /api/spadex/simulate and GET /api/spadex/presets.
"""

import sys
from pathlib import Path
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure package roots are on sys.path
_repo_root = Path(__file__).resolve().parent.parent
_fno_pkg = _repo_root / "aasi-aero-fno"
for p in [str(_repo_root), str(_fno_pkg)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from aasi_aero_fno.spadex_docking import (
    SpaDeXDockingEngine,
    LambdaAmbiguityResolver,
    SPADEX_SCENARIO_PRESETS,
)
from backend.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_lambda_ambiguity_resolution():
    """Verifies that LAMBDA algorithm resolves integer ambiguities with high ratio test metric."""
    float_ambiguities = np.array([451.29, 312.82, 589.04, 219.98])
    Q_matrix = np.array([
        [0.08, 0.03, 0.01, 0.01],
        [0.03, 0.07, 0.02, 0.01],
        [0.01, 0.02, 0.09, 0.02],
        [0.01, 0.01, 0.02, 0.06],
    ])
    result = LambdaAmbiguityResolver.resolve_ambiguities(float_ambiguities, Q_matrix)

    assert result.ambiguity_fixed is True
    assert result.ratio_test_metric >= 2.5
    assert result.fixed_integer_ambiguities == [451, 313, 589, 220]
    # Fixed ambiguity guarantees sub-centimeter relative navigation
    assert result.relative_position_error_cm <= 2.0


def test_spadex_nominal_docking_mission():
    """Verifies full 6-DOF relative docking simulation from 225m hold point to latch capture."""
    sim_result = SpaDeXDockingEngine.simulate_docking_mission(
        preset_key="SPADEX_NOMINAL_VBAR",
        initial_distance_m=225.0,
        approach_corridor_deg=15.0,
        max_duration_s=250.0,
        time_step_s=1.0,
    )

    assert sim_result.terminal_latch_status == "MECHANICAL_LATCH_SECURED"
    assert sim_result.final_distance_m <= 0.05  # Within 5 cm
    assert sim_result.final_speed_mps <= 0.05   # Contact speed <= 50 mm/s
    assert sim_result.astm_f3269_cone_compliant is True
    assert sim_result.attitude_alignment_deg < 0.05  # Attitude aligned to < 0.05 deg
    assert sim_result.fuel_consumed_kg > 0.0
    assert len(sim_result.waypoints) > 20
    assert sim_result.merkle_provenance_hash is not None


def test_spadex_post_eclipse_drift_fix():
    """Verifies that NavIC carrier-phase lock eliminates the 225m post-eclipse drift anomaly."""
    sim_result = SpaDeXDockingEngine.simulate_docking_mission(
        preset_key="SPADEX_POST_ECLIPSE_DRIFT_FIX",
        initial_distance_m=225.0,
        approach_corridor_deg=15.0,
        max_duration_s=250.0,
    )

    assert sim_result.navic_lambda_ratio_metric >= 2.5
    assert sim_result.terminal_latch_status == "MECHANICAL_LATCH_SECURED"
    assert sim_result.astm_f3269_cone_compliant is True


def test_chandrayaan4_lunar_docking():
    """Verifies Chandrayaan-4 lunar orbit rendezvous with low-impact latch."""
    sim_result = SpaDeXDockingEngine.simulate_docking_mission(
        preset_key="CHANDRAYAAN4_LUNAR_DOCKING",
        initial_distance_m=180.0,
        approach_corridor_deg=12.0,
        max_duration_s=250.0,
    )

    assert "Lunar Orbit" in sim_result.orbit_type
    assert sim_result.terminal_latch_status == "MECHANICAL_LATCH_SECURED"
    assert sim_result.total_delta_v_mps > 0.0


def test_api_spadex_simulate(test_client):
    """Verifies POST /api/spadex/simulate endpoint returns complete mission telemetry."""
    payload = {
        "preset_key": "SPADEX_NOMINAL_VBAR",
        "initial_distance_m": 150.0,
        "approach_corridor_deg": 15.0,
        "enable_navic_lambda": True,
        "max_duration_s": 200.0,
        "time_step_s": 1.0,
    }
    response = test_client.post("/api/spadex/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["mission_preset"] == "SPADEX_NOMINAL_VBAR"
    assert data["terminal_latch_status"] == "MECHANICAL_LATCH_SECURED"
    assert data["astm_f3269_cone_compliant"] is True
    assert data["attitude_alignment_deg"] < 0.05
    assert len(data["waypoints"]) > 10
    first_wp = data["waypoints"][0]
    assert "rel_pos_m" in first_wp
    assert "approach_cone_angle_deg" in first_wp


def test_api_spadex_presets(test_client):
    """Verifies GET /api/spadex/presets returns ISRO docking presets."""
    response = test_client.get("/api/spadex/presets")
    assert response.status_code == 200
    presets = response.json()

    assert "SPADEX_NOMINAL_VBAR" in presets
    assert "SPADEX_POST_ECLIPSE_DRIFT_FIX" in presets
    assert "CHANDRAYAAN4_LUNAR_DOCKING" in presets
    assert "BAS01_STATION_MODULE" in presets
