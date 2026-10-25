---
name: openfoam-failure-diagnosis
version: 2.0.0
description: Parses solver logs for divergence, Courant number explosion, or non-convergence.
triggers:
  - "diagnose openfoam failure"
  - "parse solver log"
preconditions:
  - Solver log text available
permitted_tools:
  - log_parser
required_inputs:
  log_text: string
output_schema:
  diverged: boolean
  failure_mode: string
  recommended_fix: string
resource_estimate:
  ram_mb: 32
  wall_time_seconds: 5
---

# OpenFOAM Failure Diagnosis Skill

## Purpose
Identifies root causes of CFD run failures: CFL violations, pressure-velocity decoupling, mesh non-orthogonality errors, or linear solver max-iteration stalls.
