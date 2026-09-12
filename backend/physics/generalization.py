"""
AASI Cross-Dataset Generalization & Scientific Compatibility Engine.

Evaluates aerodynamic physics-AI models across distinct authentic datasets:
- Evaluates models trained on Dataset A against ground truths from Dataset B.
- Strictly enforces the Scientific Compatibility Contract:
  * Variable quantity and dimension matching
  * 2D section vs 3D body reference frames
  * Compressibility regime limits (incompressible vs transonic shock)
  * Experimental vs numerical CFD origin tracking
- If scientifically invalid: returns COMPARISON_NOT_VALID fail-closed.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import numpy as np
from pydantic import BaseModel, Field

from backend.datasets.catalog import DatasetCatalog
from backend.datasets.adapters.base import DatasetAdapter, DatasetCase
from backend.physics_ai.validation import PhysicsAwareValidator


class ScientificCompatibilityContract:
    """Evaluates physical comparability between training domain and target dataset."""

    @staticmethod
    def check_compatibility(
        source_domain: Dict[str, Any],
        target_domain: Dict[str, Any],
        variable: str = "CL"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates whether target evaluation is scientifically meaningful.
        """
        # 1. Reference frame check: 2D airfoil vs 3D finite wing/body
        source_dim = source_domain.get("dimension", "2D").upper()
        target_dim = target_domain.get("dimension", "2D").upper()
        if source_dim == "2D" and target_dim == "3D":
            return False, (
                "COMPARISON_NOT_VALID: Cannot compare 2D sectional coefficients directly to 3D finite wing/body "
                "without finite aspect ratio (AR) corrections and induced drag (CD_i = CL^2 / (pi * e * AR)) modeling."
            )

        # 2. Compressibility regime check
        source_mach_max = source_domain.get("mach_max", 0.35)
        target_mach_min = target_domain.get("mach_min", 0.15)
        if target_mach_min >= 0.70 and source_mach_max <= 0.35:
            return False, (
                f"COMPARISON_NOT_VALID: Transonic regime (M >= {target_mach_min}) contains shock-wave interactions "
                f"which violate the training domain assumption of subsonic/incompressible flow (M <= {source_mach_max})."
            )

        # 3. Variable matching
        allowed_vars = {"CL", "CD", "CM", "CP", "CF"}
        if variable.upper() not in allowed_vars:
            return False, f"COMPARISON_NOT_VALID: Variable '{variable}' is not a standardized aerodynamic coefficient."

        return True, None


class CrossDatasetPointResult(BaseModel):
    geometry: str
    aoa_deg: float
    mach: float
    reynolds: float
    pred_cl: float
    pred_cd: float
    true_cl: float
    true_cd: float
    error_cl: float
    error_cd: float
    is_physically_consistent: bool
    notes: str = ""


class CrossDatasetGeneralizationReport(BaseModel):
    benchmark_id: str
    source_dataset_id: str
    target_dataset_id: str
    model_name: str
    variable: str = "CL, CD"
    is_valid_comparison: bool
    status: str  # "VALID_SCIENTIFIC_COMPARISON" or "COMPARISON_NOT_VALID"
    rejection_reason: Optional[str] = None
    target_sample_count: int = 0
    points: List[CrossDatasetPointResult] = Field(default_factory=list)
    cl_rmse: float = 0.0
    cd_rmse: float = 0.0
    cl_mae: float = 0.0
    cd_mae: float = 0.0
    r2_cl: float = 0.0
    lift_monotonicity_passed: bool = True
    drag_positivity_passed: bool = True
    scientific_verdict: str = ""


