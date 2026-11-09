"""
Stage 37 Verification Test Suite: Push-Button FAA Part 23/25 & DGCA Airworthiness Dossier Synthesizer
======================================================================================================
Tests:
1. 14 CFR § 25.335 Design Airspeeds: V_S, V_A, V_C, V_D, V_F.
2. 14 CFR § 25.341 Pratt Discrete 1-Cosine Gust Loads & Alleviation Factor.
3. RTM Regulatory Compliance Matrix and Cryptographic Certification Digest.
4. FastAPI Endpoints for Stage 37.
"""

import pytest
import math
from fastapi.testclient import TestClient
from aasi_aero_fno.airworthiness_certification_dossier import (
    AirworthinessDossierEngine,
    RegulatoryAuthority,
    MeansOfCompliance,
)
from backend.main import app


def test_isa_density_and_design_airspeeds():
    engine = AirworthinessDossierEngine()

    # ISA density checks
    rho_sl = engine.get_isa_density(0.0)
    assert math.isclose(rho_sl, 1.225, rel_tol=1e-3)
    rho_3k = engine.get_isa_density(3000.0)
    assert 0.85 < rho_3k < 0.95

    # Aircraft: 45,000 kg transport category, S = 122.4 m^2
    speeds = engine.compute_design_airspeeds(
        gross_weight_kg=45000.0,
        wing_area_m2=122.4,
        cl_max_clean=1.45,
        cl_max_flaps=2.20,
        altitude_m=3000.0,
    )

    # 1. Stall speed in clean configuration > stall speed in flaps
    assert speeds.v_stall_clean_mps > speeds.v_stall_flaps_mps
    assert 60.0 <= speeds.v_stall_clean_mps <= 85.0  # ~130 knots

    # 2. FAR 25 limit load factor for 45,000 kg (~99,200 lbs)
    # n_calc = 2.1 + 24000 / (99200 + 10000) = 2.1 + 0.22 = 2.32 -> clamped to 2.5 min
    assert speeds.n_max_maneuver >= 2.5

    # 3. Maneuvering speed V_A = V_S * sqrt(n_max)
    expected_va = speeds.v_stall_clean_mps * math.sqrt(speeds.n_max_maneuver)
    assert math.isclose(speeds.v_maneuver_va_mps, expected_va, rel_tol=1e-3)

    # 4. FAR 25.335(b): V_D >= 1.25 * V_C
    assert speeds.v_dive_vd_mps >= 1.25 * speeds.v_cruise_vc_mps
    assert speeds.v_dive_vd_knots > speeds.v_cruise_vc_knots

    # 5. FAR 25.335(e): Flap design speed V_F >= 1.6 * V_SF
    assert speeds.v_flap_vf_mps >= 1.6 * speeds.v_stall_flaps_mps


def test_pratt_gust_load_factors_and_alleviation():
    engine = AirworthinessDossierEngine()

    gust = engine.compute_pratt_gust_load_analysis(
        gross_weight_kg=45000.0,
        wing_area_m2=122.4,
        mean_aerodynamic_chord_m=4.15,
        cl_alpha_per_rad=5.25,
        v_cruise_mps=180.0,
        altitude_m=3000.0,
    )

    # 1. Wing loading W/S = mg/S
    expected_ws = (45000.0 * 9.80665) / 122.4
    assert math.isclose(gust.wing_loading_n_m2, expected_ws, rel_tol=1e-3)

    # 2. Alleviation factor K_g in valid physical range (0.6 - 0.95 for transport jets)
    assert 0.60 <= gust.gust_alleviation_factor_kg <= 0.95

    # 3. Gust load increment delta_n > 0
    assert gust.gust_load_increment_delta_n > 0.0

    # 4. Limit gust load factors
    assert math.isclose(gust.limit_gust_load_pos, 1.0 + gust.gust_load_increment_delta_n, rel_tol=1e-3)
    assert math.isclose(gust.limit_gust_load_neg, 1.0 - gust.gust_load_increment_delta_n, rel_tol=1e-3)

    # 5. Positive limit gust load should be >= 2.0g and <= 3.8g
    assert 2.0 <= gust.limit_gust_load_pos <= 3.8

    # 6. Ultimate load factor must have 1.5x safety factor
    assert gust.ultimate_load_factor >= 1.5 * gust.limit_gust_load_pos
    assert gust.structural_reserve_margin > 0.0


