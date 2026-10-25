---
name: regression-test-repair
version: 2.0.0
description: Automated diagnosis and non-destructive repair of failing regression tests preserving physical truth.
triggers:
  - "repair failing test"
  - "diagnose test regression"
  - "fix test suite"
preconditions:
  - Pytest failure trace and source test file available
permitted_tools:
  - inspect_ast
required_inputs:
  test_name: string
  traceback: string
  test_file_path: string
output_schema:
  root_cause: string
  repair_strategy: string
  patch_diff: string
  invariants_preserved: boolean
resource_estimate:
  ram_mb: 48
  wall_time_seconds: 8
---

# Regression Test Repair Skill

## Purpose
Systematically diagnoses failing tests in the AASI continuous integration and verification pipelines. Implements surgical corrections for interface drift, dependency deprecations, or platform-specific quirks (e.g. Windows file locking or path separators) without weakening scientific assertions.

## Execution Procedure
1. Parse Pytest failure output, separating:
   - Numerical tolerance mismatches
   - Assertion failures on physical invariants ($C_D \ge 0$)
   - Environment / import errors
   - Schema / Pydantic V2 migration differences
2. Verify that the failing test is not an intentional negative test (e.g., verifying that non-convergent CFD or unphysical airfoils fail closed).
3. If the test asserts a physical ground truth, verify whether the underlying solver implementation drifted or if the test tolerance was inappropriately narrow for numerical precision.
4. Draft a minimal diff fixing the issue.
5. Re-run test isolated via `pytest -k <test_name>` and verify that full regression suite remains green.

## Anti-Fabrication Invariants
- NEVER loosen or delete physical assertion checks ($C_D \ge 0$, finite lift slope, positive energy) to make a test pass.
- NEVER convert a `FAILED` CFD verification test to `PASSED` without actual solver convergence and residual criteria satisfaction.
