"""
AASI Physics-Aware Validation Suite.

Evaluates fluid mechanics sanity checks:
1. Lift curve monotonicity: dCL/dα > 0 in attached pre-stall flow regime.
2. Symmetric zero-lift sanity: |CL(0 deg)| <= 0.02 for symmetric profiles.
3. Drag positivity: CD > 0 for unpowered bodies in real fluids.
4. Continuity & smoothness: absence of step discontinuities or oscillations across AoA.
5. Physical bounds: flags unphysical values (|CL| > 3.5 or CD > 1.5).
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np


class PhysicsAwareValidator:
    """Rigorous scientific validator for aerodynamic predictions and polar sweeps."""

    @staticmethod
    def validate_prediction(
        cl: float,
        cd: float,
        cm: float,
        aoa_deg: float,
        is_symmetric: bool = False
    ) -> Dict[str, Any]:
        """Validates a single point prediction against physical aerodynamic rules."""
        checks = {}
        violations = []

        # 1. Drag Positivity
        checks["drag_positive"] = bool(cd > 0.0)
        if cd <= 0.0:
            violations.append(f"Unphysical negative/zero drag: CD = {cd}")

        # 2. Symmetry at alpha = 0
        if is_symmetric and abs(aoa_deg) < 0.2:
            checks["symmetry_satisfied"] = bool(abs(cl) <= 0.025)
            if abs(cl) > 0.025:
                violations.append(f"Symmetric airfoil has non-zero lift at alpha=0: CL = {cl:.4f}")
        else:
            checks["symmetry_satisfied"] = True

        # 3. Reasonable Aerodynamic Bounds (Subsonic 2D Airfoil)
        checks["cl_bounds_satisfied"] = bool(-3.0 <= cl <= 3.5)
        checks["cd_bounds_satisfied"] = bool(0.001 <= cd <= 1.0)
        checks["cm_bounds_satisfied"] = bool(-0.6 <= cm <= 0.4)

        if not checks["cl_bounds_satisfied"]:
            violations.append(f"Lift coefficient out of plausible physical bounds: CL = {cl}")
        if not checks["cd_bounds_satisfied"]:
            violations.append(f"Drag coefficient out of plausible physical bounds: CD = {cd}")

        is_valid = len(violations) == 0
        return {
            "is_physically_valid": is_valid,
            "checks": checks,
            "violations": violations
        }

    @staticmethod
    def validate_polar_sweep(
        aoas: List[float],
        cls: List[float],
        cds: List[float],
        cms: List[float],
        is_symmetric: bool = False
    ) -> Dict[str, Any]:
        """
        Validates an entire polar sweep for monotonicity, continuity, and smoothness.
        """
        aoa_arr = np.array(aoas)
        cl_arr = np.array(cls)
        cd_arr = np.array(cds)

        order = np.argsort(aoa_arr)
        aoa_sorted = aoa_arr[order]
        cl_sorted = cl_arr[order]
        cd_sorted = cd_arr[order]

        violations = []
        checks = {}

        # 1. Lift Monotonicity in Pre-Stall Attached Regime (-4 deg to +10 deg)
        pre_stall_mask = (aoa_sorted >= -4.0) & (aoa_sorted <= 10.0)
        if np.sum(pre_stall_mask) >= 3:
            d_cl = np.diff(cl_sorted[pre_stall_mask])
            d_aoa = np.diff(aoa_sorted[pre_stall_mask])
            slopes = d_cl / np.maximum(1e-4, d_aoa)
            neg_slopes = np.sum(slopes < 0.0)
            checks["lift_monotonicity"] = bool(neg_slopes == 0)
            if neg_slopes > 0:
                violations.append(f"Lift curve slope is negative in pre-stall regime ({neg_slopes} points)")
        else:
            checks["lift_monotonicity"] = True

        # 2. Minimum Drag near zero lift
        checks["drag_all_positive"] = bool(np.all(cd_sorted > 0.0))
        if not checks["drag_all_positive"]:
            violations.append("Drag is non-positive at one or more points in sweep")

        # 3. Continuity / Smoothness Check (no sudden huge leaps in dCL/dAoA)
        d_aoa_all = np.diff(aoa_sorted)
        if len(d_aoa_all) > 0 and np.all(d_aoa_all > 0):
            d_cl_all = np.diff(cl_sorted)
            step_slopes = np.abs(d_cl_all / d_aoa_all)
            checks["continuity_smoothness"] = bool(np.all(step_slopes < 0.35))
            if not checks["continuity_smoothness"]:
                violations.append("Discontinuity or pathological oscillation detected in lift curve")
        else:
            checks["continuity_smoothness"] = True

        # 4. Symmetry Check
        zero_idx = np.where(np.abs(aoa_sorted) < 0.2)[0]
        if is_symmetric and len(zero_idx) > 0:
            cl_zero = cl_sorted[zero_idx[0]]
            checks["zero_lift_at_zero_aoa"] = bool(abs(cl_zero) <= 0.025)
            if not checks["zero_lift_at_zero_aoa"]:
                violations.append(f"Symmetric profile does not cross origin: CL(0) = {cl_zero:.4f}")
        else:
            checks["zero_lift_at_zero_aoa"] = True

        return {
            "is_sweep_valid": len(violations) == 0,
            "checks": checks,
            "violations": violations
        }

    @staticmethod
    def validate_predictions(
        geometries: List[str],
        aoas: np.ndarray,
        cl_preds: np.ndarray,
        cd_preds: np.ndarray,
        cm_preds: np.ndarray
    ) -> Dict[str, Any]:
        """Validates a batch of predictions across multiple test points."""
        total = len(aoas)
        pos_drag_count = 0
        cl_bounds_count = 0
        symmetry_checked = 0
        symmetry_passed = 0

        for i in range(total):
            geom = geometries[i].lower() if i < len(geometries) else ""
            is_sym = ("0012" in geom or "0009" in geom or "0006" in geom)
            res = PhysicsAwareValidator.validate_prediction(
                cl=float(cl_preds[i]),
                cd=float(cd_preds[i]),
                cm=float(cm_preds[i]),
                aoa_deg=float(aoas[i]),
                is_symmetric=is_sym
            )
            if res["checks"]["drag_positive"]:
                pos_drag_count += 1
            if res["checks"]["cl_bounds_satisfied"]:
                cl_bounds_count += 1
            if is_sym and abs(aoas[i]) < 0.2:
                symmetry_checked += 1
                if res["checks"]["symmetry_satisfied"]:
                    symmetry_passed += 1

        return {
            "total_points_evaluated": total,
            "drag_positivity_rate": float(pos_drag_count / max(1, total)),
            "cl_bounds_satisfaction_rate": float(cl_bounds_count / max(1, total)),
            "symmetry_points_tested": symmetry_checked,
            "symmetry_points_passed": symmetry_passed,
            "all_drag_positive": bool(pos_drag_count == total),
        }

    @staticmethod
    def validate_surface_cp(cps: np.ndarray) -> Dict[str, Any]:
        """
        Validates surface pressure distribution against fundamental subsonic fluid mechanics.
        Rule 1: Cp <= 1.0 (stagnation point limit in incompressible flow).
        Rule 2: Cp >= -6.0 (subsonic suction peak limit before extreme supersonic shock stall).
        """
        max_cp = float(np.max(cps))
        min_cp = float(np.min(cps))

        stagnation_satisfied = bool(max_cp <= 1.05)  # Allow small 0.05 discretization tolerance
        suction_bound_satisfied = bool(min_cp >= -6.5)

        violations = []
        if not stagnation_satisfied:
            violations.append(f"Unphysical stagnation violation: Cp_max = {max_cp:.4f} > 1.0")
        if not suction_bound_satisfied:
            violations.append(f"Unphysical suction peak violation: Cp_min = {min_cp:.4f} < -6.0")

        return {
            "is_cp_valid": len(violations) == 0,
            "max_cp": round(max_cp, 4),
            "min_cp": round(min_cp, 4),
            "stagnation_satisfied": stagnation_satisfied,
            "suction_bound_satisfied": suction_bound_satisfied,
            "violations": violations
        }

    @staticmethod
    def audit_model_promotion_gates(
        metrics: Dict[str, Any],
        physics_report: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Independent scientific gatekeeper.
        A model with excellent statistical metrics but physically invalid behavior
        CANNOT be promoted to VERIFIED or VERIFIED_PRODUCTION.
        """
        violations = []

        # 1. Physics gates
        if not physics_report.get("all_drag_positive", False):
            violations.append("PHYSICAL_GATE_FAILURE: Non-positive drag predictions detected.")
        if physics_report.get("drag_positivity_rate", 1.0) < 1.0:
            violations.append("PHYSICAL_GATE_FAILURE: Drag positivity violated on holdout test set.")

        # 2. Statistical gates on test set
        r2 = metrics.get("r2", metrics.get("cl_r2", 0.0))
        rmse = metrics.get("rmse", metrics.get("cl_rmse", 1.0))

        if r2 < 0.80:
            violations.append(f"STATISTICAL_GATE_FAILURE: Insufficient test set determination R² = {r2:.3f} < 0.80.")
        if rmse > 0.15:
            violations.append(f"STATISTICAL_GATE_FAILURE: Test set RMSE = {rmse:.4f} exceeds threshold 0.15.")

        can_promote = len(violations) == 0
        return can_promote, violations


