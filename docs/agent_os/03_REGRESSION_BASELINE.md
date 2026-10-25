# AASI 2.0 — 03. Regression Baseline

**Environment**: Windows 11 AMD64, Python 3.12.10 (.venv)  
**Verification Date**: 2026-10-25

---

## 1. Test Suite Results

All primary functional and security test suites are in passing status:

- **Governor & Resource Safety Suite** (`tests/test_governor_security.py`):
  - `test_resource_monitor_snapshot_structure`: PASSED
  - `test_resource_budget_bounds_validation`: PASSED
  - `test_resource_budget_evaluation_fail_closed`: PASSED
  - `test_resource_budget_system_saturation`: PASSED
  - `test_kill_switch_lifecycle`: PASSED
  - `test_execution_policy_engine_allowlists`: PASSED
  - `test_safety_governor_authorization_and_audit`: PASSED
  - `test_api_governor_and_resource_routes`: PASSED
  - *Result: 8 passed in 13.27s*

- **Agent Task Harness & Skills Suite** (`tests/test_agent_harness_integration.py`):
  - `test_tool_bus_catalog`: PASSED (9/9 tools verified)
  - `test_tool_bus_parameter_bounds_enforcement`: PASSED
  - `test_skill_aero_2d_solve`: PASSED
  - `test_skill_aero_3d_vlm`: PASSED
  - `test_skill_polar_sweep`: PASSED
  - `test_skill_uncertainty_quantify`: PASSED
  - `test_skill_benchmark_verify`: PASSED
  - `test_skill_geometry_parse`: PASSED
  - `test_skill_export_datcom`: PASSED
  - `test_skill_export_shabp`: PASSED
  - `test_skill_mesh_generate`: PASSED
  - `test_task_harness_full_cycle`: PASSED
  - `test_task_harness_kill_switch_interception`: PASSED
  - `test_api_agent_routes`: PASSED
  - *Result: 14 passed in 13.90s*

**Combined Phase 1 Suite**: 22 passed, 0 failed.

---

## 2. Frozen Scientific Benchmark Assertions

- **NACA 0012 Abbott Benchmark**: $\alpha = 4^\circ$, $Re = 3 \times 10^6$, $M = 0.15$:
  - Experimental reference: $C_L = 0.4350$, $C_D = 0.0084$
  - Calculated panel result: $C_L = 0.4843$, $C_D = 0.00919$ (within verified tolerance)
- **Anti-Fabrication Invariants**:
  - Drag non-negativity: $C_D > 0$ strictly preserved
  - Epistemic integrity: Planned != Staged != Executed != Verified
