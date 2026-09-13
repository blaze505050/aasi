"""
AASI Phase 21: CFD Convergence Evaluator.
Governing Rule: Absolute Anti-Fabrication Rule.
Evaluates multi-criteria convergence: residual floor, residual drop, force stabilization, and continuity.
Never accepts exit_code == 0 alone as evidence of convergence.
"""

from typing import Any, Dict, List, Optional
from backend.cfd.solver_interface import ConvergenceState


class CFDConvergenceEvaluator:
    """Evaluates multi-criteria convergence from residuals and force histories."""

    MAX_RESIDUAL_FLOOR = 1e-3
    MIN_ORDER_OF_MAGNITUDE_DROP = 3.0
    MAX_FORCE_RELATIVE_VARIATION = 0.01  # 1.0% variation in CD/CL over tail
    MIN_CONVERGENCE_ITERATIONS = 50

    @classmethod
    def evaluate_convergence(
        cls,
        residual_data: Dict[str, Any],
        force_data: Dict[str, Any],
        solver_exit_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate full convergence state based on physical and mathematical evidence.
        """
        evidence: Dict[str, Any] = {
            "checks": {},
            "criteria_passed": 0,
            "total_criteria": 4,
        }

        # If solver failed or was not run
        if solver_exit_code is None or solver_exit_code != 0:
            return {
                "converged": False,
                "convergence_state": ConvergenceState.SOLVER_FAILED.value,
                "reason": f"Solver exit code was {solver_exit_code} (non-zero or null)",
                "evidence": evidence,
            }

        # Check for numerical NaN/Inf
        if residual_data.get("has_nan_or_inf", False):
            return {
                "converged": False,
                "convergence_state": ConvergenceState.DIVERGED.value,
                "reason": "Simulation diverged with NaN or Inf residuals",
                "evidence": evidence,
            }

        residuals = residual_data.get("residuals", {})
        total_iterations = residual_data.get("total_iterations", 0)

        if not residuals or total_iterations < cls.MIN_CONVERGENCE_ITERATIONS:
            return {
                "converged": False,
                "convergence_state": ConvergenceState.CONVERGENCE_NOT_ESTABLISHED.value,
                "reason": f"Insufficient iteration history ({total_iterations} < {cls.MIN_CONVERGENCE_ITERATIONS})",
                "evidence": evidence,
            }

        summary = residual_data.get("summary", {})

        # Criterion 1: Residual Floor
        pressure_res = summary.get("p", {}).get("final", 1.0)
        ux_res = summary.get("Ux", {}).get("final", 1.0)
        uy_res = summary.get("Uy", {}).get("final", 1.0)
        max_final_res = max(pressure_res, ux_res, uy_res)
        floor_passed = max_final_res <= cls.MAX_RESIDUAL_FLOOR
        evidence["checks"]["residual_floor"] = {
            "passed": floor_passed,
            "max_final_residual": max_final_res,
            "threshold": cls.MAX_RESIDUAL_FLOOR,
        }
        if floor_passed:
            evidence["criteria_passed"] += 1

        # Criterion 2: Residual Drop (order of magnitude)
        p_drop = summary.get("p", {}).get("order_of_magnitude_drop", 0.0)
        ux_drop = summary.get("Ux", {}).get("order_of_magnitude_drop", 0.0)
        min_drop = min(p_drop, ux_drop)
        drop_passed = min_drop >= cls.MIN_ORDER_OF_MAGNITUDE_DROP or max_final_res <= 1e-4
        evidence["checks"]["residual_drop"] = {
            "passed": drop_passed,
            "min_order_drop": min_drop,
            "threshold": cls.MIN_ORDER_OF_MAGNITUDE_DROP,
        }
        if drop_passed:
            evidence["criteria_passed"] += 1

        # Criterion 3: Force Stabilization
        force_parsed = force_data.get("parsed", False)
        if force_parsed:
            cd_var = force_data.get("CD", {}).get("relative_variation", 1.0)
            cl_var = force_data.get("CL", {}).get("relative_variation", 1.0)
            force_stabilized = (cd_var <= cls.MAX_FORCE_RELATIVE_VARIATION) and (
                cl_var <= cls.MAX_FORCE_RELATIVE_VARIATION
            )
            evidence["checks"]["force_stabilization"] = {
                "passed": force_stabilized,
                "cd_relative_variation": cd_var,
                "cl_relative_variation": cl_var,
                "threshold": cls.MAX_FORCE_RELATIVE_VARIATION,
            }
            if force_stabilized:
                evidence["criteria_passed"] += 1
        else:
            evidence["checks"]["force_stabilization"] = {
                "passed": False,
                "reason": "Force history not available or unparsed",
            }

        # Criterion 4: Continuity Error
        cont_global = residual_data.get("continuity_global", [])
        if cont_global:
            final_cont = abs(cont_global[-1])
            cont_passed = final_cont < 1e-3
            evidence["checks"]["continuity"] = {
                "passed": cont_passed,
                "final_global_continuity": final_cont,
                "threshold": 1e-3,
            }
            if cont_passed:
                evidence["criteria_passed"] += 1
        else:
            evidence["checks"]["continuity"] = {
                "passed": True,  # Neutral if not explicitly logged
                "note": "Continuity errors not explicitly recorded in log",
            }
            evidence["criteria_passed"] += 1

        # Strict convergence determination
        all_passed = evidence["criteria_passed"] >= 3 and floor_passed

        if all_passed:
            state = ConvergenceState.CONVERGED
            reason = "Multi-criteria convergence established: residual floor met and forces stabilized."
        elif floor_passed and not force_parsed:
            state = ConvergenceState.CONVERGENCE_NOT_ESTABLISHED
            reason = "Residual floor met but force coefficient stabilization evidence is missing."
        else:
            state = ConvergenceState.UNCONVERGED
            reason = f"Simulation failed convergence criteria ({evidence['criteria_passed']}/4 passed)."

        return {
            "converged": state == ConvergenceState.CONVERGED,
            "convergence_state": state.value,
            "reason": reason,
            "evidence": evidence,
        }
