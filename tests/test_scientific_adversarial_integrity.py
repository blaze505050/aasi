"""
Adversarial Scientific Integrity & Reproducibility Test Suite.

Governing Directive: Real Scientific Execution, Evidence Integrity & Independent Reproducibility.
Targeted tests designed to actively attempt to break scientific integrity, verifying that AASI
strictly fails closed (INSUFFICIENT_EVIDENCE / UNAVAILABLE / EXPLICIT ERROR) rather than producing
plausible-looking fabricated answers or unearned conclusion promotions.
"""

import os
import json
import zipfile
import hashlib
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.datasets.models import DatasetManifest, DatasetLifecycle, StorageStatus
from backend.datasets.pipeline import DatasetPipelineOrchestrator
from backend.physics_ai.inference import AerodynamicInferenceEngine, ModelUnavailableError
from backend.physics_ai.checkpoints import CheckpointManager
from backend.research.evidence_ledger import (
    EvidenceLedger,
    EvidenceRecord,
    EvidenceType,
    EpistemicStatus,
)
from backend.research.conclusion_engine import (
    ScientificPromotionGate,
    ConclusionLevel,
    PhysicalValidationMetrics,
    StatisticalMetrics,
)
from backend.research.bundle import ResearchBundleExporter
from backend.research.service import ResearchRunOrchestrator, research_loop_service

client = TestClient(app)


def test_adversarial_missing_checkpoint_fails_closed():
    """Attempting inference with a non-existent checkpoint must fail closed with ModelUnavailableError."""
    engine = AerodynamicInferenceEngine(checkpoint_path="data/checkpoints/non_existent_model_xyz.npz")
    assert engine.model is None
    with pytest.raises(ModelUnavailableError, match="MODEL_UNAVAILABLE"):
        engine.predict(geometry="NACA 0012", mach=0.15, reynolds=3.0e6, aoa_deg=5.0)


def test_adversarial_corrupted_dataset_fails_closed(tmp_path):
    """Corrupted coordinate bytes with altered hash must fail closed at HASH_VERIFIED."""
    raw_data = b"NACA 0012\n 1.0 0.0\n 0.0 0.0\n 1.0 0.0\n"
    tampered_data = b"NACA 0012\n 1.0 0.999\n 0.0 0.0\n 1.0 0.0\n"
    correct_hash = hashlib.sha256(raw_data).hexdigest()

    manifest = DatasetManifest(
        dataset_id="TEST-CORRUPT-SET",
        name="Tampered Dataset",
        source="Test Source",
        license="Public Domain",
        checksum=correct_hash,  # Expects raw_data hash
    )

    res = DatasetPipelineOrchestrator.execute_full_pipeline(
        manifest=manifest,
        raw_content=tampered_data  # Feed tampered data
    )
    assert res["success"] is False
    assert res["stage"] == DatasetLifecycle.FAILED.value
    assert "Checksum mismatch" in res["error"]
    assert manifest.lifecycle_stage == DatasetLifecycle.FAILED


def test_adversarial_invalid_license_fails_closed():
    """Proprietary or unknown licenses must fail closed at LICENSE_VERIFIED stage."""
    manifest = DatasetManifest(
        dataset_id="TEST-RESTRICTED-SET",
        name="Commercial Secret Airfoil",
        source="Restricted Lab",
        license="All Rights Reserved - Confidential",
    )
    res = DatasetPipelineOrchestrator.execute_full_pipeline(
        manifest=manifest,
        raw_content=b"Sample content"
    )
    assert res["success"] is False
    assert res["stage"] == DatasetLifecycle.FAILED.value


