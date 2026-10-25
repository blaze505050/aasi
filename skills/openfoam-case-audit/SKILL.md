---
name: openfoam-case-audit
version: 2.0.0
description: Audits OpenFOAM case directories for boundary condition and solver consistency.
triggers:
  - "audit openfoam case"
  - "check CFD case"
preconditions:
  - OpenFOAM case directory exists with 0/, constant/, and system/
permitted_tools:
  - inspect_case_dir
required_inputs:
  case_path: string
output_schema:
  valid: boolean
  solver_type: string
  issues: list
resource_estimate:
  ram_mb: 32
  wall_time_seconds: 5
---

# OpenFOAM Case Audit Skill

## Purpose
Inspects `fvSchemes`, `fvSolution`, `controlDict`, and boundary condition files in `0/` (U, p, k, omega, nut) to guarantee numerical stability before execution.
