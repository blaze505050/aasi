"""
Tests for Stage 13: Project NETRA Swarm Collision Avoidance Maneuver (CAM) Synthesizer.
========================================================================================
Verifies:
1. Foster-1992 2D Gaussian B-plane collision probability (Pc) integral.
2. Epistemic uncertainty bounds on Pc under covariance scaling.
3. Alfriend-Akella analytical equivalent path integral comparison.
4. Fuel-optimal impulsive CAM synthesis (depressing Pc <= 1e-7 and miss >= 2.5 km).
5. Conjunction dossier evaluation across ISRO presets (RISAT-1B, Cartosat-3, SpaDeX).
6. FastAPI endpoints: POST /api/netra/evaluate and GET /api/netra/presets.
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

from aasi_aero_fno.netra_cam_synthesizer import (
    ProjectNetraEngine,
    FosterCollisionProbabilityEngine,
    NetraCamOptimizer,
    NETRA_SCENARIO_PRESETS,
)
from backend.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_foster_pc_near_and_far_conjunctions():
    """Verifies that Foster Pc calculation scales properly with miss distance."""
    # Near direct collision: miss distance 25 meters, sigma ~ 50 meters
    pc_near, pc_min, pc_max = FosterCollisionProbabilityEngine.compute_foster_pc(
        miss_xi=15.0,
        miss_zeta=20.0,
        sigma_xi=40.0,
        sigma_zeta=60.0,
        rho=0.1,
        r_hbr=4.5,
    )
    assert pc_near > 1e-4
    assert pc_min <= pc_near <= pc_max

    # Far encounter: miss distance 5000 meters
    pc_far, _, _ = FosterCollisionProbabilityEngine.compute_foster_pc(
        miss_xi=3000.0,
        miss_zeta=4000.0,
        sigma_xi=40.0,
        sigma_zeta=60.0,
        rho=0.1,
        r_hbr=4.5,
    )
    assert pc_far < 1e-12


def test_alfriend_akella_pc_consistency():
    """Verifies that Alfriend-Akella fast integral yields consistent order of magnitude."""
    pc_foster, _, _ = FosterCollisionProbabilityEngine.compute_foster_pc(
        miss_xi=50.0,
        miss_zeta=80.0,
        sigma_xi=40.0,
        sigma_zeta=70.0,
        r_hbr=5.0,
    )
    pc_alf = FosterCollisionProbabilityEngine.compute_alfriend_akella_pc(
        miss_xi=50.0,
        miss_zeta=80.0,
        sigma_xi=40.0,
        sigma_zeta=70.0,
        r_hbr=5.0,
    )
    assert pc_foster > 0.0
    assert pc_alf > 0.0
    # Both methods should predict the same risk tier (e.g. within factor of 3)
    ratio = pc_foster / max(pc_alf, 1e-12)
    assert 0.2 < ratio < 5.0


def test_netra_cam_optimizer():
    """Verifies that CAM optimizer calculates optimal Delta-V that depresses Pc below 1e-7."""
    opt_burn, alts = NetraCamOptimizer.optimize_cam(
        current_miss_m=84.0,
        tca_seconds=14.2 * 3600.0,
        primary_mass_kg=1150.0,
        target_clearance_m=3000.0,
    )

    assert opt_burn.burn_direction == "PROGRADE"
    assert 0.04 <= opt_burn.delta_v_magnitude_mps <= 2.5
    assert opt_burn.post_burn_foster_pc <= 1e-7
    assert opt_burn.post_burn_miss_distance_m >= 3000.0
    assert opt_burn.propellant_consumed_kg > 0.0
    assert len(alts) == 2  # Retrograde and cross-track


def test_evaluate_netra_conjunction_presets():
    """Verifies complete conjunction dossier evaluation for ISRO satellite presets."""
    for preset_key in ["RISAT1B_FENGYUN", "CARTOSAT3_COSMOS2251", "SPADEX_ROCKET_STAGE"]:
        dossier = ProjectNetraEngine.evaluate_conjunction_and_synthesize_cam(preset_key)
        assert dossier.conjunction_id.startswith("NETRA-CONJ-")
        assert dossier.encounter.alert_level in ["RED", "YELLOW", "GREEN"]
        assert dossier.recommended_cam.post_burn_foster_pc <= 1e-7
        assert dossier.recommended_cam.post_burn_miss_distance_m >= 2500.0
        assert dossier.merkle_provenance_hash is not None


def test_api_netra_evaluate(test_client):
    """Verifies POST /api/netra/evaluate endpoint returns complete CAM mitigation telemetry."""
    payload = {
        "preset_key": "RISAT1B_FENGYUN",
        "target_clearance_m": 3500.0,
    }
    response = test_client.post("/api/netra/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["primary_asset_name"].startswith("ISRO RISAT-1B")
    assert "debris_object" in data
    assert "encounter" in data
    assert data["encounter"]["foster_pc"] > 1e-6
    assert "recommended_cam" in data
    assert data["recommended_cam"]["post_burn_foster_pc"] <= 1e-7
    assert data["recommended_cam"]["post_burn_miss_distance_m"] >= 3500.0
    assert data["isro_safety_clearance"] in ["CAM_DISPATCH_MANDATED", "ADVISORY_MONITOR"]


def test_api_netra_presets(test_client):
    """Verifies GET /api/netra/presets returns active ISRO conjunction presets."""
    response = test_client.get("/api/netra/presets")
    assert response.status_code == 200
    presets = response.json()

    assert "RISAT1B_FENGYUN" in presets
    assert "CARTOSAT3_COSMOS2251" in presets
    assert "SPADEX_ROCKET_STAGE" in presets
    assert "GSAT24_GEO_DEBRIS" in presets
