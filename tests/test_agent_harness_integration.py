"""
AASI 2.0 Agent Task Harness & Scientific Skills Integration Test Suite.

Verifies:
1. Strongly-typed ToolBus dispatch under Safety Governor gate
2. All 9 core AASI scientific tools round-trip execution
3. Full cognitive loop (QUESTION -> PLAN -> VALIDATE -> EXECUTE -> VERIFY -> RECONCILE -> LEARN -> DECIDE -> COMPLETE)
4. Physical invariant verification (CD >= 0, lift slope, bounded CL)
5. Kill switch interception during active task loop (HALTED state)
6. Epistemic tier tagging and Merkle provenance chain integrity
7. REST API endpoints under /api/agent/*
"""

import pytest
from fastapi.testclient import TestClient

from backend.governor import global_kill_switch, ResourceBudget
from backend.tools.contracts import EpistemicTier
from backend.harness import (
    global_task_harness,
    global_tool_bus,
    TaskHarness,
    ToolBus,
    TaskState,
    HarnessTaskResult,
    ToolResult,
)


# ─── 1. ToolBus & Catalog Tests ──────────────────────────────────────────────

def test_tool_bus_catalog():
    tools = global_tool_bus.list_tools()
    assert len(tools) >= 9
    names = {t["name"] for t in tools}
    expected = {
        "aero_2d_solve",
        "aero_3d_vlm",
        "polar_sweep",
        "uncertainty_quantify",
        "benchmark_verify",
        "geometry_parse",
        "export_datcom",
        "export_shabp",
        "mesh_generate",
    }
    assert expected.issubset(names)


def test_tool_bus_parameter_bounds_enforcement():
    # alpha_deg has bounds [-20, 25]; pass 80 deg -> should fail validation
    res = global_tool_bus.dispatch(
        tool_name="aero_2d_solve",
        parameters={"airfoil": "NACA 0012", "alpha_deg": 80.0},
    )
    assert res.success is False
    assert "out of valid bounds" in (res.error or "")


# ─── 2. Core AASI Skills Round-Trip Tests ─────────────────────────────────────

def test_skill_aero_2d_solve():
    res = global_tool_bus.dispatch(
        tool_name="aero_2d_solve",
        parameters={"airfoil": "NACA 0012", "alpha_deg": 4.0, "mach": 0.15, "reynolds": 3e6},
    )
    assert res.success is True
    out = res.output
    assert isinstance(out, dict)
    assert 0.35 < out["CL"] < 0.60
    assert 0.005 < out["CD"] < 0.025
    assert out["L_over_D"] > 20.0
    assert res.epistemic_tier == EpistemicTier.ANALYTICAL
    assert len(res.provenance_hash) == 64


def test_skill_aero_3d_vlm():
    res = global_tool_bus.dispatch(
        tool_name="aero_3d_vlm",
        parameters={"wingspan_m": 12.0, "aspect_ratio": 8.0, "alpha_deg": 5.0, "airfoil": "NACA 0012"},
    )
    assert res.success is True
    out = res.output
    assert out["CL_3D"] > 0.0
    assert out["CD_induced"] > 0.0
    assert out["CD_total"] > out["CD_induced"]
    assert out["lift_curve_slope_per_deg"] > 0.05


def test_skill_polar_sweep():
    res = global_tool_bus.dispatch(
        tool_name="polar_sweep",
        parameters={"airfoil": "NACA 0012", "alpha_start": -2.0, "alpha_end": 8.0, "step_deg": 2.0},
    )
    assert res.success is True
    out = res.output
    assert out["num_points"] == 6
    assert out["max_L_over_D"] > 30.0
    assert len(out["points"]) == 6


def test_skill_uncertainty_quantify():
    res = global_tool_bus.dispatch(
        tool_name="uncertainty_quantify",
        parameters={"coefficient": "CL", "nominal_value": 0.435},
    )
    assert res.success is True
    out = res.output
    assert out["standard_uncertainty"] > 0.0
    assert out["expanded_uncertainty_95pct"] > out["standard_uncertainty"]
    assert out["standard_framework"] == "GUM (JCGM 100:2008 / ASME V&V 20)"


def test_skill_benchmark_verify():
    res = global_tool_bus.dispatch(
        tool_name="benchmark_verify",
        parameters={"geometry": "NACA 0012", "alpha_deg": 4.0},
    )
    assert res.success is True
    out = res.output
    assert "discrepancy_cl_percent" in out
    assert "discrepancy_cd_percent" in out
    assert res.epistemic_tier == EpistemicTier.DATABASE_REAL


