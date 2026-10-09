"""
AASI Milestone 1: Local Runner Comprehensive Test Suite.
Tests:
- Host capability detection (OpenFOAM, Python, MPI, CUDA, CPU, RAM)
- Allowlisted executable security sandbox
- Shell injection prevention
- Fixed workspace path traversal protection
- Explicit user approval enforcement
- Structured artifact returns with SHA-256 digests
- FastAPI control plane endpoints (register, capabilities, heartbeat, execute)
- Process timeout enforcement
"""

import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

WORKSPACE_ROOT = Path(__file__).parent.parent.resolve()
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from runner.protocol.models import (
    RunnerCapabilities,
    RunnerRegistration,
    ExecutionApproval,
    ExecutionRequest,
    ExecutionStatus,
)
from runner.detector.capabilities import HostCapabilityDetector
from runner.sandbox.security import ExecutionSandbox, SecurityViolationError
from runner.executors.openfoam import OpenFOAMExecutor
from runner.agent import LocalRunnerAgent
from backend.main import app


@pytest.fixture
def temp_workspace():
    td = tempfile.mkdtemp(prefix="aasi_test_workspace_")
    yield Path(td)


@pytest.fixture
def test_client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: Capability Detection Audit
# ---------------------------------------------------------------------------
def test_runner_capability_detection():
    """Verifies that capability detector reports all required host specs."""
    caps = HostCapabilityDetector.detect(runner_id="TEST-RUNNER-001")
    assert isinstance(caps, RunnerCapabilities)
    assert caps.runner_id == "TEST-RUNNER-001"
    assert caps.cpu_cores_logical >= 1
    assert caps.ram_total_gb > 0.0
    assert caps.disk_free_gb >= 0.0
    assert len(caps.python_version) > 0
    assert caps.os_platform in ["win32", "linux", "darwin"]
    assert isinstance(caps.openfoam_available, bool)
    assert isinstance(caps.has_cuda, bool)
    assert isinstance(caps.has_mpi, bool)
    assert isinstance(caps.supported_solvers, list)


# ---------------------------------------------------------------------------
# Test 2: Unallowlisted Executables Blocked Fail-Closed
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad_cmd", [
    "bash", "sh", "cmd.exe", "powershell.exe", "rm", "del", "curl", "wget", "netstat",
])
def test_sandbox_rejects_unallowlisted_executable(temp_workspace, bad_cmd):
    """Sandbox must reject any executable not in the allowlist."""
    sandbox = ExecutionSandbox(workspace_root=temp_workspace)
    req = ExecutionRequest(
        job_id="JOB-SEC-01",
        solver_command=bad_cmd,
        solver_args=["-v"],
        case_dir_relative="case_01",
        approval=ExecutionApproval(
            approval_token="valid_cryptographic_token_12345",
            job_id="JOB-SEC-01",
            user_approved=True,
        ),
    )
    with pytest.raises(SecurityViolationError, match="not in the allowlist"):
        sandbox.validate_request(req)


# ---------------------------------------------------------------------------
# Test 3: Shell Injection Metacharacters Blocked
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("injection_arg", [
    "; rm -rf /",
    "| cat /etc/passwd",
    "& echo hacked",
    "`id`",
    "$(whoami)",
    "> output.txt",
    "< input.txt",
    "arg1\narg2",
    "arg\x00extra",
])
def test_sandbox_rejects_shell_metacharacters(temp_workspace, injection_arg):
    """Arguments with shell metacharacters must be blocked."""
    sandbox = ExecutionSandbox(workspace_root=temp_workspace)
    req = ExecutionRequest(
        job_id="JOB-SEC-02",
        solver_command="simpleFoam",
        solver_args=["-case", injection_arg],
        case_dir_relative="case_01",
        approval=ExecutionApproval(
            approval_token="valid_cryptographic_token_12345",
            job_id="JOB-SEC-02",
            user_approved=True,
        ),
    )
    with pytest.raises(SecurityViolationError, match="prohibited shell metacharacters"):
        sandbox.validate_request(req)


