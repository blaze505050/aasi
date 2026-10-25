---
name: colab-package-generation
version: 2.0.0
description: Bundles high-compute simulation cases into reproducible Colab execution archives.
triggers:
  - "generate colab package"
  - "prepare remote simulation bundle"
preconditions:
  - Valid case directory and execution parameters available
permitted_tools:
  - package_archiver
required_inputs:
  case_name: string
  solver_command: string
output_schema:
  bundle_path: string
  sha256_checksum: string
  manifest: dict
resource_estimate:
  ram_mb: 64
  wall_time_seconds: 15
---

# Colab Package Generation Skill

## Purpose
Packages mesh definitions, OpenFOAM configurations, Python verification scripts, and a self-contained execution Jupyter Notebook into a signed ZIP archive for execution on Google Colab or external HPC.
