---
name: aerospace-literature-review
version: 2.0.0
description: Searches and synthesizes verified aerospace publications and reference datasets.
triggers:
  - "literature review"
  - "find reference polar"
preconditions:
  - Subject geometry and flight regime specified
permitted_tools:
  - scientific_memory_search
  - dataset_catalog_query
required_inputs:
  topic: string
output_schema:
  citations: list
  reference_data_points: list
  epistemic_sources: list
resource_estimate:
  ram_mb: 64
  wall_time_seconds: 10
---

# Aerospace Literature Review Skill

## Purpose
Retrieves authoritative aerodynamic benchmarks (NASA TM-4083, Abbott & von Doenhoff, AGARD AR-138) and correlates published experimental data with computational investigations.
