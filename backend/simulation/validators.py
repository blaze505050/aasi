"""Validation checks for case dictionaries, boundary definitions, and mesh sanity."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from .models import SimulationCase


class SimulationCaseValidator:
    """Pre-flight validator checking boundary conditions, mesh specs, and physical parameters."""

    def validate_case(self, case: SimulationCase) -> Tuple[bool, List[str]]:
        """Run pre-flight consistency checks on case parameters."""
        errors: List[str] = []

        # 1. Mach bounds
        if case.mach < 0.0 or case.mach > 25.0:
            errors.append(f"Mach number {case.mach} outside physical bounds [0, 25]")

        # 2. Reynolds number bounds
        if case.reynolds <= 0.0 or case.reynolds > 1e9:
            errors.append(f"Reynolds number {case.reynolds} must be positive and <= 1e9")

        # 3. Angle of attack bounds
        if case.aoa_deg < -90.0 or case.aoa_deg > 90.0:
            errors.append(f"Angle of attack {case.aoa_deg}° outside nominal range [-90, 90]")

        # 4. Mesh cells
        if case.mesh_cells < 100 or case.mesh_cells > 100_000_000:
            errors.append(f"Mesh cells {case.mesh_cells} outside valid range [100, 100M]")

        # 5. Turbulence model validation
        valid_turb = ["k-omega SST", "Spalart-Allmaras", "k-epsilon", "laminar", "LES"]
        if case.turbulence_model not in valid_turb:
            errors.append(f"Turbulence model '{case.turbulence_model}' not supported. Choose from {valid_turb}")

        is_valid = len(errors) == 0
        return is_valid, errors
