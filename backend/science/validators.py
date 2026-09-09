"""Validation engine for dimensional consistency, boundary envelopes, convergence criteria, and provenance checksums."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple
from backend.tools.units import unit_registry


class ScientificValidationEngine:
    """Rigorous scientific validator enforcing dimensional, physical, and convergence gates."""

    # Physical valid domain limits
    PHYSICAL_LIMITS = {
        "mach": (0.0, 30.0),
        "reynolds": (1.0, 1e10),
        "aoa_deg": (-180.0, 180.0),
        "temperature_k": (2.7, 5000.0),
        "pressure_pa": (0.0, 1e8),
        "altitude_km": (0.0, 100000.0),
        "cd": (0.0001, 5.0),
        "cl": (-5.0, 5.0),
        "cm": (-2.0, 2.0),
    }

    def validate_dimensions(self, quantity: str, unit_str: str) -> Tuple[bool, str]:
        """Verify that unit matches expected physical dimensionality."""
        try:
            u = unit_registry.parse_unit(unit_str)
            if quantity.upper() in ["CD", "CL", "CM", "CP", "MACH"]:
                # Must be dimensionless
                if u.dimensionless:
                    return True, "Dimensionless valid"
                return False, f"Expected dimensionless for {quantity}, got dimension '{u.dimensionality}'"
            elif quantity.upper() in ["VELOCITY", "ORBITAL_VELOCITY", "ESCAPE_VELOCITY", "DELTA_V"]:
                if str(u.dimensionality) == "[length] / [time]":
                    return True, "Velocity dimension valid"
                return False, f"Expected [length]/[time] for {quantity}, got '{u.dimensionality}'"
            elif quantity.upper() in ["ALTITUDE", "LENGTH", "CHORD"]:
                if str(u.dimensionality) == "[length]":
                    return True, "Length dimension valid"
                return False, f"Expected [length] for {quantity}, got '{u.dimensionality}'"
            return True, "Unit recognized"
        except Exception as err:
            return False, f"Unit parse error: {str(err)}"

    def validate_range(self, param_name: str, value: float) -> Tuple[bool, str]:
        """Verify value lies within physical laws of aerodynamics and thermodynamics."""
        key = param_name.lower()
        if key in self.PHYSICAL_LIMITS:
            min_val, max_val = self.PHYSICAL_LIMITS[key]
            if value < min_val or value > max_val:
                return False, f"Value {value} for '{param_name}' exceeds physical bounds [{min_val}, {max_val}]"
            return True, "Within physical limits"
        return True, "No limit defined"

    def validate_cfd_convergence_vs_validation(
        self,
        residuals: Dict[str, float],
        target_residual: float = 1e-5,
        grid_independence_verified: bool = False,
        experimental_comparison_done: bool = False,
    ) -> Dict[str, Any]:
        """CRITICAL PRINCIPLE: Convergence != Validation.

        Convergence means the discrete algebraic equations were solved without numerical instability.
        Validation means the equations model physical reality with documented grid independence and uncertainty.
        """
        max_residual = max(residuals.values()) if residuals else 1.0
        is_converged = max_residual <= target_residual

        # Epistemic determination
        if is_converged and grid_independence_verified and experimental_comparison_done:
            status = "VALIDATED_CFD"
            level = "Level 3 - Validated CFD Benchmark"
        elif is_converged:
            status = "LOCAL_CFD"
            level = "Level 6 - Converged Local CFD (Uncalibrated against experiments)"
        else:
            status = "UNVALIDATED_CFD"
            level = "Unconverged Simulation"

        return {
            "is_converged": is_converged,
            "max_residual": max_residual,
            "target_residual": target_residual,
            "grid_independence_verified": grid_independence_verified,
            "experimental_comparison_done": experimental_comparison_done,
            "status": status,
            "level": level,
            "scientific_advisory": (
                "Numerical convergence achieved. Note: Convergence alone does not guarantee physical validation. "
                "Grid independence studies and experimental calibration are mandatory for design sign-off."
                if is_converged and not experimental_comparison_done
                else "Fully validated CFD benchmark with documented experimental calibration."
                if is_converged
                else "Warning: Simulation residuals did not reach target threshold."
            ),
        }

    def verify_checksum(self, data_str: str, expected_hash: str) -> bool:
        """Verify SHA-256 integrity of scientific dataset."""
        calculated = hashlib.sha256(data_str.encode("utf-8")).hexdigest()
        return calculated.lower() == expected_hash.lower()