def test_adversarial_broken_provenance_graph_fails_promotion():
    """A missing link in the backward provenance graph must cap conclusion at INSUFFICIENT_EVIDENCE."""
    ledger = EvidenceLedger(ledger_id="LEDGER-ADV-01", run_id="RUN-ADV-01")

    # Add question
    rec_q = EvidenceRecord(
        evidence_id="ev-q",
        run_id="RUN-ADV-01",
        evidence_type=EvidenceType.QUESTION,
        source="Spec",
        source_identifier="Q-01",
        acquisition_method="FORMAL",
        input_hash="hash_q",
        output_hash="hash_q",
        provenance_chain=[],
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_q)

    # Conclusion references non-existent validation step "ev-non-existent-val"
    rec_conc = EvidenceRecord(
        evidence_id="ev-conc",
        run_id="RUN-ADV-01",
        evidence_type=EvidenceType.RESEARCH_CONCLUSION,
        source="Engine",
        source_identifier="CONC-01",
        acquisition_method="INFERENCE",
        input_hash="hash_val",
        output_hash="hash_conc",
        provenance_chain=["ev-non-existent-val"],  # Broken link!
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_conc)

    # Verify backward chain directly
    is_valid, visited, missing = ledger.verify_backward_chain("ev-conc")
    assert is_valid is False
    assert "ev-non-existent-val" in missing

    # Gate evaluation must return INSUFFICIENT_EVIDENCE
    verdict = ScientificPromotionGate.evaluate_conclusion(
        ledger=ledger,
        target_conclusion_id="ev-conc",
        hypothesis_statement="Test hypothesis",
        regime_evaluations={},
        physical_metrics=PhysicalValidationMetrics(
            lift_slope_error_pct=1.0,
            zero_lift_offset_deg=0.0,
            symmetry_max_error=0.01
        ),
        statistical_metrics=StatisticalMetrics(r2_cl=0.98)
    )
    assert verdict.conclusion_level == ConclusionLevel.INSUFFICIENT_EVIDENCE
    assert verdict.verdict == "INSUFFICIENT_EVIDENCE"
    assert any("Broken provenance chain" in gate for gate in verdict.failed_promotion_gates)


def test_adversarial_surrogate_cannot_claim_experimentally_supported():
    """A surrogate prediction alone must NEVER be promoted to EXPERIMENTALLY_SUPPORTED or CFD_SUPPORTED."""
    ledger = EvidenceLedger(ledger_id="LEDGER-ADV-02", run_id="RUN-ADV-02")

    rec_q = EvidenceRecord(
        evidence_id="ev-q",
        run_id="RUN-ADV-02",
        evidence_type=EvidenceType.QUESTION,
        source="Spec",
        source_identifier="Q-02",
        acquisition_method="FORMAL",
        input_hash="hash_q",
        output_hash="hash_q",
        provenance_chain=[],
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_q)

    rec_surr = EvidenceRecord(
        evidence_id="ev-surr",
        run_id="RUN-ADV-02",
        evidence_type=EvidenceType.SURROGATE_INFERENCE,
        source="SurrogateV1",
        source_identifier="SURR-01",
        acquisition_method="INFERENCE",
        input_hash="hash_q",
        output_hash="hash_pred",
        provenance_chain=["ev-q"],
        epistemic_status=EpistemicStatus.SURROGATE
    )
    ledger.append_record(rec_surr)

    rec_conc = EvidenceRecord(
        evidence_id="ev-conc",
        run_id="RUN-ADV-02",
        evidence_type=EvidenceType.RESEARCH_CONCLUSION,
        source="Engine",
        source_identifier="CONC-02",
        acquisition_method="EVALUATION",
        input_hash="hash_pred",
        output_hash="hash_conc",
        provenance_chain=["ev-surr"],
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_conc)

    verdict = ScientificPromotionGate.evaluate_conclusion(
        ledger=ledger,
        target_conclusion_id="ev-conc",
        hypothesis_statement="Test hypothesis",
        regime_evaluations={},
        physical_metrics=PhysicalValidationMetrics(
            lift_slope_error_pct=2.0,
            zero_lift_offset_deg=0.0,
            symmetry_max_error=0.02
        ),
        statistical_metrics=StatisticalMetrics(r2_cl=0.95)
    )

    # Must be capped at SURROGATE_SUPPORTED
    assert verdict.conclusion_level == ConclusionLevel.SURROGATE_SUPPORTED
    assert verdict.conclusion_level != ConclusionLevel.EXPERIMENTALLY_SUPPORTED
    assert verdict.conclusion_level != ConclusionLevel.CFD_SUPPORTED
    assert verdict.conclusion_level != ConclusionLevel.RESEARCH_GRADE


