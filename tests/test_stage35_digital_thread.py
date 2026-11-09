"""
Unit and regression tests for Stage 35: Digital Thread Merkle Supply Chain & AS9100D Quality Passport.
Validates:
1. Cryptographic SHA-256 Merkle-DAG lifecycle lineage and tamper detection.
2. AS9100D Rev D Statistical Process Control (SPC) Cpk index computation and Six-Sigma flight qualification.
3. Automated FAA Form 8130-3 / DGCA Form 1 Airworthiness Approval Tag certification.
4. FastAPI REST API endpoints.
"""

import copy
import pytest
from starlette.testclient import TestClient

from aasi_aero_fno.digital_thread_passport import (
    MerkleLineageDAG,
    audit_as9100d_quality,
    generate_faa_form_8130_3,
    build_complete_digital_thread,
)
from backend.main import app


def test_merkle_dag_lineage_and_tamper_detection():
    """Validates SHA-256 Merkle-DAG integrity and tamper detection."""
    dag = MerkleLineageDAG(serial_number="SN-TI64-TEST", part_number="AASI-WING-RIB-01")

    # Add 3 lifecycle steps
    s1 = dag.add_step(
        step_id="STEP-1",
        phase_name="Powder Batch Verification",
        facility="AP&C",
        parameters={"o2_ppm": 850, "particle_size_um": 32.4},
    )
    s2 = dag.add_step(
        step_id="STEP-2",
        phase_name="LPBF Additive Manufacturing",
        facility="AASI Flight Lab",
        parameters={"laser_power_w": 280.0, "scan_speed_mps": 1.2},
        parent_hashes=[s1.step_hash],
    )
    s3 = dag.add_step(
        step_id="STEP-3",
        phase_name="Micro-CT NDT Inspection",
        facility="AASI NDT Lab",
        parameters={"relative_density_percent": 99.95},
        parent_hashes=[s2.step_hash],
    )

    root = dag.compute_merkle_root()
    assert len(root) == 64  # SHA-256 hex string

    # Verify pristine thread
    is_valid, err = dag.verify_integrity()
    assert is_valid is True
    assert err is None

    # Simulate malicious tamper: alter laser power in step 2 without re-signing
    s2.process_parameters["laser_power_w"] = 350.0  # altered telemetry!
    tamper_valid, tamper_err = dag.verify_integrity()
    assert tamper_valid is False
    assert "Tamper detected at step STEP-2" in tamper_err


def test_as9100d_spc_capability_indices():
    """Validates AS9100D Six-Sigma process capability indices Cp and Cpk."""
    # 1. High-capability Six-Sigma process: mean = 190.0, std = 4.0, limits [160, 220]
    # Cp = 60 / (6 * 4) = 2.50, Cpk = 30 / (3 * 4) = 2.50
    ideal_samples = [188.0, 192.0, 190.5, 189.5, 191.0, 189.0, 192.5, 187.5]
    audit_high = audit_as9100d_quality(
        measurements=ideal_samples,
        nominal_target=190.0,
        lower_spec_limit=160.0,
        upper_spec_limit=220.0,
    )

    cpk_val = audit_high["capability_indices"]["cpk"]
    assert cpk_val >= 1.67
    assert audit_high["capability_indices"]["process_verdict"] == "HIGH_CAPABILITY_SIX_SIGMA"
    assert audit_high["capability_indices"]["estimated_ppm_defects"] < 1.0

    # 2. Marginal capability process (Cpk ~ 1.1)
    marginal_samples = [172.0, 208.0, 168.0, 212.0, 185.0, 195.0, 205.0]
    audit_marg = audit_as9100d_quality(
        measurements=marginal_samples,
        nominal_target=190.0,
        lower_spec_limit=160.0,
        upper_spec_limit=220.0,
    )
    assert audit_marg["capability_indices"]["cpk"] < 1.33

    # Check clauses
    clauses = {c["clause"]: c["status"] for c in audit_high["as9100d_clauses"]}
    assert "8.1.4" in clauses
    assert "8.5.2" in clauses


def test_faa_form_8130_airworthiness_tag_generation():
    """Validates official FAA Form 8130-3 / DGCA Form 1 airworthiness synthesis."""
    cert = generate_faa_form_8130_3(
        part_name="TITANIUM_TRANSONIC_WING_RIB",
        part_number="AASI-LPBF-TI64-001",
        serial_number="SN-2026-X892",
        material_spec="AMS 4928 Grade 5 Ti-6Al-4V",
        merkle_root_hash="c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2",
        cpk_score=1.75,
    )

    assert "FAA Form 8130-3" in cert["form_standard"]
    assert cert["cert_tracking_id"].startswith("FAA-8130-")
    assert cert["item_details"]["serial_number"] == "SN-2026-X892"
    assert "14 CFR § 21.303" in cert["airworthiness_approval"]["cfr_reference"]
    assert len(cert["airworthiness_approval"]["digital_signature_hash"]) == 64
    assert "AMS 4928" in cert["remarks"]


def test_complete_digital_thread_builder():
    """Validates complete multi-tier digital thread assembly for aerospace flight hardware."""
    thread = build_complete_digital_thread("TITANIUM_WING_RIB_LPBF")

    assert thread["is_tamper_free"] is True
    assert len(thread["lifecycle_steps"]) == 5
    assert len(thread["merkle_root_hash"]) == 64
    assert thread["spc_quality_audit"]["capability_indices"]["cpk"] > 1.33
    assert thread["airworthiness_certificate"]["item_details"]["part_number"] == "AASI-LPBF-TI64-001"


def test_digital_thread_api_endpoints():
    """Validates FastAPI REST endpoints for Stage 35."""
    client = TestClient(app)

    # 1. Presets endpoint
    res_presets = client.get("/api/v1/digital-thread/presets")
    assert res_presets.status_code == 200
    presets = res_presets.json()["data"]["presets"]
    keys = [p["key"] for p in presets]
    assert "TITANIUM_WING_RIB_LPBF" in keys
    assert "INCONEL_TURBINE_BLADE" in keys

    # 2. Audit endpoint
    res_audit = client.post(
        "/api/v1/digital-thread/audit",
        json={"scenario_preset": "TITANIUM_WING_RIB_LPBF"},
    )
    assert res_audit.status_code == 200
    adata = res_audit.json()["data"]
    assert adata["is_tamper_free"] is True
    assert len(adata["lifecycle_steps"]) == 5

    # 3. SPC Cpk endpoint
    res_spc = client.post(
        "/api/v1/digital-thread/spc-cpk",
        json={
            "measurements": [188.0, 192.0, 190.0, 189.0, 191.0, 190.5],
            "nominal_target": 190.0,
            "lower_spec_limit": 160.0,
            "upper_spec_limit": 220.0,
        },
    )
    assert res_spc.status_code == 200
    assert res_spc.json()["data"]["capability_indices"]["cpk"] > 1.5

    # 4. Form 8130 certificate endpoint
    res_cert = client.post(
        "/api/v1/digital-thread/certificate-8130",
        json={
            "part_name": "TITANIUM_TRANSONIC_WING_RIB",
            "part_number": "AASI-LPBF-TI64-001",
            "serial_number": "SN-2026-X892",
            "material_spec": "AMS 4928 Ti-6Al-4V",
            "merkle_root_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "cpk_score": 1.82,
        },
    )
    assert res_cert.status_code == 200
    assert "cert_tracking_id" in res_cert.json()["data"]
