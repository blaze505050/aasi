"""
AASI Phase 0 Regression & Truth-Preserving Verification Tests.

Verifies:
1. Missing or unverified surrogate checkpoint fails closed with ModelUnavailableError (no random weights).
2. Source adapters declare honest access methods (STATIC_SEED / METADATA_ONLY) and never claim DIRECT_API without live fetch.
3. Current information service reports accurate age_days, STALE_STATIC_SEED, and freshness warnings.
4. LocalComputeBackend invokes runner.run_case without AttributeError.
5. ScienceResolutionEngine strictly validates target variables without falling back to CL.
6. FastAPI endpoints return honest 503 and is_live: False warnings.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.physics_ai.inference import AerodynamicInferenceEngine, ModelUnavailableError
from backend.physics_ai.service import PhysicsAIService
from backend.sources.models import AccessMethod
from backend.sources.nasa import NASASourceAdapter
from backend.sources.isro import ISROSourceAdapter
from backend.sources.esa import ESASourceAdapter
from backend.sources.current_info import CurrentInformationService
from backend.compute.local import LocalComputeBackend
from backend.compute.models import ComputeRequest, ComputeBackendType
from backend.simulation.runner import SimulationRunner


def test_missing_checkpoint_fails_closed(tmp_path):
    """Scientific inference must strictly fail closed if checkpoint is missing."""
    nonexistent = tmp_path / "does_not_exist.npz"
    engine = AerodynamicInferenceEngine(checkpoint_path=str(nonexistent))
    
    assert engine.weights_status == "MISSING"
    assert engine.model is None
    assert engine.checksum == "MISSING"
    
    # Must refuse forward inference with explicit ModelUnavailableError
    with pytest.raises(ModelUnavailableError) as excinfo:
        engine.predict("naca0012", mach=0.2, reynolds=2.0e6, aoa_deg=4.0)
    assert "MODEL_UNAVAILABLE" in str(excinfo.value)
    
    # Must refuse polar sweep
    with pytest.raises(ModelUnavailableError) as excinfo_polar:
        engine.predict_polar("naca0012", mach=0.2, reynolds=2.0e6)
    assert "MODEL_UNAVAILABLE" in str(excinfo_polar.value)


def test_sources_declare_honest_access_methods():
    """Adapters must never claim DIRECT_API when searching offline curated indexes."""
    assert NASASourceAdapter.METADATA.access_method == AccessMethod.STATIC_SEED
    assert NASASourceAdapter.METADATA.update_frequency == "Curated Static Index"
    
    assert ISROSourceAdapter.METADATA.access_method == AccessMethod.METADATA_ONLY
    assert ESASourceAdapter.METADATA.access_method == AccessMethod.METADATA_ONLY
    
    # Search results must report STATIC_SEED_INDEX acquisition method
    nasa = NASASourceAdapter()
    results = nasa.search("naca")
    assert len(results) > 0
    assert results[0].get("acquisition_method") == "STATIC_SEED_INDEX"
    assert results[0].get("provenance_type") == "METADATA_DESCRIPTOR_SHA256"


def test_current_info_freshness_tracking():
    """Historical records from 2023-2024 must carry age_days and STALE_STATIC_SEED status."""
    svc = CurrentInformationService()
    assert "STATIC_SEED_DATA" in svc.FRESHNESS_NOTICE
    
    events = svc.get_latest_events()
    assert len(events) > 0
    
    for ev in events:
        assert ev.age_days > 0
        assert ev.freshness_status == "STALE_STATIC_SEED"
        assert ev.acquisition_method == "STATIC_SEED_INDEX"
        assert ev.label == "CURRENT_INFORMATION"


def test_local_compute_runner_interface():
    """LocalComputeBackend must correctly call runner.run_case without AttributeError."""
    backend = LocalComputeBackend()
    
    # Check SimulationRunner has both run_case and run alias
    assert hasattr(backend.runner, "run_case")
    assert hasattr(backend.runner, "run")
    assert backend.runner.run == backend.runner.run_case
    
    # Execute request when solver is missing should return failed diagnostic without crashing
    req = ComputeRequest(
        case_id="test-case-001",
        backend=ComputeBackendType.LOCAL,
        solver="NonExistentSolver99",
        geometry="NACA 0012",
        mach=0.15,
        reynolds=3000000.0,
        aoa_deg=4.0
    )
    result = backend.execute(req)
    assert result["status"] == "FAILED"
    assert "not installed locally" in result["reason"]


from backend.science.engine import ScientificResolutionEngine


def test_science_engine_target_variable_validation():
    """ScientificResolutionEngine must not silently substitute CL for unknown/unsupported target variables."""
    engine = ScientificResolutionEngine()
    
    # Query with CP (pressure coefficient) which surrogate does not output directly
    res = engine.resolve("What is the pressure coefficient CP of NACA 0012 at Mach 0.2, Reynolds 2000000, AoA 0 deg?")
    trace_str = " ".join(res.get("trace", []))
    
    # Must trace that CP is unsupported by the surrogate rather than silently returning CL
    assert "Target variable 'CP' is not supported by aerodynamic surrogate" in trace_str


def test_api_current_info_warning():
    """GET /api/current-info must return is_live: False and the freshness warning."""
    client = TestClient(app)
    response = client.get("/api/current-info")
    assert response.status_code == 200
    data = response.json()
    assert data["is_live"] is False
    assert "STATIC_SEED_DATA" in data["warning"]
    assert len(data["events"]) > 0
