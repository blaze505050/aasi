"""
Stage 40 Verification Test Suite: Turbofan Remaining Useful Life (RUL) & Fleet Health Digital Twin
===================================================================================================
Epoch VIII Capstone Tests:
1. Paris-Erdogan low-cycle fatigue (LCF) crack propagation physics & critical crack check.
2. NASA C-MAPSS EGT margin erosion and isentropic efficiency loss.
3. Two-parameter Weibull reliability R(t), hazard rate h(t), and RUL cycles monotonic decay.
4. Airline fleet-wide overview synthesis and avoided AOG cost prevention.
5. FastAPI Endpoints for Stage 40.
"""

import pytest
from fastapi.testclient import TestClient
from aasi_aero_fno.turbofan_fleet_rul_twin import (
    TurbofanFleetRulEngine,
    TurbofanEngineModel,
    TURBOFAN_SPECS,
)
from backend.main import app


def test_paris_erdogan_crack_propagation():
    engine = TurbofanFleetRulEngine()
    specs = TURBOFAN_SPECS[TurbofanEngineModel.CFM_LEAP_1A]

    # At 0 cycles: crack length equals initial crack (0.5 mm)
    crack_0, da_0, k_0 = engine.evaluate_paris_crack_growth(specs, cycles=0, initial_crack_mm=0.5)
    assert crack_0 == 0.5
    assert da_0 > 0.0
    assert k_0 > 0.0

    # At 8,000 cycles: crack must grow monotonically
    crack_8k, da_8k, k_8k = engine.evaluate_paris_crack_growth(specs, cycles=8000, initial_crack_mm=0.5)
    assert crack_8k > crack_0
    assert k_8k > k_0
    assert da_8k > da_0  # Crack growth rate accelerates with crack length
    assert crack_8k < specs.critical_crack_length_mm


def test_egt_margin_and_efficiency_degradation():
    engine = TurbofanFleetRulEngine()
    specs = TURBOFAN_SPECS[TurbofanEngineModel.CFM_LEAP_1A]

    # Fresh engine: 0 cycles -> full margin
    egt_0, deg_0, hpc_0, hpt_0 = engine.evaluate_egt_and_efficiencies(specs, 0)
    assert egt_0 == specs.fresh_egt_margin_celsius
    assert deg_0 == 0.0

    # Aged engine: 10,000 cycles -> significant erosion
    egt_10k, deg_10k, hpc_10k, hpt_10k = engine.evaluate_egt_and_efficiencies(specs, 10000)
    assert egt_10k < egt_0
    assert deg_10k > 50.0
    assert hpc_10k > hpc_0
    assert hpt_10k > hpt_0


def test_weibull_survival_and_rul():
    engine = TurbofanFleetRulEngine()
    specs = TURBOFAN_SPECS[TurbofanEngineModel.CFM_LEAP_1A]

    r_0, h_0, rul_0 = engine.evaluate_weibull_survival(specs, 0)
    assert r_0 == 1.0
    assert rul_0 > 10000

    r_7k, h_7k, rul_7k = engine.evaluate_weibull_survival(specs, 7000)
    assert r_7k < r_0
    assert rul_7k < rul_0
    assert h_7k > 0.0


def test_engine_diagnosis_and_fleet_overview():
    engine = TurbofanFleetRulEngine()

    # 1. Fresh engine nominal diagnosis
    diag_fresh = engine.diagnose_engine(TurbofanEngineModel.CFM_LEAP_1A, flight_cycles=1500)
    assert diag_fresh.maintenance_status == "NOMINAL_FLIGHT_SERVICE"
    assert diag_fresh.avoided_aog_savings_usd == 0.0

    # 2. Critical aged engine diagnosis
    diag_aged = engine.diagnose_engine(TurbofanEngineModel.CFM_LEAP_1A, flight_cycles=12500)
    assert diag_aged.maintenance_status in ("CRITICAL_AOG_RISK", "EXPEDITE_C_CHECK")
    assert diag_aged.avoided_aog_savings_usd > 100000.0

    # 3. Fleet overview
    fleet = engine.get_fleet_overview()
    assert fleet["total_engines_monitored"] == 12
    assert fleet["total_avoided_aog_savings_usd"] > 500000.0
    assert len(fleet["engines"]) == 12


def test_fleet_rul_api_endpoints():
    client = TestClient(app)

    # 1. Diagnose engine endpoint
    res_diag = client.post(
        "/api/v1/fleet-rul/diagnose-engine",
        json={
            "engine_model_key": "CFM_LEAP_1A",
            "flight_cycles": 6800,
            "serial_number": "ESN-LEAP-98421",
        },
    )
    assert res_diag.status_code == 200
    d_diag = res_diag.json()["data"]
    assert "rul_cycles_remaining" in d_diag
    assert d_diag["egt_margin_celsius"] > 0.0

    # 2. Fleet overview endpoint
    res_fleet = client.get("/api/v1/fleet-rul/fleet-overview")
    assert res_fleet.status_code == 200
    d_fleet = res_fleet.json()["data"]
    assert d_fleet["total_engines_monitored"] == 12
    assert "fleet_mean_rul_cycles" in d_fleet