def test_adversarial_thin_airfoil_cannot_claim_cfd_supported():
    """Analytical thin-airfoil theory alone must be capped at ANALYTICAL_ONLY."""
    ledger = EvidenceLedger(ledger_id="LEDGER-ADV-03", run_id="RUN-ADV-03")

    rec_q = EvidenceRecord(
        evidence_id="ev-q",
        run_id="RUN-ADV-03",
        evidence_type=EvidenceType.QUESTION,
        source="Spec",
        source_identifier="Q-03",
        acquisition_method="FORMAL",
        input_hash="hash_q",
        output_hash="hash_q",
        provenance_chain=[],
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_q)

    rec_ana = EvidenceRecord(
        evidence_id="ev-ana",
        run_id="RUN-ADV-03",
        evidence_type=EvidenceType.ANALYTICAL_DERIVATION,
        source="Thin Airfoil Theory",
        source_identifier="POTENTIAL_THEORY",
        acquisition_method="ANALYTICAL",
        input_hash="hash_q",
        output_hash="hash_ana",
        provenance_chain=["ev-q"],
        epistemic_status=EpistemicStatus.DERIVED
    )
    ledger.append_record(rec_ana)

    rec_conc = EvidenceRecord(
        evidence_id="ev-conc",
        run_id="RUN-ADV-03",
        evidence_type=EvidenceType.RESEARCH_CONCLUSION,
        source="Engine",
        source_identifier="CONC-03",
        acquisition_method="EVALUATION",
        input_hash="hash_ana",
        output_hash="hash_conc",
        provenance_chain=["ev-ana"],
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_conc)

    verdict = ScientificPromotionGate.evaluate_conclusion(
        ledger=ledger,
        target_conclusion_id="ev-conc",
        hypothesis_statement="Thin airfoil hypothesis",
        regime_evaluations={},
        physical_metrics=PhysicalValidationMetrics(
            lift_slope_error_pct=0.0,
            zero_lift_offset_deg=0.0,
            symmetry_max_error=0.0
        ),
        statistical_metrics=StatisticalMetrics(r2_cl=1.0)
    )

    assert verdict.conclusion_level == ConclusionLevel.ANALYTICAL_ONLY
    assert verdict.conclusion_level != ConclusionLevel.CFD_SUPPORTED


def test_adversarial_physical_violations_fail_closed():
    """Even with perfect R2, negative drag or non-monotonic lift must fail closed to INSUFFICIENT_EVIDENCE."""
    ledger = EvidenceLedger(ledger_id="LEDGER-ADV-04", run_id="RUN-ADV-04")

    rec_q = EvidenceRecord(
        evidence_id="ev-q",
        run_id="RUN-ADV-04",
        evidence_type=EvidenceType.QUESTION,
        source="Spec",
        source_identifier="Q-04",
        acquisition_method="FORMAL",
        input_hash="hq",
        output_hash="hq",
        provenance_chain=[],
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_q)

    rec_conc = EvidenceRecord(
        evidence_id="ev-conc",
        run_id="RUN-ADV-04",
        evidence_type=EvidenceType.RESEARCH_CONCLUSION,
        source="Engine",
        source_identifier="CONC-04",
        acquisition_method="EVALUATION",
        input_hash="hq",
        output_hash="hc",
        provenance_chain=["ev-q"],
        epistemic_status=EpistemicStatus.REAL
    )
    ledger.append_record(rec_conc)

    # Physical violation: negative drag!
    phys_violation = PhysicalValidationMetrics(
        lift_slope_error_pct=0.5,
        zero_lift_offset_deg=0.0,
        symmetry_max_error=0.01,
        drag_positivity_verified=False,  # VIOLATION!
        monotonic_lift_linear_range=True
    )
    stat_high = StatisticalMetrics(r2_cl=0.999, rmse_cl=0.001)

    verdict = ScientificPromotionGate.evaluate_conclusion(
        ledger=ledger,
        target_conclusion_id="ev-conc",
        hypothesis_statement="Hypothesis",
        regime_evaluations={},
        physical_metrics=phys_violation,
        statistical_metrics=stat_high
    )

    assert verdict.conclusion_level == ConclusionLevel.INSUFFICIENT_EVIDENCE
    assert any("drag coefficient" in fail for fail in verdict.failed_promotion_gates)


