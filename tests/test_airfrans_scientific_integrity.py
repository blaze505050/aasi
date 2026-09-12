"""
AASI Adversarial Scientific Integrity Test Suite: AirfRANS & Multi-Dataset Validation.

Governs multi-dataset CFD integration, provenance tracking, storage safety,
adversarial physical bounds checking, and OOD generalization verification.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.datasets.catalog import DatasetCatalog
from backend.datasets.adapters.base import (
    DatasetStorageState,
    DatasetCase,
    DatasetField,
)
from backend.datasets.adapters.airfrans import AirfRANSDatasetAdapter
from backend.datasets.adapters.naca0012 import NACA0012DatasetAdapter
from backend.datasets.validation import DatasetValidator, ValidationSeverity
from backend.datasets.splits import DataSplitManager
from backend.physics.multi_benchmark import MultiDatasetBenchmarkEngine
from backend.physics.uncertainty_model import AerodynamicUncertaintyQuantifier
from backend.research.service import research_loop_service
from backend.research.evidence_ledger import EvidenceType, EvidenceLedger
from backend.research.bundle import ResearchBundleExporter


@pytest.fixture
def client():
    return TestClient(app)


# 1. Provenance & License Verification
def test_airfrans_provenance_and_odbl_license():
    catalog = DatasetCatalog()
    adapter = catalog.get_adapter("DATASET-AIRFRANS-1K")
    assert adapter is not None
    manifest = adapter.get_manifest()

    assert manifest.dataset_id == "DATASET-AIRFRANS-1K"
    assert "Open Data Commons Open Database License (ODbL) v1.0" in manifest.license
    assert "NeurIPS" in manifest.citation
    assert "Bonnet" in manifest.citation
    assert manifest.url == "https://github.com/Extrality/AirfRANS"
    assert manifest.solver == "OpenFOAM (simpleFoam)"
    assert manifest.experimental_or_simulated == "SIMULATED"


# 2. Workstation Storage Safety Guards
def test_airfrans_storage_safety_guard():
    adapter = AirfRANSDatasetAdapter()
    report = adapter.check_storage_safety()
    assert report.dataset_id == "DATASET-AIRFRANS-1K"
    assert report.estimated_compressed_bytes >= 20_000_000_000
    # In constrained workstation environment, storage state must not be DATASET_FULL
    state = adapter.get_storage_state()
    assert state in (DatasetStorageState.DATASET_METADATA_ONLY, DatasetStorageState.RESOURCE_LIMITED)


# 3. Input & Output Field Schemas
def test_airfrans_fields_and_units_integrity():
    adapter = AirfRANSDatasetAdapter()
    fields = adapter.get_fields()
    field_names = [f.field_name for f in fields]

    # Required 7 inputs
    for required_in in ["x", "y", "distance_to_wall", "normal_x", "normal_y", "U_inf_x", "U_inf_y"]:
        assert required_in in field_names

    # Required outputs
    for required_out in ["U_x", "U_y", "p_over_rho", "nu_tilde", "CL", "CD"]:
        assert required_out in field_names

    # Units check
    nu_field = next(f for f in fields if f.field_name == "nu_tilde")
    assert nu_field.units == "m^2/s"
    assert nu_field.min_physical_bound >= 0.0


# 4. Representative Simulation Physical Bounds
def test_airfrans_representative_cases_physical_bounds():
    adapter = AirfRANSDatasetAdapter()
    cases = adapter.list_cases(limit=100)
    assert len(cases) >= 10

    for c in cases:
        assert c.reynolds >= 2.0e6
        assert c.mach > 0.0
        assert -6.0 <= c.aoa_deg <= 16.0
        if c.cd is not None:
            assert c.cd > 0.0, f"Unphysical drag in case {c.case_id}: {c.cd}"
        if c.node_count is not None:
            assert c.node_count > 100_000


# 5. Adversarial: Catch Negative Drag
def test_dataset_validator_catches_negative_drag():
    unphysical_case = DatasetCase(
        case_id="CORRUPT_DRAG_01",
        dataset_id="DATASET-AIRFRANS-1K",
        geometry_name="NACA 0012",
        reynolds=3.0e6,
        mach=0.15,
        aoa_deg=4.0,
        cl=0.42,
        cd=-0.005,  # Second law violation
        node_count=200000
    )
    results = DatasetValidator.validate_case(unphysical_case)
    bounds_check = next(r for r in results if r.check_name == "physical_bounds_check")
    assert not bounds_check.passed
    assert bounds_check.severity == ValidationSeverity.ERROR
    assert "Negative drag coefficient" in bounds_check.details


# 6. Adversarial: Catch Unphysical Lift
def test_dataset_validator_catches_unphysical_lift():
    unphysical_case = DatasetCase(
        case_id="CORRUPT_LIFT_01",
        dataset_id="DATASET-AIRFRANS-1K",
        geometry_name="NACA 0012",
        reynolds=3.0e6,
        mach=0.15,
        aoa_deg=4.0,
        cl=5.50,  # Unphysical for subsonic 2D airfoil
        cd=0.015,
        node_count=200000
    )
    results = DatasetValidator.validate_case(unphysical_case)
    bounds_check = next(r for r in results if r.check_name == "physical_bounds_check")
    assert not bounds_check.passed
    assert "Unphysical lift coefficient" in bounds_check.details


# 7. Adversarial: Catch Corrupt Mesh
def test_dataset_validator_catches_corrupt_mesh():
    corrupt_mesh_case = DatasetCase(
        case_id="CORRUPT_MESH_01",
        dataset_id="DATASET-AIRFRANS-1K",
        geometry_name="NACA 0012",
        reynolds=3.0e6,
        mach=0.15,
        aoa_deg=4.0,
        cl=0.42,
        cd=0.008,
        node_count=-500  # Invalid node count
    )
    results = DatasetValidator.validate_case(corrupt_mesh_case)
    mesh_check = next(r for r in results if r.check_name == "mesh_sanity_check")
    assert not mesh_check.passed
    assert mesh_check.severity == ValidationSeverity.ERROR


# 8. Duplicate Detection
def test_dataset_validator_detects_duplicate_cases():
    c1 = DatasetCase(
        case_id="CASE_A",
        dataset_id="DATASET-AIRFRANS-1K",
        geometry_name="NACA 0012",
        reynolds=3.0e6,
        mach=0.15,
        aoa_deg=4.0,
        cl=0.42,
        cd=0.008
    )
    c2 = DatasetCase(
        case_id="CASE_B",
        dataset_id="DATASET-AIRFRANS-1K",
        geometry_name="NACA 0012",
        reynolds=3.0e6,
        mach=0.15,
        aoa_deg=4.0,
        cl=0.42,
        cd=0.008
    )
    dup_res = DatasetValidator.check_duplicate_cases([c1, c2])
    assert not dup_res.passed
    assert len(dup_res.affected_cases) > 0


# 9. Adversarial: Catch Train/Test Geometry Leakage
def test_dataset_validator_geometry_leakage_detection():
    c_train = DatasetCase(case_id="C_TR", dataset_id="D1", geometry_name="NACA 0012", reynolds=2e6, mach=0.1, aoa_deg=0.0)
    c_test = DatasetCase(case_id="C_TE", dataset_id="D1", geometry_name="NACA 0012", reynolds=2e6, mach=0.1, aoa_deg=4.0)
    cases_map = {"C_TR": c_train, "C_TE": c_test}

    leak_res = DatasetValidator.check_geometry_leakage(["C_TR"], ["C_TE"], cases_map)
    assert not leak_res.passed
    assert "Geometric leakage detected" in leak_res.details
    assert "NACA 0012" in leak_res.affected_cases


# 10. Official NeurIPS Splits Geometry Isolation
def test_airfrans_official_splits_isolation():
    adapter = AirfRANSDatasetAdapter()
    splits = adapter.get_available_splits()
    cases_map = {c.case_id: c for c in adapter.list_cases(limit=100)}

    leak_res = DatasetValidator.check_geometry_leakage(splits["full_train"], splits["full_test"], cases_map)
    assert leak_res.passed, f"Leakage found in official splits: {leak_res.details}"


# 11. OOD Parameter Distance Metrics
def test_ood_split_distance_metrics():
    in_dist_case = DatasetCase(case_id="IN_1", dataset_id="D1", geometry_name="NACA 0012", reynolds=3.0e6, mach=0.15, aoa_deg=4.0)
    ood_re_case = DatasetCase(case_id="OOD_RE", dataset_id="D1", geometry_name="NACA 0012", reynolds=5.8e6, mach=0.15, aoa_deg=4.0)
    ood_aoa_case = DatasetCase(case_id="OOD_AOA", dataset_id="D1", geometry_name="NACA 0012", reynolds=3.0e6, mach=0.15, aoa_deg=14.0)

    # Reynolds in-domain: [2.0e6, 4.0e6]
    eval_in = DataSplitManager.evaluate_ood_distance(in_dist_case, "reynolds", (2.0e6, 4.0e6))
    assert not eval_in.is_ood
    assert eval_in.normalized_ood_distance == 0.0

    eval_re = DataSplitManager.evaluate_ood_distance(ood_re_case, "reynolds", (2.0e6, 4.0e6))
    assert eval_re.is_ood
    assert eval_re.normalized_ood_distance > 0.5

    # AoA in-domain: [-5.0, 8.0]
    eval_aoa = DataSplitManager.evaluate_ood_distance(ood_aoa_case, "aoa_deg", (-5.0, 8.0))
    assert eval_aoa.is_ood
    assert eval_aoa.normalized_ood_distance > 0.3


# 12. Multi-Dataset Benchmark Engine Execution
def test_multi_dataset_benchmark_engine_execution():
    engine = MultiDatasetBenchmarkEngine()
    test_preds = [
        {"geometry": "NACA 0012", "aoa_deg": 0.0, "mach": 0.15, "reynolds": 6.0e6, "cl": 0.005, "cd": 0.0065},
        {"geometry": "NACA 0012", "aoa_deg": 4.0, "mach": 0.15, "reynolds": 6.0e6, "cl": 0.430, "cd": 0.0078},
        {"geometry": "NACA 0012", "aoa_deg": 8.0, "mach": 0.15, "reynolds": 6.0e6, "cl": 0.845, "cd": 0.0110},
    ]
    res = engine.benchmark_model_predictions(
        model_name="TestSurrogate",
        predictions=test_preds,
        dataset_ids=["DATASET-NACA-0012-LTPT", "DATASET-AIRFRANS-1K"]
    )
    assert res.total_comparisons >= 3
    assert len(res.dataset_summaries) == 2
    assert res.overall_scientific_consistency_score > 0.80
    assert res.uncertainty_assessment is not None


# 13. Multi-Dataset Uncertainty Budget in Stall Regime
def test_multi_dataset_uncertainty_budget_stall():
    unc_linear = AerodynamicUncertaintyQuantifier.compute_multidataset_uncertainty(aoa_deg=4.0)
    unc_stall = AerodynamicUncertaintyQuantifier.compute_multidataset_uncertainty(aoa_deg=14.0)

    assert unc_linear.combined_expanded_uncertainty_cl_u95 < unc_stall.combined_expanded_uncertainty_cl_u95
    assert unc_stall.model_uncertainty.turbulence_model_discrepancy_cl >= 0.060
    assert "Expanded multi-dataset U95 interval" in unc_stall.notes[-1]


# 14. Evidence Ledger Multi-Dataset DAG Records
def test_evidence_ledger_multi_dataset_records():
    run = research_loop_service.execute_flagship_naca0012_run()
    ledger_data = run.evidence_ledger
    assert ledger_data is not None

    records = ledger_data.get("records", [])
    record_types = [r.get("evidence_type") for r in records]

    assert EvidenceType.DATASET_CASE.value in record_types
    assert EvidenceType.DATASET_VALIDATION.value in record_types
    assert EvidenceType.OOD_EVALUATION.value in record_types

    # Cryptographic DAG integrity verification
    ledger = EvidenceLedger(ledger_id=ledger_data["ledger_id"], run_id=run.run_id)
    for r in records:
        ledger.records.append(ledger.records[-1].__class__.model_validate(r) if hasattr(ledger.records, "model_validate") else r)
    
    report = run.provenance_trail
    assert report.get("ledger_integrity_valid") is True
    assert len(report.get("ledger_orphan_records", [])) == 0
    assert len(report.get("ledger_cycles_detected", [])) == 0


# 15. Reproducibility Bundle Manifest with Multi-Dataset Provenance
def test_reproducibility_bundle_multi_dataset_manifest(tmp_path):
    run = research_loop_service.execute_flagship_naca0012_run()
    bundle_dir, zip_path = ResearchBundleExporter.export_bundle(run, output_base_dir=str(tmp_path))

    manifest_file = bundle_dir / "dataset_manifest.json"
    assert manifest_file.exists()

    import json
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert "multi_dataset_benchmarks" in data
    airfrans_ref = next(b for b in data["multi_dataset_benchmarks"] if b["dataset_id"] == "DATASET-AIRFRANS-1K")
    assert airfrans_ref["status"] == "DATASET_REACQUISITION_REQUIRED"
    assert "data.isir.upmc.fr" in airfrans_ref["acquisition_url"]


# 16. REST API Endpoints Verification
def test_rest_api_dataset_endpoints(client):
    # 1. List adapters
    r1 = client.get("/api/datasets/adapters")
    assert r1.status_code == 200
    adapters = r1.json()
    assert any(a["dataset_id"] == "DATASET-AIRFRANS-1K" for a in adapters)
    assert any(a["dataset_id"] == "DATASET-NACA-0012-LTPT" for a in adapters)

    # 2. Audit AirfRANS
    r2 = client.get("/api/datasets/DATASET-AIRFRANS-1K/audit")
    assert r2.status_code == 200
    audit = r2.json()
    assert "Open Data Commons Open Database License (ODbL) v1.0" in audit["manifest"]["license"]
    assert "storage_safety_report" in audit
    assert len(audit["fields"]) >= 10

    # 3. List Cases
    r3 = client.get("/api/datasets/DATASET-AIRFRANS-1K/cases?limit=5")
    assert r3.status_code == 200
    cases_resp = r3.json()
    assert len(cases_resp["cases"]) == 5

    # 4. Get Splits
    r4 = client.get("/api/datasets/DATASET-AIRFRANS-1K/splits")
    assert r4.status_code == 200
    splits_resp = r4.json()
    assert "full_train" in splits_resp["splits"]
    assert "full_test" in splits_resp["splits"]

    # 5. Validate Dataset
    r5 = client.post("/api/datasets/DATASET-AIRFRANS-1K/validate")
    assert r5.status_code == 200
    val_resp = r5.json()
    assert val_resp["is_valid"] is True

    # 6. Benchmark Model
    r6 = client.post("/api/datasets/benchmark", json={
        "model_name": "TestModelV1",
        "predictions": [
            {"geometry": "NACA 0012", "aoa_deg": 2.0, "mach": 0.15, "reynolds": 3e6, "cl": 0.22, "cd": 0.007}
        ]
    })
    assert r6.status_code == 200
    bm_resp = r6.json()
    assert bm_resp["total_comparisons"] >= 1
    assert "DATASET-AIRFRANS-1K" in bm_resp["datasets_evaluated"]