def test_full_airworthiness_dossier_synthesis():
    engine = AirworthinessDossierEngine()

    dossier = engine.synthesize_dossier(
        aircraft_name="AeroCraft-X40 Sovereign Transport",
        tail_number="VT-AASI-001",
        gross_weight_kg=45000.0,
        wing_area_m2=122.4,
        mean_aerodynamic_chord_m=4.15,
        cl_max_clean=1.45,
        cl_max_flaps=2.20,
        cl_alpha_per_rad=5.25,
        cruise_altitude_m=9500.0,
        authority=RegulatoryAuthority.FAA_PART_25,
    )

    assert dossier["status"] == "APPROVED_FOR_CONFORMITY_INSPECTION"
    assert dossier["dossier_id"].startswith("CERT-FAA_PART_25")
    assert len(dossier["certification_digest_sha256"]) == 64

    # Compliance summary
    comp = dossier["compliance_summary"]
    assert comp["total_requirements"] >= 7
    assert comp["compliance_percentage"] == 100.0
    assert comp["moc_distribution"]["MOC_2_Numerical_Simulation"] >= 4

    # RTM check
    rtm = dossier["requirement_traceability_matrix"]
    req_ids = [item["req_id"] for item in rtm]
    assert "FAR-25.335" in req_ids
    assert "FAR-25.341" in req_ids
    assert "FAR-25.571" in req_ids
    assert "FAR-25.1309" in req_ids

    # Chief engineer seal
    assert "DER-AERO-CRYPTO" in dossier["airworthiness_declaration"]["chief_engineer_seal"]


def test_airworthiness_api_endpoints():
    client = TestClient(app)

    # 1. Airspeeds endpoint
    res_speed = client.post(
        "/api/v1/airworthiness/airspeeds",
        json={
            "gross_weight_kg": 45000.0,
            "wing_area_m2": 122.4,
            "cl_max_clean": 1.45,
            "cl_max_flaps": 2.20,
            "altitude_m": 3000.0,
        },
    )
    assert res_speed.status_code == 200
    data_speed = res_speed.json()["data"]
    assert "v_dive_vd_knots" in data_speed
    assert data_speed["v_dive_vd_mps"] >= 1.25 * data_speed["v_cruise_vc_mps"]

    # 2. Pratt gust endpoint
    res_gust = client.post(
        "/api/v1/airworthiness/pratt-gust",
        json={
            "gross_weight_kg": 45000.0,
            "wing_area_m2": 122.4,
            "mean_aerodynamic_chord_m": 4.15,
            "cl_alpha_per_rad": 5.25,
            "v_cruise_mps": 180.0,
            "altitude_m": 3000.0,
        },
    )
    assert res_gust.status_code == 200
    data_gust = res_gust.json()["data"]
    assert "gust_alleviation_factor_kg" in data_gust
    assert data_gust["limit_gust_load_pos"] > 1.0

    # 3. Synthesize dossier endpoint
    res_dossier = client.post(
        "/api/v1/airworthiness/synthesize-dossier",
        json={
            "aircraft_name": "AeroCraft-X40 Sovereign Transport",
            "tail_number": "VT-AASI-001",
            "gross_weight_kg": 45000.0,
            "wing_area_m2": 122.4,
            "mean_aerodynamic_chord_m": 4.15,
            "cl_max_clean": 1.45,
            "cl_max_flaps": 2.20,
            "cl_alpha_per_rad": 5.25,
            "cruise_altitude_m": 9500.0,
            "authority_key": "FAA_PART_25",
        },
    )
    assert res_dossier.status_code == 200
    data_dossier = res_dossier.json()["data"]
    assert data_dossier["status"] == "APPROVED_FOR_CONFORMITY_INSPECTION"
    assert "certification_digest_sha256" in data_dossier
