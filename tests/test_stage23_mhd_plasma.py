"""
Unit and Integration Tests for Stage 23: Magnetohydrodynamic (MHD) Hypersonic Plasma Shielding.
================================================================================================
Tests coupled MHD shock standoff extension, Sutton-Graves aerothermal heat flux mitigation,
cyclotron and plasma cutoff frequencies, Whistler-mode RF window transmission, Faraday power extraction,
and FastAPI REST endpoints.
"""

import math
import numpy as np
import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.mhd_plasma_shield import (
    MHDPlasmaEngine,
    MHDShieldNavigator,
    MHD_PRESETS,
    RFBand,
)
from backend.main import app

client = TestClient(app)


def test_plasma_and_cyclotron_frequencies():
    """Verifies plasma cutoff and electron cyclotron frequencies from first principles."""
    # Test plasma frequency for n_e = 1.0e18 m^-3: f_p = sqrt(n_e * e^2 / (eps_0 * m_e)) / (2*pi) ~ 8.98 GHz
    f_p = MHDPlasmaEngine.compute_plasma_frequency_ghz(1.0e18)
    assert 8.5 < f_p < 9.5, f"Plasma frequency {f_p} GHz outside expected range [8.5, 9.5]"

    # Test electron cyclotron frequency for B = 1.0 T: f_ce = e * B / (2*pi * m_e) ~ 27.99 GHz
    f_ce = MHDPlasmaEngine.compute_cyclotron_frequency_ghz(1.0)
    assert 27.0 < f_ce < 29.0, f"Cyclotron frequency {f_ce} GHz outside expected range [27.0, 29.0]"


def test_mhd_shock_standoff_and_heat_flux_mitigation():
    """Verifies Lorentz magnetic pressure increases shock standoff and reduces convective heat flux."""
    state = MHDPlasmaEngine.compute_mhd_interaction(
        mach=24.5,
        velocity_mps=7650.0,
        density_kg_m3=0.00018,
        nose_radius_m=1.75,
        magnetic_field_tesla=1.5,
        rf_freq_ghz=2.2,
    )

    # 1. Shock standoff must be extended by Lorentz force
    assert state.shock_standoff_mhd_m > state.shock_standoff_baseline_m
    assert state.stuart_number > 0.5

    # 2. Convective heat flux must be mitigated by 25% to 85%
    assert 25.0 <= state.heat_flux_reduction_pct <= 85.0
    assert state.heat_flux_mhd_mw_m2 < state.heat_flux_baseline_mw_m2

    # 3. RF Blackout must be mitigated via Whistler mode
    assert state.rf_blackout_mitigated is True
    assert state.rf_attenuation_db < 40.0

    # 4. Faraday electrical power extraction
    assert state.mhd_power_extracted_kw > 10.0


def test_isro_gaganyaan_mhd_simulation():
    """Verifies complete Gaganyaan MHD mission dossier generation with cryptographic Merkle proof."""
    dossier = MHDShieldNavigator.execute_mhd_simulation("ISRO_GAGANYAAN_MHD_REENTRY")

    assert "Gaganyaan" in dossier.target_vehicle
    assert dossier.magnetic_coil_field_tesla == 1.25
    assert dossier.heat_flux_reduction_pct >= 28.0
    assert dossier.rf_blackout_eliminated is True
    assert dossier.power_generated_kw > 5.0
    assert len(dossier.trajectory_profile) == 16
    assert len(dossier.merkle_provenance_hash) == 64


def test_mhd_api_endpoints():
    """Tests FastAPI REST endpoints for Stage 23."""
    # 1. Presets endpoint
    resp_pre = client.get("/api/v1/mhd/presets")
    assert resp_pre.status_code == 200
    presets = resp_pre.json()
    assert "ISRO_GAGANYAAN_MHD_REENTRY" in presets
    assert "HGV_SHAVIT_GLIDE_MACH20" in presets

    # 2. Simulate endpoint
    payload = {
        "preset_key": "ISRO_GAGANYAAN_MHD_REENTRY",
        "override_magnetic_field_tesla": 1.6,
    }
    resp_sim = client.post("/api/v1/mhd/simulate", json=payload)
    assert resp_sim.status_code == 200
    data = resp_sim.json()
    assert data["magnetic_coil_field_tesla"] == 1.6
    assert data["heat_flux_reduction_pct"] > 30.0
    assert data["rf_blackout_eliminated"] is True
    assert len(data["trajectory_profile"]) == 16