# ---------------------------------------------------------------------------
# Test 4: Path Traversal Outside Workspace Blocked
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("traversal_path", [
    "../../outside",
    "..\\..\\outside",
    "/etc/shadow",
    "C:\\Windows\\System32",
    "case/../../../root",
])
def test_sandbox_rejects_path_traversal(temp_workspace, traversal_path):
    """Any attempt to point case_dir outside workspace must be blocked."""
    sandbox = ExecutionSandbox(workspace_root=temp_workspace)
    req = ExecutionRequest(
        job_id="JOB-SEC-03",
        solver_command="simpleFoam",
        solver_args=[],
        case_dir_relative=traversal_path,
        approval=ExecutionApproval(
            approval_token="valid_cryptographic_token_12345",
            job_id="JOB-SEC-03",
            user_approved=True,
        ),
    )
    with pytest.raises(SecurityViolationError, match="Path traversal detected"):
        sandbox.validate_request(req)


# ---------------------------------------------------------------------------
# Test 5: Explicit User Approval Required
# ---------------------------------------------------------------------------
def test_sandbox_rejects_unapproved_execution(temp_workspace):
    """Execution must fail-closed without explicit user approval."""
    sandbox = ExecutionSandbox(workspace_root=temp_workspace)
    # user_approved = False
    req1 = ExecutionRequest(
        job_id="JOB-APPROVAL-01",
        solver_command="simpleFoam",
        case_dir_relative="case_01",
        approval=ExecutionApproval(
            approval_token="valid_token_12345",
            job_id="JOB-APPROVAL-01",
            user_approved=False,
        ),
    )
    with pytest.raises(SecurityViolationError, match="Explicit user approval required"):
        sandbox.validate_request(req1)

    # Missing / empty token
    req2 = ExecutionRequest(
        job_id="JOB-APPROVAL-02",
        solver_command="simpleFoam",
        case_dir_relative="case_01",
        approval=ExecutionApproval(
            approval_token="",
            job_id="JOB-APPROVAL-02",
            user_approved=True,
        ),
    )
    with pytest.raises(SecurityViolationError, match="Invalid or missing cryptographic approval token"):
        sandbox.validate_request(req2)

    # Job mismatch
    req3 = ExecutionRequest(
        job_id="JOB-APPROVAL-03",
        solver_command="simpleFoam",
        case_dir_relative="case_01",
        approval=ExecutionApproval(
            approval_token="valid_token_12345",
            job_id="DIFFERENT-JOB-ID",
            user_approved=True,
        ),
    )
    with pytest.raises(SecurityViolationError, match="Approval token job mismatch"):
        sandbox.validate_request(req3)


# ---------------------------------------------------------------------------
# Test 6: Allowlisted Execution & Artifact Collection
# ---------------------------------------------------------------------------
def test_sandbox_executes_allowlisted_command_and_collects_artifacts(temp_workspace):
    """Executing an allowlisted command generates log and artifact receipts with SHA-256."""
    sandbox = ExecutionSandbox(workspace_root=temp_workspace)
    executor = OpenFOAMExecutor(sandbox=sandbox, runner_id="TEST-RUNNER")

    # Pre-create a script file in the case directory
    case_dir = temp_workspace / "case_exec_01"
    case_dir.mkdir(parents=True, exist_ok=True)
    script_file = case_dir / "sim.py"
    script_file.write_text(
        "print('Solving for p, Initial residual = 0.001, Final residual = 1.5e-5')\n"
        "with open('output.dat', 'w') as f:\n"
        "    f.write('CL=0.66 CD=0.0089')\n",
        encoding="utf-8"
    )

    req = ExecutionRequest(
        job_id="JOB-EXEC-01",
        solver_command=sys.executable,
        solver_args=["sim.py"],
        case_dir_relative="case_exec_01",
        approval=ExecutionApproval(
            approval_token="valid_approval_token_9999",
            job_id="JOB-EXEC-01",
            user_approved=True,
        ),
    )

    result = executor.execute(req)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.exit_code == 0
    assert result.duration_seconds >= 0.0
    assert "Solving for p" in result.stdout_tail
    assert len(result.artifacts) >= 1

    # Check artifact digests
    artifact_map = {a.relative_path: a for a in result.artifacts}
    assert any("output.dat" in p for p in artifact_map)
    for art in result.artifacts:
        assert len(art.sha256_hash) == 64
        assert art.file_size_bytes > 0


