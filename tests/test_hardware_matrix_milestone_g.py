"""
Milestone G Verification Tests: Hardware Capability Matrix & Resource-Aware Routing.

Validates that AASI accurately detects host resources without hallucination,
safely classifies local operating constraints (4-core, 8 GB RAM, no GPU),
and routes heavy CFD or deep neural workloads to external execution fail-closed.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.compute.models import ComputeBackendType
from backend.compute.hardware_matrix import (
    hardware_matrix_manager,
    HardwareProfile,
    ComputationalTaskType,
)


def test_detect_hardware_returns_accurate_profile():
    profile = hardware_matrix_manager.detect_hardware(force_refresh=True)

    assert isinstance(profile, HardwareProfile)
    assert profile.cpu_cores_logical >= 1
    assert profile.ram_total_gb > 0.0
    assert profile.ram_available_gb > 0.0
    assert profile.disk_free_gb > 0.0
    assert isinstance(profile.has_cuda, bool)
    assert isinstance(profile.is_windows, bool)
    assert isinstance(profile.has_wsl2, bool)
    assert isinstance(profile.installed_solvers, dict)
    assert profile.safe_max_local_mesh_cells > 0
    assert profile.safe_max_local_dimension in ("2D", "3D")
    assert ComputeBackendType.USER_EXECUTED.value in profile.supported_backends
    assert ComputeBackendType.REMOTE.value in profile.supported_backends


def test_route_task_surrogate_inference_allowed_locally():
    decision = hardware_matrix_manager.route_task(
        task_type="SURROGATE_INFERENCE",
    )
    assert decision.allowed_locally is True
    assert decision.recommended_backend == ComputeBackendType.LOCAL
    assert "Surrogate polynomial and ridge" in decision.reason
    assert len(decision.resource_bottlenecks) == 0


def test_route_task_cfd_3d_routed_to_user_executed():
    decision = hardware_matrix_manager.route_task(
        task_type="CFD_3D",
        dimension="3D",
        solver="openfoam",
    )
    assert decision.allowed_locally is False
    assert decision.recommended_backend == ComputeBackendType.USER_EXECUTED
    assert "3D CFD simulations cannot run" in decision.reason
    assert len(decision.resource_bottlenecks) > 0


def test_route_task_cfd_2d_missing_solver_fails_closed():
    profile = hardware_matrix_manager.detect_hardware()
    # If OpenFOAM is not installed on this test host
    if not profile.installed_solvers.get("OpenFOAM", False):
        decision = hardware_matrix_manager.route_task(
            task_type="CFD_2D",
            dimension="2D",
            solver="openfoam",
        )
        assert decision.allowed_locally is False
        assert decision.recommended_backend == ComputeBackendType.USER_EXECUTED
        assert "not installed locally" in decision.reason


def test_route_task_cfd_2d_mesh_oversized_routed_externally():
    # Simulate a profile with installed solver but huge mesh
    mock_hw = HardwareProfile(
        cpu_cores_logical=4,
        cpu_cores_physical=4,
        ram_total_gb=8.0,
        ram_available_gb=2.0,
        disk_free_gb=20.0,
        has_cuda=False,
        is_windows=True,
        has_wsl2=True,
        installed_solvers={"openfoam": True},
        safe_max_local_mesh_cells=50_000,
        safe_max_local_dimension="2D",
        supported_backends=["USER_EXECUTED", "LOCAL"],
        operating_regime="LIGHTWEIGHT_CPU_EDGE",
    )

    decision = hardware_matrix_manager.route_task(
        task_type="CFD_2D",
        mesh_cells=150_000,
        dimension="2D",
        solver="openfoam",
        profile=mock_hw,
    )
    assert decision.allowed_locally is False
    assert decision.recommended_backend == ComputeBackendType.USER_EXECUTED
    assert "exceeds local safety limit" in decision.reason
    assert len(decision.resource_bottlenecks) > 0


def test_route_task_deep_surrogate_training_requires_gpu():
    decision = hardware_matrix_manager.route_task(
        task_type="SURROGATE_TRAINING",
        model_type="fno",
    )
    assert decision.allowed_locally is False
    assert decision.recommended_backend == ComputeBackendType.REMOTE
    assert any("GPU" in b for b in decision.resource_bottlenecks)


def test_api_system_capabilities_and_routing():
    client = TestClient(app)

    # 1. GET /api/system/capabilities
    cap_res = client.get("/api/system/capabilities")
    assert cap_res.status_code == 200
    cap_data = cap_res.json()
    assert "cpu_cores_logical" in cap_data
    assert "ram_total_gb" in cap_data
    assert "safe_max_local_mesh_cells" in cap_data
    assert "operating_regime" in cap_data

    # 2. POST /api/compute/route-request
    route_res = client.post(
        "/api/compute/route-request",
        json={
            "task_type": "CFD_3D",
            "dimension": "3D",
            "solver": "openfoam",
        },
    )
    assert route_res.status_code == 200
    route_data = route_res.json()
    assert route_data["allowed_locally"] is False
    assert route_data["recommended_backend"] == "USER_EXECUTED"
    assert len(route_data["resource_bottlenecks"]) > 0

    # 3. GET / (root index contains system_capabilities_url)
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "system_capabilities_url" in root_res.json()