def test_flagship_evidence_ledger_integrity():
    """Verifies that the real flagship NACA 0012 run builds a complete EvidenceLedger with Merkle root."""
    run = ResearchRunOrchestrator.execute_flagship_naca0012()
    assert run.conclusion_level == ConclusionLevel.MULTI_SOURCE_VALIDATED.value
    assert run.evidence_ledger is not None
    assert "records" in run.evidence_ledger
    assert len(run.evidence_ledger["records"]) >= 7

    # Verify all records have valid hashes
    for rec in run.evidence_ledger["records"]:
        assert len(rec["input_hash"]) > 0
        assert len(rec["output_hash"]) > 0
        assert rec["epistemic_status"] in [e.value for e in EpistemicStatus]

    # Verify Merkle root exists and is 64 hex characters
    merkle = run.evidence_ledger.get("merkle_root")
    assert merkle is not None
    assert len(merkle) == 64


def test_reproducibility_bundle_generation_and_verification(tmp_path):
    """Exports reproducibility bundle, checks all 12 canonical files, and verifies SHA-256 manifest."""
    run = ResearchRunOrchestrator.execute_flagship_naca0012()
    bundle_dir, zip_path = ResearchBundleExporter.export_bundle(run, output_base_dir=str(tmp_path))

    assert bundle_dir.exists()
    assert zip_path.exists()

    expected_files = [
        "research_question.json",
        "sources.json",
        "citations.json",
        "dataset_manifest.json",
        "input_parameters.json",
        "computation_manifest.json",
        "solver_information.json",
        "validation_results.json",
        "provenance.json",
        "conclusion.json",
        "README.md",
        "hashes.sha256",
    ]

    for fname in expected_files:
        fpath = bundle_dir / fname
        assert fpath.exists(), f"Missing expected bundle descriptor: {fname}"
        assert fpath.stat().st_size > 0, f"File {fname} was empty"

    # Verify hashes.sha256 matches all files
    hashes_content = (bundle_dir / "hashes.sha256").read_text(encoding="utf-8")
    lines = [line.strip() for line in hashes_content.splitlines() if line.strip()]
    assert len(lines) >= len(expected_files) - 1

    for line in lines:
        expected_sha, rel_name = line.split("  ", 1)
        target = bundle_dir / rel_name
        assert target.exists()
        hasher = hashlib.sha256()
        with open(target, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        assert hasher.hexdigest() == expected_sha, f"Hash mismatch for {rel_name}"

    # Verify zip archive content
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        for fname in expected_files:
            assert any(fname in name for name in namelist)


def test_api_reproducibility_bundle_endpoints():
    """Validates /api/research/runs/{run_id}/bundle and /api/research/runs/{run_id}/export."""
    # 1. Execute flagship run
    resp_exec = client.post("/api/research/runs/execute-flagship")
    assert resp_exec.status_code == 200
    run_id = resp_exec.json()["run_id"]

    # 2. Inspect bundle manifest
    resp_bundle = client.get(f"/api/research/runs/{run_id}/bundle")
    assert resp_bundle.status_code == 200
    b_data = resp_bundle.json()
    assert b_data["run_id"] == run_id
    assert b_data["zip_exists"] is True
    assert "hashes.sha256" in b_data["bundle_files"]
    assert "conclusion.json" in b_data["bundle_files"]
    assert b_data["conclusion_level"] == "MULTI_SOURCE_VALIDATED"

    # 3. Download zip export
    resp_export = client.get(f"/api/research/runs/{run_id}/export")
    assert resp_export.status_code == 200
    assert resp_export.headers["content-type"] == "application/zip"
    assert len(resp_export.content) > 1000  # Non-trivial zip file
