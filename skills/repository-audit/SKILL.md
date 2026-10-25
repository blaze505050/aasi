---
name: repository-audit
version: 2.0.0
description: Audits codebase structure, entry points, dependencies, and test status.
triggers:
  - "audit repository"
  - "inspect codebase"
preconditions:
  - Repository workspace root accessible
permitted_tools:
  - inspect_workspace
  - list_permitted_files
required_inputs:
  workspace_path: string
output_schema:
  files_indexed: integer
  modules_detected: list
  test_status: string
resource_estimate:
  ram_mb: 64
  wall_time_seconds: 15
---

# Repository Audit Skill

## Purpose
Inspects repository architecture, catalogs API routers, verifies test suite health, and flags architectural regressions.

## Validation Steps
1. Scan directory structure and verify core packages (`backend/`, `runner/`, `tests/`, `frontend/`).
2. Verify package configuration manifests (`requirements.txt`, `package.json`).
3. Execute dry-run test discovery without modifying source files.
