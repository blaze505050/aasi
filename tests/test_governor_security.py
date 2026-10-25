"""
AASI 2.0 Safety Governor & Resource Monitor Security Test Suite.

Verifies:
1. Deterministic fail-closed authorization semantics
2. Live hardware discovery (CPU, RAM, Disk, Process RSS)
3. Budget headroom and constraint enforcement
4. Global kill switch trip, debounce, and cooperative cancellation
5. Policy allowlist, dangerous command denial, and path traversal protection
6. Cryptographic SHA-256 Merkle audit trail integrity
7. Real-time REST endpoints under /api/system/
"""

import pytest
from fastapi.testclient import TestClient

from backend.governor.constants import (
    DEFAULT_TASK_TIMEOUT_SECONDS,
    HARD_MAX_TIMEOUT_SECONDS,
    DEFAULT_MAX_CPU_PERCENT,
    CRITICAL_CPU_PERCENT,
)
from backend.governor.resource_monitor import (
    ResourceMonitor,
    ResourceSnapshot,
    GpuSnapshot,
    ProcessSnapshot,
)
from backend.governor.resource_budget import (
    ResourceBudget,
    BudgetVerdict,
)
from backend.governor.kill_switch import (
    KillSwitch,
    KillSwitchActiveError,
)
from backend.governor.execution_policy import (
    ExecutionPolicyEngine,
    ExecutionAction,
    ActionType,
    PolicyVerdict,
)
from backend.governor.safety_governor import (
    SafetyGovernor,
    DecisionVerdict,
)


# ─── 1. Resource Monitor Tests ───────────────────────────────────────────────

def test_resource_monitor_snapshot_structure():
    monitor = ResourceMonitor()
    snap = monitor.snapshot()

    assert isinstance(snap, ResourceSnapshot)
    assert snap.hostname
    assert snap.platform in ("win32", "linux", "darwin")
    assert snap.cpu_cores_logical >= 1
    assert 0.0 <= snap.cpu_percent <= 100.0
    assert snap.ram_total_gb > 0.0
    assert snap.ram_available_gb >= 0.0
    assert 0.0 <= snap.ram_percent <= 100.0
    assert snap.disk_total_gb > 0.0
    assert snap.disk_free_gb >= 0.0
    assert isinstance(snap.gpu, GpuSnapshot)
    assert isinstance(snap.process, ProcessSnapshot)
    assert snap.process.pid > 0
    assert snap.process.rss_mb >= 0.0


# ─── 2. Resource Budget Tests ────────────────────────────────────────────────

def test_resource_budget_bounds_validation():
    # Valid budget
    budget = ResourceBudget(max_timeout_seconds=300, max_ram_gb=1.0)
    assert budget.max_timeout_seconds == 300

    # Exceeding HARD_MAX must raise ValueError
    with pytest.raises(ValueError, match="exceeds HARD_MAX"):
        ResourceBudget(max_timeout_seconds=HARD_MAX_TIMEOUT_SECONDS + 10)


def test_resource_budget_evaluation_fail_closed():
    # Mock nominal snapshot
    snap = ResourceSnapshot(
        hostname="test-host",
        platform="win32",
        cpu_cores_logical=8,
        cpu_percent=15.0,
        ram_total_gb=16.0,
        ram_used_gb=8.0,
        ram_available_gb=8.0,
        ram_percent=50.0,
        disk_total_gb=500.0,
        disk_used_gb=100.0,
        disk_free_gb=400.0,
        disk_percent=20.0,
        gpu=GpuSnapshot(available=False),
        process=ProcessSnapshot(pid=1234, rss_mb=50.0),
        critical_alert=False,
    )

    # 1. Modest budget on healthy system -> Approved
    budget = ResourceBudget(max_ram_gb=1.0, max_disk_gb=5.0)
    verdict = budget.evaluate(snap)
    assert verdict.approved is True
    assert len(verdict.reasons) == 0

    # 2. Excessive RAM request exceeding safe headroom -> Denied
    excessive_ram = ResourceBudget(max_ram_gb=15.0)
    verdict_ram = excessive_ram.evaluate(snap)
    assert verdict_ram.approved is False
    assert any("exceeds safe available RAM" in r for r in verdict_ram.reasons)

    # 3. Excessive Disk request -> Denied
    excessive_disk = ResourceBudget(max_disk_gb=1000.0)
    verdict_disk = excessive_disk.evaluate(snap)
    assert verdict_disk.approved is False
    assert any("exceeds safe free disk" in r for r in verdict_disk.reasons)

    # 4. Requesting GPU when no GPU available -> Denied
    gpu_budget = ResourceBudget(max_gpu_vram_gb=4.0)
    verdict_gpu = gpu_budget.evaluate(snap)
    assert verdict_gpu.approved is False
    assert any("no GPU is available" in r for r in verdict_gpu.reasons)


def test_resource_budget_system_saturation():
    # Saturated CPU snapshot
    saturated_snap = ResourceSnapshot(
        hostname="test-host",
        platform="win32",
        cpu_cores_logical=8,
        cpu_percent=99.0,  # Saturated
        ram_total_gb=16.0,
        ram_used_gb=8.0,
        ram_available_gb=8.0,
        ram_percent=50.0,
        disk_total_gb=500.0,
        disk_used_gb=100.0,
        disk_free_gb=400.0,
        disk_percent=20.0,
        gpu=GpuSnapshot(available=False),
        process=ProcessSnapshot(pid=1234, rss_mb=50.0),
        critical_alert=True,
        alert_reasons=["CPU saturated"],
    )

    budget = ResourceBudget(max_ram_gb=0.1)
    verdict = budget.evaluate(saturated_snap)
    assert verdict.approved is False
    assert any("saturated" in r.lower() or "alert" in r.lower() for r in verdict.reasons)


