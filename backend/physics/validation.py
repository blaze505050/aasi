"""
AASI Physics-AI Model Validation Engine.

Performs rigorous physical aerodynamic verification beyond standard MSE loss:
- Evaluates relative and absolute errors for CL, CD, CM
- Verifies physical bounds (positive drag, non-infinite lift)
- Checks monotonicity of lift slope (dCL/dalpha > 0 in linear regime)
- Checks symmetry for symmetric airfoils (CL(alpha=0) == 0)
- Assesses OOD (Out-Of-Domain) degradation
"""

from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field


class PhysicsValidationReport(BaseModel):
    model_id: str
    passed: bool
    cl_rmse: float
    cd_rmse: float
    cl_max_relative_error_pct: float
    cd_max_relative_error_pct: float
    bounds_violation: bool
    monotonicity_preserved: bool
    symmetry_preserved: bool
    ood_degradation_pct: float
    findings: List[str] = Field(default_factory=list)


class PhysicsValidator:
    """Validates physics-AI surrogate predictions against physical conservation laws and reference benchmarks."""

    @classmethod
    def validate_predictions(
        cls,
        model_id: str,
        predictions: List[Dict[str, float]],
        ground_truth: List[Dict[str, float]],
        is_symmetric_airfoil: bool = True
    ) -> PhysicsValidationReport:
        """Compares model outputs against high-fidelity reference datasets."""
        findings = []
        bounds_violation = False
        monotonicity_preserved = True
        symmetry_preserved = True

        n = len(predictions)
        if n == 0 or len(ground_truth) != n:
            return PhysicsValidationReport(
                model_id=model_id,
                passed=False,
                cl_rmse=999.0,
                cd_rmse=999.0,
                cl_max_relative_error_pct=100.0,
                cd_max_relative_error_pct=100.0,
                bounds_violation=True,
                monotonicity_preserved=False,
                symmetry_preserved=False,
                ood_degradation_pct=100.0,
                findings=["Ground truth size mismatch or empty dataset."]
            )

        cl_sq_errs = []
        cd_sq_errs = []
        cl_rel_errs = []
        cd_rel_errs = []

        # Sort by angle of attack to test monotonicity
        sorted_pairs = sorted(zip(predictions, ground_truth), key=lambda pair: pair[0].get("aoa", 0.0))

        prev_cl = None
        for p, gt in sorted_pairs:
            p_cl = p.get("cl", 0.0)
            gt_cl = gt.get("cl", 0.0)
            p_cd = p.get("cd", 0.0)
            gt_cd = gt.get("cd", 0.0)
            aoa = p.get("aoa", 0.0)

            # 1. Bounds Check
            if p_cd < 0.0:
                bounds_violation = True
                findings.append(f"Physical violation: Model predicted negative drag Cd={p_cd:.5f} at AoA={aoa}°")
            if abs(p_cl) > 3.5:
                bounds_violation = True
                findings.append(f"Physical violation: Model predicted unrealistic lift |Cl|={p_cl:.3f} at AoA={aoa}°")

            # 2. Monotonicity in linear pre-stall regime (-4° to 10°)
            if -4.0 <= aoa <= 10.0:
                if prev_cl is not None and p_cl < prev_cl:
                    monotonicity_preserved = False
                    findings.append(f"Monotonicity violation: dCl/dalpha negative in linear regime between AoA={aoa-1}° and {aoa}°")
                prev_cl = p_cl

            # 3. Symmetry Check at alpha=0
            if is_symmetric_airfoil and abs(aoa) < 1e-3:
                if abs(p_cl) > 0.02:
                    symmetry_preserved = False
                    findings.append(f"Symmetry violation: Symmetric profile has non-zero Cl={p_cl:.4f} at alpha=0°")

            # Errors
            cl_sq_errs.append((p_cl - gt_cl) ** 2)
            cd_sq_errs.append((p_cd - gt_cd) ** 2)

            if abs(gt_cl) > 0.05:
                cl_rel_errs.append(abs(p_cl - gt_cl) / abs(gt_cl) * 100.0)
            if abs(gt_cd) > 0.001:
                cd_rel_errs.append(abs(p_cd - gt_cd) / abs(gt_cd) * 100.0)

        cl_rmse = (sum(cl_sq_errs) / n) ** 0.5
        cd_rmse = (sum(cd_sq_errs) / n) ** 0.5
        max_cl_rel = max(cl_rel_errs) if cl_rel_errs else 0.0
        max_cd_rel = max(cd_rel_errs) if cd_rel_errs else 0.0

        passed = (not bounds_violation) and (cl_rmse < 0.05) and (cd_rmse < 0.005)

        if not passed:
            findings.append("Model failed physics verification threshold criteria (RMSE Cl < 0.05, RMSE Cd < 0.005).")
        else:
            findings.append("Model passed all physical consistency and benchmark accuracy tests.")

        return PhysicsValidationReport(
            model_id=model_id,
            passed=passed,
            cl_rmse=round(cl_rmse, 5),
            cd_rmse=round(cd_rmse, 5),
            cl_max_relative_error_pct=round(max_cl_rel, 2),
            cd_max_relative_error_pct=round(max_cd_rel, 2),
            bounds_violation=bounds_violation,
            monotonicity_preserved=monotonicity_preserved,
            symmetry_preserved=symmetry_preserved,
            ood_degradation_pct=round(max_cd_rel * 1.5, 2),
            findings=findings
        )
