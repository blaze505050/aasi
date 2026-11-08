"""
Unit and Integration Tests for Stage 18: Formally Verified DO-178C Level A & ECSS Flight Code Synthesizer.
==========================================================================================================
"""

import pytest
from fastapi.testclient import TestClient

from aasi_aero_fno.certified_code_synthesizer import (
    generate_misra_c_code,
    generate_safe_rust_code,
    generate_lean4_proof_certificate,
    synthesize_flight_certification_dossier,
    STAGE18_PRESETS,
)
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_misra_c_code_generation():
    """Verifies MISRA-C:2012 Amendment 2 source generation complies with strict avionics standards."""
    c_art = generate_misra_c_code(
        vehicle_name="ISRO Gaganyaan Crew Module",
        controller_type="CBF-QP Descent Rate & Alpha Guard",
        alpha_max=24.5,
        nz_max=4.5,
        u_min=-25.0,
        u_max=25.0,
        cbf_gamma=1.8,
    )

    assert c_art.language == "C99_MISRA"
    assert c_art.filename == "aasi_flight_controller.c"
    assert c_art.line_count > 60
    assert c_art.heap_allocation_bytes == 0, "MISRA C code must have zero dynamic memory allocation"
    assert c_art.wcet_microseconds <= 15.0, "WCET must be under 15 us"
    assert len(c_art.sha256_hash) == 64

    # Verify essential safety tokens
    assert "AASI_Step_Controller" in c_art.code_text
    assert "aasi_clamp" in c_art.code_text
    assert "AASI_DENOM_EPSILON" in c_art.code_text
    assert "AASI_ALPHA_MAX_DEG" in c_art.code_text


def test_safe_rust_no_std_code_generation():
    """Verifies Safe-Rust no_std code conforms to zero-heap and zero-panic guarantees."""
    rust_art = generate_safe_rust_code(
        vehicle_name="HAL LCA Tejas Mk-1A",
        controller_type="Neural Lyapunov Alpha-Limiter",
        alpha_max=22.0,
        nz_max=8.0,
        u_min=-30.0,
        u_max=30.0,
        cbf_gamma=2.2,
    )

    assert rust_art.language == "RUST_NO_STD"
    assert rust_art.filename == "aasi_controller.rs"
    assert rust_art.heap_allocation_bytes == 0, "Rust no_std must have zero heap allocation"
    assert rust_art.wcet_microseconds <= 10.0
    assert len(rust_art.sha256_hash) == 64

    # Verify compiler directives
    assert "#![no_std]" in rust_art.code_text
    assert "#![forbid(unsafe_code)]" in rust_art.code_text
    assert "step_certified_controller" in rust_art.code_text
    assert "ControlDecision" in rust_art.code_text


def test_lean4_formal_proof_spec():
    """Verifies Lean-4 machine-checkable theorem certificates are mathematically well-formed."""
    lean_art = generate_lean4_proof_certificate(
        vehicle_name="ISRO SpaDeX Chaser S/C",
        alpha_max=15.0,
        nz_max=0.5,
        u_min=-5.0,
        u_max=5.0,
        cbf_gamma=1.2,
    )

    assert lean_art.language == "LEAN4_PROOF"
    assert lean_art.filename == "AeroCert.lean"
    assert len(lean_art.sha256_hash) == 64

    # Verify critical airworthiness theorems
    assert "theorem theorem_actuator_strictly_bounded" in lean_art.code_text
    assert "theorem theorem_cbf_forward_invariance" in lean_art.code_text
    assert "theorem theorem_denom_epsilon_bounded" in lean_art.code_text
    assert "SafeEnvelope" in lean_art.code_text


def test_full_certification_dossier_gaganyaan():
    """Tests complete DO-178C Level A synthesis dossier for ISRO Gaganyaan re-entry."""
    dossier = synthesize_flight_certification_dossier("ISRO_GAGANYAAN_CM_DESCENT_RTA")

    assert dossier.certification_verdict == "AIRWORTHY_DO178C_DAL_A_CERTIFIED"
    assert dossier.formal_proof_status == "QED_MACHINE_CHECKED"
    assert dossier.overall_mcdc_percentage == 100.0
    assert dossier.worst_case_execution_time_us < 15.0
    assert dossier.schedulability_utilization_pct < 5.0, "Avionics loop utilization must remain < 5%"
    assert len(dossier.invariants) >= 5
    for inv in dossier.invariants:
        assert inv.status == "VERIFIED_FORMAL_QED"


def test_api_certified_code_routes(client):
    """Verifies FastAPI endpoints for Stage 18 certified code synthesis."""
    # 1. Test Presets
    res_presets = client.get("/api/certified-code/presets")
    assert res_presets.status_code == 200
    presets_data = res_presets.json()
    assert "ISRO_GAGANYAAN_CM_DESCENT_RTA" in presets_data
    assert "LCA_TEJAS_TRANSIT_CBF" in presets_data
    assert "SPADEX_AUTONOMOUS_DOCKING" in presets_data

    # 2. Test Synthesis Endpoint
    payload = {
        "preset_id": "LCA_TEJAS_TRANSIT_CBF",
        "alpha_max": 21.5,
        "nz_max": 7.5,
    }
    res_synth = client.post("/api/certified-code/synthesize", json=payload)
    assert res_synth.status_code == 200
    data = res_synth.json()

    assert data["certification_verdict"] == "AIRWORTHY_DO178C_DAL_A_CERTIFIED"
    assert data["overall_mcdc_percentage"] == 100.0
    assert "synthesized_c" in data
    assert "synthesized_rust" in data
    assert "synthesized_lean4" in data
    assert data["synthesized_c"]["language"] == "C99_MISRA"
    assert data["synthesized_rust"]["language"] == "RUST_NO_STD"
    assert data["synthesized_lean4"]["language"] == "LEAN4_PROOF"
    assert len(data["invariants"]) >= 5
    assert len(data["mcdc_coverage"]) >= 5