# ---------------------------------------------------------------------------
# Test 7: Timeout Enforcement
# ---------------------------------------------------------------------------
def test_runner_timeout_enforcement(temp_workspace):
    """Commands exceeding timeout are killed and reported as TIMED_OUT."""
    sandbox = ExecutionSandbox(workspace_root=temp_workspace)
    executor = OpenFOAMExecutor(sandbox=sandbox, runner_id="TEST-RUNNER")

    case_dir = temp_workspace / "case_timeout_01"
    case_dir.mkdir(parents=True, exist_ok=True)
    sleep_script = case_dir / "sleep.py"
    sleep_script.write_text("import time\ntime.sleep(5)\n", encoding="utf-8")

    req = ExecutionRequest(
        job_id="JOB-TIMEOUT-01",
        solver_command=sys.executable,
        solver_args=["sleep.py"],
        case_dir_relative="case_timeout_01",
        timeout_seconds=1,
        approval=ExecutionApproval(
            approval_token="valid_approval_token_9999",
            job_id="JOB-TIMEOUT-01",
            user_approved=True,
        ),
    )

    result = executor.execute(req)
    assert result.status == ExecutionStatus.TIMED_OUT
    assert "timeout" in result.stderr_tail.lower()


# ---------------------------------------------------------------------------
# Test 8: Control Plane API Integration
# ---------------------------------------------------------------------------
def test_runner_api_endpoints(test_client):
    """Verifies runner registration, capabilities probing, and heartbeat."""
    # 1. Capabilities
    res_caps = test_client.get("/api/runner/capabilities")
    assert res_caps.status_code == 200
    caps_data = res_caps.json()
    assert caps_data["registered"] is True
    assert "capabilities" in caps_data
    assert caps_data["capabilities"]["cpu_cores_logical"] >= 1

    # 2. Register
    agent = LocalRunnerAgent()
    reg = agent.get_registration_payload()
    res_reg = test_client.post("/api/runner/register", json=reg.model_dump())
    assert res_reg.status_code == 200
    assert res_reg.json()["status"] == "REGISTERED"

    # 3. Heartbeat
    res_hb = test_client.post(
        "/api/runner/heartbeat",
        json={"runner_id": reg.runner_id, "status": "ONLINE", "active_jobs": 0},
    )
    assert res_hb.status_code == 200
    assert res_hb.json()["status"] == "ACK"

    # 4. Status
    res_status = test_client.get("/api/runner/status")
    assert res_status.status_code == 200
    assert res_status.json()["active"] is True


# ---------------------------------------------------------------------------
# Test 9: Control Plane Execute Endpoint Security
# ---------------------------------------------------------------------------
def test_runner_api_execute_unapproved_rejected(test_client):
    """API endpoint rejects unapproved job requests with 403 Forbidden."""
    unapproved_req = {
        "job_id": "JOB-API-UNAPPROVED",
        "solver_command": "simpleFoam",
        "solver_args": [],
        "case_dir_relative": "case_test",
        "approval": {
            "approval_token": "token_123",
            "job_id": "JOB-API-UNAPPROVED",
            "user_approved": False,
        },
    }
    res = test_client.post("/api/runner/jobs/execute", json=unapproved_req)
    assert res.status_code == 403
    assert "Explicit user approval required" in res.json()["detail"]
