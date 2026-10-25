---
name: result-archive-verification
version: 2.0.0
description: Validates cryptographic hashes, residuals, and physical outputs of returned simulations.
triggers:
  - "verify simulation archive"
  - "ingest remote results"
preconditions:
  - Returned result archive and expected input manifest available
permitted_tools:
  - archive_verifier
  - residual_checker
required_inputs:
  archive_path: string
  expected_manifest_hash: string
output_schema:
  verified: boolean
  force_coefficients: dict
  residuals_converged: boolean
resource_estimate:
  ram_mb: 64
  wall_time_seconds: 10
---

# Result Archive Verification Skill

## Purpose
Enforces the fail-closed verification boundary upon ingesting remote simulation results. Rejects tampered archives, diverged residuals, or missing force integration histories.
