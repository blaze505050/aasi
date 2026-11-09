"""
Stage 39 Verification Test Suite: Sustainable Aviation Fuel (SAF) & ICAO CORSIA Carbon Twin
============================================================================================
Tests:
1. ASTM D7566 physical blend properties, LHV energy scaling, and aromatics limit.
2. Non-CO2 climate impacts: soot particulate and contrail radiative forcing reduction.
3. Flight mission fuel burn, net lifecycle CO2 avoidance, and CORSIA credit monetization.
4. FastAPI Endpoints for Stage 39.
"""

import pytest
from fastapi.testclient import TestClient
from aasi_aero_fno.saf_corsia_carbon_twin import (
    SafCorsiaCarbonTwinEngine,
    SafPathway,
    FUEL_DATABASE,
)
from backend.main import app


def test_astm_d7566_blend_and_aromatics():
    engine = SafCorsiaCarbonTwinEngine()

    # 1. 50% HEFA-SPK blend (compliant)
    res_50 = engine.evaluate_blend(SafPathway.HEFA_SPK, 50.0)
    assert res_50.astm_d7566_compliant is True
    assert res_50.compliance_warning is None
    # Higher LHV than Jet A-1 (43.2 MJ/kg) -> positive sfc improvement
    assert res_50.blended_lhv_mj_kg > 43.20
    assert res_50.sfc_improvement_pct > 0.0
    # Aromatic content = 0.5 * 0.5 + 0.5 * 18.5 = 9.5% >= 8.4%
    assert res_50.blended_aromatics_pct >= 8.4
    # Lifecycle CO2 reduction should be > 35% for 50% blend
    assert res_50.co2_lifecycle_reduction_pct > 35.0

    # 2. 70% HEFA-SPK blend (non-compliant: exceeds 50% ASTM limit)
    res_70 = engine.evaluate_blend(SafPathway.HEFA_SPK, 70.0)
    assert res_70.astm_d7566_compliant is False
    assert "exceeds ASTM D7566" in res_70.compliance_warning


def test_non_co2_soot_and_contrail_mitigation():
    engine = SafCorsiaCarbonTwinEngine()

    # 50% PtL e-Kerosene blend
    res_ptl = engine.evaluate_blend(SafPathway.PTL_E_KEROSENE, 50.0)
    assert res_ptl.soot_reduction_pct >= 30.0
    assert res_ptl.contrail_radiative_forcing_reduction_pct >= 25.0


def test_flight_mission_and_corsia_monetization():
    engine = SafCorsiaCarbonTwinEngine()

    mission = engine.simulate_flight_mission(
        flight_distance_km=4000.0,
        aircraft_type="AeroCraft-X40 Sovereign Transport",
        payload_kg=18000.0,
        blend_ratio_saf_pct=50.0,
        saf_pathway=SafPathway.HEFA_SPK,
        carbon_price_usd_per_tonne=48.0,
    )

    # 1. Fuel saved due to higher LHV
    assert mission.saf_blend_fuel_burn_kg < mission.conventional_fuel_burn_kg
    assert mission.fuel_saved_due_to_lhv_kg > 50.0  # At least 50 kg saved

    # 2. Lifecycle CO2 avoidance
    assert mission.saf_lifecycle_co2_tonnes < mission.baseline_lifecycle_co2_tonnes
    assert mission.net_co2_avoided_tonnes > 5.0  # Multi-tonne CO2 savings

    # 3. Monetized credits
    assert mission.corsia_offset_credits_earned == round(mission.net_co2_avoided_tonnes, 3)
    assert mission.monetized_corsia_credit_usd > 200.0

    # 4. Cryptographic seal & certificate
    assert mission.corsia_cef_certificate_id.startswith("CEF-ICAO-")
    assert len(mission.cryptographic_seal_sha256) == 64


def test_saf_carbon_api_endpoints():
    client = TestClient(app)

    # 1. Evaluate blend endpoint
    res_blend = client.post(
        "/api/v1/saf-carbon/evaluate-blend",
        json={
            "saf_pathway_key": "HEFA_SPK",
            "blend_ratio_saf_pct": 50.0,
        },
    )
    assert res_blend.status_code == 200
    data_blend = res_blend.json()["data"]
    assert data_blend["astm_d7566_compliant"] is True
    assert "blended_lhv_mj_kg" in data_blend

    # 2. Simulate mission endpoint
    res_miss = client.post(
        "/api/v1/saf-carbon/simulate-mission",
        json={
            "flight_distance_km": 3500.0,
            "aircraft_type": "AeroCraft-X40 Sovereign Transport",
            "payload_kg": 18000.0,
            "blend_ratio_saf_pct": 50.0,
            "saf_pathway_key": "HEFA_SPK",
            "carbon_price_usd_per_tonne": 48.0,
        },
    )
    assert res_miss.status_code == 200
    data_miss = res_miss.json()["data"]
    assert "corsia_cef_certificate_id" in data_miss
    assert data_miss["monetized_corsia_credit_usd"] > 0.0
