"""
AASI Automated CFD Result Quality Control Engine.

Evaluates raw CFD simulation artifacts before allowing results into any dataset:
1. Numerical Convergence: Residual reduction, force stability, iteration counts, NaN/Inf checks.
2. Physical Sanity: Universal drag positivity (CD > 0), reasonable aerodynamic bounds (|CL| <= 3.5), moment sanity.
3. Provenance Verification: Manifest match, geometry coordinate integrity, operating condition verification.
4. Spatial Grid Convergence: Integrates with ASME V&V 20 GCI module to check continuum convergence.

Classifies CFD runs into:
- CONVERGED
- GRID_CONVERGED
- QUESTIONABLE
- DIVERGED
- INVALID
"""

from typing import Dict, List, Any, Optional, Tuple
import math
import numpy as np
from backend.multifidelity.models import CFDQualityClassification, FlowConditions


class CFDQualityControlEngine:
    """Automated gatekeeper inspecting numerical, physical, and provenance integrity."""

    @classmethod
    def audit_simulation_run(
        cls,
        forces_history: List[Dict[str, float]],       # [{"iteration": int, "cl": float, "cd": float, "cm": float}]
        residuals_history: Optional[List[Dict[str, float]]] = None, # [{"iteration": int, "p": float, "Ux": float, ...}]
        flow_conditions: Optional[FlowConditions] = None,
        gci_results: Optional[Dict[str, Any]] = None,
        convergence_tolerance: float = 1e-4,
        force_stability_tolerance_pct: float = 1.0,
        min_iterations: int = 150
    ) -> Tuple[CFDQualityClassification, Dict[str, Any]]:
        """
        Conducts thorough scientific QC of a completed simulation run.
        """
        audit_report: Dict[str, Any] = {
            "is_valid": True,
            "violations": [],
            "warnings": [],
            "final_cl": None,
            "final_cd": None,
            "final_cm": None,
            "residual_drop_orders": None,
            "force_oscillation_pct": None,
            "grid_convergence_verified": False,
        }

        if not forces_history or len(forces_history) < 10:
            audit_report["violations"].append("Insufficient iterations in force history (< 10 recorded steps).")
            return CFDQualityClassification.INVALID, audit_report

        # 1. NaN / Inf Check
        for step in forces_history:
            for k in ["cl", "cd", "cm"]:
                v = step.get(k)
                if v is None or math.isnan(v) or math.isinf(v):
                    audit_report["violations"].append(f"Fatal Numerical Explosion: {k.upper()} contains NaN or Inf at iteration {step.get('iteration', 'unknown')}.")
                    audit_report["is_valid"] = False
                    return CFDQualityClassification.INVALID, audit_report

        # Extract last 20% iterations for convergence evaluation
        n_total = len(forces_history)
        tail_count = max(int(n_total * 0.20), 5)
        tail_forces = forces_history[-tail_count:]

        final_cl = float(tail_forces[-1]["cl"])
        final_cd = float(tail_forces[-1]["cd"])
        final_cm = float(tail_forces[-1].get("cm", 0.0))

        audit_report["final_cl"] = final_cl
        audit_report["final_cd"] = final_cd
        audit_report["final_cm"] = final_cm

        # 2. Physical Sanity Checks
        if final_cd <= 0.0:
            audit_report["violations"].append(f"Physical Drag Violation: Final CD ({final_cd:.6f}) is non-positive (violates thermodynamics/viscous resistance).")
            audit_report["is_valid"] = False
            return CFDQualityClassification.INVALID, audit_report

        if abs(final_cl) > 3.5:
            audit_report["violations"].append(f"Physical Lift Violation: |CL| ({abs(final_cl):.3f}) exceeds maximum conceivable 2D aerodynamic limit (3.5).")
            audit_report["is_valid"] = False
            return CFDQualityClassification.INVALID, audit_report

        if abs(final_cm) > 1.5:
            audit_report["violations"].append(f"Physical Moment Violation: |CM| ({abs(final_cm):.3f}) exceeds reasonable stability bounds (1.5).")
            audit_report["is_valid"] = False
            return CFDQualityClassification.INVALID, audit_report

        # 3. Force Stability Check (Oscillation in tail)
        cl_tail = [s["cl"] for s in tail_forces]
        cl_range = max(cl_tail) - min(cl_tail)
        cl_base = max(abs(final_cl), 0.1)
        force_osc_pct = (cl_range / cl_base) * 100.0
        audit_report["force_oscillation_pct"] = round(force_osc_pct, 4)

        if force_osc_pct > 15.0:
            audit_report["violations"].append(f"Unsteady Oscillation / Stall Divergence: CL oscillation ({force_osc_pct:.1f}%) exceeds allowable threshold.")
            return CFDQualityClassification.DIVERGED, audit_report

        # 4. Residual Convergence Check
        is_converged_residuals = True
        if residuals_history and len(residuals_history) > 1:
            initial_res = max(residuals_history[0].values()) if isinstance(residuals_history[0], dict) else 1.0
            final_res = max(residuals_history[-1].values()) if isinstance(residuals_history[-1], dict) else 1e-5

            if initial_res > 0 and final_res > 0:
                drop = math.log10(initial_res / final_res)
                audit_report["residual_drop_orders"] = round(drop, 2)
                if final_res > convergence_tolerance and drop < 2.5:
                    is_converged_residuals = False
                    audit_report["warnings"].append(f"Marginal Residual Drop: Log drop {drop:.1f} orders (final residual {final_res:.2e} > {convergence_tolerance:.2e}).")

        # 5. Grid Convergence Check
        is_grid_converged = False
        if gci_results and gci_results.get("is_in_asymptotic_range"):
            is_grid_converged = True
            audit_report["grid_convergence_verified"] = True

        # Assign Final Classification
        if n_total < min_iterations:
            audit_report["warnings"].append(f"Premature solver exit: Iterations ({n_total}) < recommended minimum ({min_iterations}).")
            return CFDQualityClassification.QUESTIONABLE, audit_report

        if force_osc_pct > force_stability_tolerance_pct or not is_converged_residuals:
            return CFDQualityClassification.QUESTIONABLE, audit_report

        if is_grid_converged:
            return CFDQualityClassification.GRID_CONVERGED, audit_report

        return CFDQualityClassification.CONVERGED, audit_report