# ─── 3. Kill Switch Tests ────────────────────────────────────────────────────

def test_kill_switch_lifecycle():
    ks = KillSwitch()
    assert ks.is_tripped is False
    ks.check_or_raise()  # Should not raise

    # Trip switch
    state = ks.trip(reason="Emergency fire drill", triggered_by="admin")
    assert state.is_tripped is True
    assert ks.is_tripped is True
    assert ks.is_running() is False

    with pytest.raises(KillSwitchActiveError, match="EMERGENCY HALT ACTIVE"):
        ks.check_or_raise()

    # Immediate reset without force must fail due to cooldown debounce
    with pytest.raises(ValueError, match="Cooldown debounce active"):
        ks.reset()

    # Force reset
    reset_state = ks.reset(force=True)
    assert reset_state.is_tripped is False
    assert ks.is_tripped is False
    ks.check_or_raise()  # Should not raise


# ─── 4. Execution Policy Engine Tests ────────────────────────────────────────

def test_execution_policy_engine_allowlists():
    policy = ExecutionPolicyEngine(workspace_root=".")

    # 1. Allowed AASI tool
    act_ok = ExecutionAction(
        action_type=ActionType.TOOL_INVOCATION,
        tool_name="aero_2d_solve",
    )
    verdict_ok = policy.evaluate(act_ok)
    assert verdict_ok.allowed is True

    # 2. Disallowed arbitrary tool -> Fail-closed
    act_bad = ExecutionAction(
        action_type=ActionType.TOOL_INVOCATION,
        tool_name="arbitrary_exploit_tool",
    )
    verdict_bad = policy.evaluate(act_bad)
    assert verdict_bad.allowed is False
    assert any("not in permitted tool allowlist" in r for r in verdict_bad.reasons)

    # 3. Dangerous system command -> Blocked
    act_cmd = ExecutionAction(
        action_type=ActionType.SYSTEM_COMMAND,
        command=["rm", "-rf", "/"],
    )
    verdict_cmd = policy.evaluate(act_cmd)
    assert verdict_cmd.allowed is False
    assert any("prohibited dangerous pattern" in r for r in verdict_cmd.reasons)

    # 4. Prohibited path traversal -> Blocked
    act_path = ExecutionAction(
        action_type=ActionType.FILE_READ,
        target_path="C:\\Windows\\System32\\config\\SAM",
    )
    verdict_path = policy.evaluate(act_path)
    assert verdict_path.allowed is False
    assert any("prohibited" in r.lower() for r in verdict_path.reasons)


# ─── 5. Safety Governor Full Integration ─────────────────────────────────────

def test_safety_governor_authorization_and_audit():
    monitor = ResourceMonitor()
    policy = ExecutionPolicyEngine()
    kill_switch = KillSwitch()
    governor = SafetyGovernor(
        resource_monitor=monitor,
        policy_engine=policy,
        kill_switch=kill_switch,
    )

    # Valid action
    action = ExecutionAction(
        action_type=ActionType.TOOL_INVOCATION,
        tool_name="aero_2d_solve",
    )
    budget = ResourceBudget(max_ram_gb=0.1, max_disk_gb=0.5)

    dec = governor.authorize(action, budget)
    # If the physical machine has sufficient RAM at test moment, dec.approved may be True;
    # in any case, dec must be a valid DecisionVerdict with provenance hash
    assert isinstance(dec, DecisionVerdict)
    assert dec.provenance_hash
    assert len(dec.provenance_hash) == 64

    # Now trip kill switch -> must guarantee denial
    kill_switch.trip(reason="Mandatory test trip")
    dec_tripped = governor.authorize(action, budget)
    assert dec_tripped.approved is False
    assert dec_tripped.kill_switch_active is True
    assert any("Emergency kill switch active" in r for r in dec_tripped.denial_reasons)

    # Audit log verification
    audit_entries = governor.get_audit_log()
    assert len(audit_entries) >= 2
    assert governor.verify_audit_log() is True


# ─── 6. API Route Integration ────────────────────────────────────────────────

def test_api_governor_and_resource_routes():
    from backend.main import app
    client = TestClient(app)

    # 1. GET /api/system/resources
    r_res = client.get("/api/system/resources")
    assert r_res.status_code == 200
    res_data = r_res.json()
    assert "cpu_percent" in res_data
    assert "ram_total_gb" in res_data
    assert "process" in res_data

    # 2. GET /api/system/governor/status
    r_stat = client.get("/api/system/governor/status")
    assert r_stat.status_code == 200
    stat_data = r_stat.json()
    assert "kill_switch" in stat_data
    assert "resources" in stat_data

    # 3. Emergency halt cycle via API
    r_halt = client.post(
        "/api/system/emergency-halt",
        json={"reason": "Automated security test halt", "triggered_by": "pytest"},
    )
    assert r_halt.status_code == 200
    assert r_halt.json()["is_tripped"] is True

    # 4. Forced reset via API
    r_reset = client.post(
        "/api/system/emergency-halt/reset",
        json={"authorized_by": "pytest", "force": True},
    )
    assert r_reset.status_code == 200
    assert r_reset.json()["is_tripped"] is False

    # 5. GET /api/system/governor/audit
    r_audit = client.get("/api/system/governor/audit")
    assert r_audit.status_code == 200
    assert isinstance(r_audit.json(), list)