def test_skill_geometry_parse():
    res = global_tool_bus.dispatch(
        tool_name="geometry_parse",
        parameters={"geometry": "NACA 2412", "num_points": 80},
    )
    assert res.success is True
    out = res.output
    assert out["maximum_thickness_t_c"] == 0.12
    assert out["maximum_camber_m_c"] == 0.02
    assert out["camber_position_p_c"] == 0.4


def test_skill_export_datcom():
    res = global_tool_bus.dispatch(
        tool_name="export_datcom",
        parameters={"geometry": "NACA 0012", "mach": 0.15},
    )
    assert res.success is True
    out = res.output
    assert out["format"] == "USAF_DATCOM_CARD_DECK"
    assert "DIM M" in out["raw_datcom"]
    assert "FLTCON" in out["raw_datcom"]


def test_skill_export_shabp():
    res = global_tool_bus.dispatch(
        tool_name="export_shabp",
        parameters={"geometry": "NACA 0012", "mach": 2.0},
    )
    assert res.success is True
    out = res.output
    assert out["format"] == "NASA_SHABP_TABULATED_POLAR"
    assert "$TABLE" in out["raw_shabp"] or "S/HABP" in out["raw_shabp"]


def test_skill_mesh_generate():
    res = global_tool_bus.dispatch(
        tool_name="mesh_generate",
        parameters={"geometry": "NACA 0012"},
    )
    assert res.success is True
    out = res.output
    assert out["mesh_type"] == "C-GRID_HYBRID_PRISMATIC"
    assert out["epistemic_tier"] == "STAGED_ONLY"


# ─── 3. TaskHarness Cognitive Loop & Verification ────────────────────────────

def test_task_harness_full_cycle():
    result = global_task_harness.run("What is the aerodynamic performance of NACA 0012 at alpha = 4 degrees?")

    assert result.final_state == TaskState.COMPLETED
    assert result.success is True
    assert "NACA 0012" in result.answer
    assert "Lift coefficient CL" in result.answer
    assert "Epistemic Tier:" in result.answer
    assert len(result.provenance_chain_hash) == 64

    # Verify execution state trace
    states = [step.state for step in result.steps]
    expected_order = [
        TaskState.QUESTION,
        TaskState.PLANNING,
        TaskState.VALIDATING,
        TaskState.EXECUTING,
        TaskState.VERIFYING,
        TaskState.RECONCILING,
        TaskState.LEARNING,
        TaskState.DECIDING,
    ]
    assert states == expected_order

    # Verify Merkle provenance integrity
    prev = "GENESIS"
    for step in result.steps:
        expected_hash = step.compute_hash(prev)
        assert step.provenance_hash == expected_hash
        prev = step.provenance_hash


def test_task_harness_kill_switch_interception():
    global_kill_switch.trip("Test emergency halt during task")
    try:
        result = global_task_harness.run("What is lift at 4 deg?")
        assert result.final_state == TaskState.HALTED
        assert result.success is False
        assert "EXECUTION HALTED" in result.answer
    finally:
        global_kill_switch.reset(force=True)


# ─── 4. REST API Endpoint Tests ──────────────────────────────────────────────

def test_api_agent_routes():
    from backend.main import app
    client = TestClient(app)

    # 1. GET /api/agent/tools
    r_tools = client.get("/api/agent/tools")
    assert r_tools.status_code == 200
    catalog = r_tools.json()
    assert len(catalog) >= 9

    # 2. POST /api/agent/tools/dispatch
    r_disp = client.post(
        "/api/agent/tools/dispatch",
        json={"tool_name": "aero_2d_solve", "parameters": {"airfoil": "NACA 0012", "alpha_deg": 4.0}},
    )
    assert r_disp.status_code == 200
    disp_data = r_disp.json()
    assert disp_data["success"] is True
    assert "CL" in disp_data["output"]

    # 3. POST /api/agent/task
    r_task = client.post(
        "/api/agent/task",
        json={"question": "What is the lift coefficient of NACA 0012 at alpha = 4 degrees?"},
    )
    assert r_task.status_code == 200
    task_data = r_task.json()
    assert task_data["final_state"] == "COMPLETED"
    assert task_data["success"] is True
    assert "CL" in task_data["answer"]