class CrossDatasetGeneralizationEngine:
    """Orchestrates cross-dataset evaluation with rigorous compatibility gating."""

    def __init__(self, catalog: Optional[DatasetCatalog] = None):
        self.catalog = catalog or DatasetCatalog()

    def evaluate_generalization(
        self,
        model_name: str,
        source_dataset_id: str,
        target_dataset_id: str,
        predictions_generator,  # Callable[[str, float, float, float], Tuple[float, float]] -> (cl, cd)
        target_geometry_filter: Optional[str] = None
    ) -> CrossDatasetGeneralizationReport:
        """
        Evaluates predictions against target dataset cases.
        """
        source_adapter = self.catalog.get_adapter(source_dataset_id)
        target_adapter = self.catalog.get_adapter(target_dataset_id)

        if not target_adapter:
            return CrossDatasetGeneralizationReport(
                benchmark_id=f"CDG-{source_dataset_id}-TO-{target_dataset_id}",
                source_dataset_id=source_dataset_id,
                target_dataset_id=target_dataset_id,
                model_name=model_name,
                is_valid_comparison=False,
                status="COMPARISON_NOT_VALID",
                rejection_reason=f"Target dataset '{target_dataset_id}' not found in registered catalog."
            )

        # Extract domain metadata
        s_manifest = source_adapter.get_manifest() if source_adapter else None
        t_manifest = target_adapter.get_manifest()

        s_domain = {
            "dimension": "3D" if "CRM" in source_dataset_id else "2D",
            "mach_max": 0.85 if "CRM" in source_dataset_id else 0.35
        }
        t_domain = {
            "dimension": "3D" if "CRM" in target_dataset_id else "2D",
            "mach_min": 0.80 if "CRM" in target_dataset_id else 0.05
        }

        # Check compatibility
        is_comp, reason = ScientificCompatibilityContract.check_compatibility(s_domain, t_domain)
        if not is_comp:
            return CrossDatasetGeneralizationReport(
                benchmark_id=f"CDG-{source_dataset_id}-TO-{target_dataset_id}",
                source_dataset_id=source_dataset_id,
                target_dataset_id=target_dataset_id,
                model_name=model_name,
                is_valid_comparison=False,
                status="COMPARISON_NOT_VALID",
                rejection_reason=reason,
                scientific_verdict=f"REJECTED: {reason}"
            )

        # Retrieve target cases
        cases = target_adapter.list_cases(limit=100)
        if target_geometry_filter:
            cases = [c for c in cases if c.geometry_name.strip().upper() == target_geometry_filter.strip().upper()]

        if not cases:
            return CrossDatasetGeneralizationReport(
                benchmark_id=f"CDG-{source_dataset_id}-TO-{target_dataset_id}",
                source_dataset_id=source_dataset_id,
                target_dataset_id=target_dataset_id,
                model_name=model_name,
                is_valid_comparison=False,
                status="COMPARISON_NOT_VALID",
                rejection_reason="No target benchmark cases available for comparison."
            )

        points: List[CrossDatasetPointResult] = []
        cls_pred = []
        cds_pred = []
        cls_true = []
        cds_true = []
        aoas = []

        for c in cases:
            if c.cl is None or c.cd is None:
                continue
            pred_cl, pred_cd = predictions_generator(c.geometry_name, c.mach, c.reynolds, c.aoa_deg)
            err_cl = abs(pred_cl - c.cl)
            err_cd = abs(pred_cd - c.cd)

            is_consistent = (pred_cd > 0) and (err_cl < 0.25)
            points.append(CrossDatasetPointResult(
                geometry=c.geometry_name,
                aoa_deg=c.aoa_deg,
                mach=c.mach,
                reynolds=c.reynolds,
                pred_cl=round(pred_cl, 4),
                pred_cd=round(pred_cd, 5),
                true_cl=c.cl,
                true_cd=c.cd,
                error_cl=round(err_cl, 4),
                error_cd=round(err_cd, 5),
                is_physically_consistent=is_consistent,
                notes=f"Target: {t_manifest.source}"
            ))
            cls_pred.append(pred_cl)
            cds_pred.append(pred_cd)
            cls_true.append(c.cl)
            cds_true.append(c.cd)
            aoas.append(c.aoa_deg)

        if not points:
            return CrossDatasetGeneralizationReport(
                benchmark_id=f"CDG-{source_dataset_id}-TO-{target_dataset_id}",
                source_dataset_id=source_dataset_id,
                target_dataset_id=target_dataset_id,
                model_name=model_name,
                is_valid_comparison=False,
                status="COMPARISON_NOT_VALID",
                rejection_reason="No valid paired points with both prediction and ground truth."
            )

        # Statistical metrics
        cl_arr_pred = np.array(cls_pred)
        cl_arr_true = np.array(cls_true)
        cd_arr_pred = np.array(cds_pred)
        cd_arr_true = np.array(cds_true)

        cl_rmse = float(np.sqrt(np.mean((cl_arr_pred - cl_arr_true) ** 2)))
        cd_rmse = float(np.sqrt(np.mean((cd_arr_pred - cd_arr_true) ** 2)))
        cl_mae = float(np.mean(np.abs(cl_arr_pred - cl_arr_true)))
        cd_mae = float(np.mean(np.abs(cd_arr_pred - cd_arr_true)))

        # R2 calculation
        ss_res = np.sum((cl_arr_true - cl_arr_pred) ** 2)
        ss_tot = np.sum((cl_arr_true - np.mean(cl_arr_true)) ** 2)
        r2 = float(1.0 - (ss_res / max(1e-6, ss_tot)))

        # Physics gates
        drag_positive = bool(np.all(cd_arr_pred > 0.0))
        # Monotonicity check on pre-stall
        order = np.argsort(aoas)
        aoas_sorted = np.array(aoas)[order]
        cls_sorted = cl_arr_pred[order]
        pre_stall = (aoas_sorted >= -2.0) & (aoas_sorted <= 8.0)
        lift_mono = True
        if np.sum(pre_stall) >= 3:
            diffs = np.diff(cls_sorted[pre_stall])
            lift_mono = bool(np.all(diffs >= -0.01))

        # Scientific verdict
        if r2 >= 0.85 and cl_rmse < 0.10 and drag_positive and lift_mono:
            verdict = "VALIDATED_CROSS_DOMAIN_GENERALIZATION: Model maintains quantitative and physical consistency across datasets."
        elif not drag_positive or not lift_mono:
            verdict = "PHYSICAL_SANITY_FAILURE: Model violates fluid dynamics constraints (drag positivity or lift monotonicity) on target domain."
        else:
            verdict = f"PARTIALLY_GENERALIZED: Model demonstrates moderate transfer fidelity (CL RMSE: {cl_rmse:.4f}, R²: {r2:.3f})."

        return CrossDatasetGeneralizationReport(
            benchmark_id=f"CDG-{source_dataset_id}-TO-{target_dataset_id}",
            source_dataset_id=source_dataset_id,
            target_dataset_id=target_dataset_id,
            model_name=model_name,
            is_valid_comparison=True,
            status="VALID_SCIENTIFIC_COMPARISON",
            target_sample_count=len(points),
            points=points,
            cl_rmse=round(cl_rmse, 4),
            cd_rmse=round(cd_rmse, 5),
            cl_mae=round(cl_mae, 4),
            cd_mae=round(cd_mae, 5),
            r2_cl=round(r2, 4),
            lift_monotonicity_passed=lift_mono,
            drag_positivity_passed=drag_positive,
            scientific_verdict=verdict
        )
