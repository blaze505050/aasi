"""
AASI Milestone 2: Deterministic Compute Router Tests.
Tests routing behavior across:
- LOCAL
- COLAB
- REMOTE_FUTURE
- UNAVAILABLE
Verifies:
- Detailed scientific explanation in every choice
- Order-of-magnitude regime classification
- Absolute refusal to claim exact runtime predictions
- Integration with FastAPI control plane
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from runner.protocol.models import RunnerCapabilities
from backend.compute.router import (
    ComputeDestination,
    ComputeRequirements,
    DeterministicComputeRouter,
)
from backend.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def high_end_workstation_caps():
    """Workstation with native OpenFOAM, 64 GB RAM, 16 cores, CUDA, MPI."""
    return RunnerCapabilities(
        runner_id="RUNNER-HIGH-END",
        host_name="workstation-01",
        os_platform="linux",
        is_wsl2=False,
        python_version="3.12.0",
        cpu_cores_logical=16,
        cpu_cores_physical=16,
        ram_total_gb=64.0,
        ram_available_gb=48.0,
        disk_free_gb=500.0,
        has_cuda=True,
        cuda_device_name="NVIDIA RTX 4090",
        cuda_memory_gb=24.0,
        has_mpi=True,
        mpi_version="OpenMPI 4.1.2",
        openfoam_available=True,
        openfoam_version="OpenFOAM-10",
        supported_solvers=["simpleFoam", "pimpleFoam", "rhoSimpleFoam", "blockMesh"],
    )


@pytest.fixture
def laptop_no_openfoam_caps():
    """Developer edge machine: 8 GB RAM, 4 cores, no GPU, no local OpenFOAM."""
    return RunnerCapabilities(
        runner_id="RUNNER-LAPTOP",
        host_name="dev-laptop",
        os_platform="win32",
        is_wsl2=True,
        python_version="3.12.10",
        cpu_cores_logical=4,
        cpu_cores_physical=4,
        ram_total_gb=8.0,
        ram_available_gb=2.0,
        disk_free_gb=25.0,
        has_cuda=False,
        has_mpi=False,
        openfoam_available=False,
        openfoam_version=None,
        supported_solvers=[],
    )


# ---------------------------------------------------------------------------
# Test 1: Invalid or Unrecognized Solver -> UNAVAILABLE
# ---------------------------------------------------------------------------
def test_router_unrecognized_solver_returns_unavailable():
    """Unrecognized or malicious solver requests must return UNAVAILABLE."""
    req = ComputeRequirements(
        case_id="CASE-UNAVAIL-01",
        solver="unknownMaliciousSolver",
        estimated_cells=50_000,
    )
    decision = DeterministicComputeRouter.route(req)
    assert decision.destination == ComputeDestination.UNAVAILABLE
    assert "Invalid or unrecognized" in decision.reason
    assert "cannot be scheduled" in decision.explanation


def test_router_invalid_cells_returns_unavailable():
    """Zero or negative cells must return UNAVAILABLE fail-closed."""
    req = ComputeRequirements(
        case_id="CASE-UNAVAIL-02",
        solver="simpleFoam",
        estimated_cells=-100,
    )
    decision = DeterministicComputeRouter.route(req)
    assert decision.destination == ComputeDestination.UNAVAILABLE


# ---------------------------------------------------------------------------
# Test 2: Local OpenFOAM Available & Sufficient RAM -> LOCAL
# ---------------------------------------------------------------------------
def test_router_routes_to_local_when_solver_and_ram_present(high_end_workstation_caps):
    """When workstation has the solver binary and ample memory, route to LOCAL."""
    req = ComputeRequirements(
        case_id="CASE-LOCAL-01",
        solver="simpleFoam",
        estimated_cells=150_000,
        timestep_count=1000,
        dimension="2D",
    )
    decision = DeterministicComputeRouter.route(req, capabilities=high_end_workstation_caps)
    assert decision.destination == ComputeDestination.LOCAL
    assert decision.recommended_backend == "LOCAL_OPENFOAM_RUNNER"
    assert "native solver" in decision.reason.lower()
    assert "local" in decision.explanation.lower()
    assert decision.audit.local_solver_available is True
    assert decision.audit.local_ram_sufficient is True


# ---------------------------------------------------------------------------
# Test 3: Local Lacks Solver -> COLAB
# ---------------------------------------------------------------------------
def test_router_routes_to_colab_when_local_lacks_openfoam(laptop_no_openfoam_caps):
    """When workstation lacks OpenFOAM binary, route to COLAB fallback."""
    req = ComputeRequirements(
        case_id="CASE-COLAB-01",
        solver="simpleFoam",
        estimated_cells=125_000,
        timestep_count=1000,
        dimension="2D",
    )
    decision = DeterministicComputeRouter.route(req, capabilities=laptop_no_openfoam_caps)
    assert decision.destination == ComputeDestination.COLAB
    assert decision.recommended_backend == "GOOGLE_COLAB_NOTEBOOK"
    assert "lacks native OpenFOAM binary" in decision.reason
    assert "Google Colab free-tier" in decision.explanation
    assert decision.audit.local_solver_available is False
    assert decision.audit.colab_cells_sufficient is True


# ---------------------------------------------------------------------------
# Test 4: Local Has Solver but Insufficient Available RAM -> COLAB
# ---------------------------------------------------------------------------
def test_router_routes_to_colab_when_mesh_exceeds_local_ram():
    """If local solver is installed but available RAM is constrained, route to COLAB."""
    low_ram_caps = RunnerCapabilities(
        runner_id="RUNNER-LOW-RAM",
        host_name="box",
        os_platform="linux",
        is_wsl2=False,
        python_version="3.12.0",
        cpu_cores_logical=8,
        cpu_cores_physical=8,
        ram_total_gb=8.0,
        ram_available_gb=0.8,  # Only 800 MB free
        disk_free_gb=50.0,
        has_cuda=False,
        has_mpi=True,
        openfoam_available=True,
        openfoam_version="OpenFOAM-10",
        supported_solvers=["simpleFoam"],
    )
    req = ComputeRequirements(
        case_id="CASE-COLAB-02",
        solver="simpleFoam",
        estimated_cells=400_000,  # Needs ~1.8 GB RAM
        dimension="2D",
    )
    decision = DeterministicComputeRouter.route(req, capabilities=low_ram_caps)
    assert decision.destination == ComputeDestination.COLAB
    assert "exceeds safe local available memory" in decision.reason or "exceeds workstation safe limit" in decision.reason


# ---------------------------------------------------------------------------
# Test 5: Workload Exceeds Colab Free Tier -> REMOTE_FUTURE
# ---------------------------------------------------------------------------
def test_router_routes_massive_mesh_to_remote_future(laptop_no_openfoam_caps):
    """Cases exceeding Colab limits (>1.5M cells or >10 GB RAM) route to REMOTE_FUTURE."""
    req = ComputeRequirements(
        case_id="CASE-REMOTE-01",
        solver="simpleFoam",
        estimated_cells=3_500_000,  # 3.5 million cells exceeds Colab free tier
        timestep_count=2000,
        dimension="2D",
    )
    decision = DeterministicComputeRouter.route(req, capabilities=laptop_no_openfoam_caps)
    assert decision.destination == ComputeDestination.REMOTE_FUTURE
    assert decision.recommended_backend == "REMOTE_HPC_SLURM"
    assert "exceeds both local workstation and Colab free-tier" in decision.reason
    assert "Slurm HPC" in decision.explanation


def test_router_routes_heavy_3d_to_remote_future(laptop_no_openfoam_caps):
    """Heavy 3D Navier-Stokes simulations route to REMOTE_FUTURE."""
    req = ComputeRequirements(
        case_id="CASE-REMOTE-3D",
        solver="pimpleFoam",
        estimated_cells=800_000,
        timestep_count=5000,
        dimension="3D",
    )
    decision = DeterministicComputeRouter.route(req, capabilities=laptop_no_openfoam_caps)
    assert decision.destination == ComputeDestination.REMOTE_FUTURE
    assert decision.recommended_backend == "REMOTE_HPC_SLURM"


# ---------------------------------------------------------------------------
# Test 6: Anti-Fabrication: No Exact Runtime Predictions
# ---------------------------------------------------------------------------
def test_router_disclaims_exact_runtime_predictions(high_end_workstation_caps):
    """Router must provide regime classification and explicit disclaimer rather than exact seconds."""
    req = ComputeRequirements(
        case_id="CASE-DISCLAIMER-01",
        solver="simpleFoam",
        estimated_cells=80_000,
        timestep_count=1000,
        dimension="2D",
    )
    decision = DeterministicComputeRouter.route(req, capabilities=high_end_workstation_caps)
    # Must have disclaimer
    assert "cannot be predicted deterministically" in decision.runtime_prediction_disclaimer
    # Must have an order-of-magnitude regime
    assert "REGIME" in decision.estimated_regime
    # Must NOT claim an exact number of seconds for completion
    assert "estimated_seconds" not in decision.model_dump()


# ---------------------------------------------------------------------------
# Test 7: FastAPI Control Plane Integration
# ---------------------------------------------------------------------------
def test_router_fastapi_endpoint(test_client):
    """Verifies POST /api/compute/route returns deterministic decision."""
    payload = {
        "case_id": "API-CASE-ROUTE-01",
        "solver": "simpleFoam",
        "estimated_cells": 100_000,
        "timestep_count": 1000,
        "parallelism": 1,
        "dimension": "2D",
    }
    res = test_client.post("/api/compute/route", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["destination"] in ["LOCAL", "COLAB", "REMOTE_FUTURE", "UNAVAILABLE"]
    assert "reason" in data
    assert "explanation" in data
    assert "estimated_regime" in data
    assert "audit" in data
