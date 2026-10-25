---
name: scientific-unit-validation
version: 2.0.0
description: Validates dimensional consistency and converts engineering units.
triggers:
  - "validate units"
  - "convert units"
preconditions:
  - Numerical value and source/target unit symbols provided
permitted_tools:
  - unit_converter
  - dimensional_analysis
required_inputs:
  value: float
  source_unit: string
  target_unit: string
output_schema:
  converted_value: float
  dimensions_match: boolean
resource_estimate:
  ram_mb: 16
  wall_time_seconds: 2
---

# Scientific Unit Validation Skill

## Purpose
Ensures strict SI dimensional consistency across all computational parameters (e.g. pressure in Pa, velocity in m/s, angles in radians or degrees) according to standard aerospace conventions.
