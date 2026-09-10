"""
AASI Model Comparison & Degradation Detection Engine.

Performs head-to-head scientific evaluations between surrogate versions
(e.g., AeroSurrogateV1 vs AeroSurrogateV2) to ensure strict non-regression.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from backend.research.benchmarks import FixedBenchmarkSuite, BenchmarkEvaluationResult


class ModelComparisonReport(BaseModel):
    baseline_model_id: str
    candidate_model_id: str
    baseline_eval: BenchmarkEvaluationResult
    candidate_eval: BenchmarkEvaluationResult
    delta_rmse_cl: float
    delta_r2_cl: float
    delta_rmse_cd: float
    delta_r2_cd: float
    delta_stall_rmse_cl: float
    improved: bool
    regressed: bool
    regression_warnings: List[str] = Field(default_factory=list)
    summary_verdict: str


class ModelComparisonEngine:
    """Evaluates and compares candidate surrogate against baseline."""

    @classmethod
    def compare_models(
        cls,
        baseline_id: str,
        candidate_id: str,
        baseline_predict_fn,
        candidate_predict_fn,
        max_allowed_regression_pct: float = 2.0
    ) -> ModelComparisonReport:
        """
        Runs standardized benchmark evaluation on both models and computes deltas.
        """
        base_res = FixedBenchmarkSuite.evaluate_model(baseline_predict_fn)
        cand_res = FixedBenchmarkSuite.evaluate_model(candidate_predict_fn)

        delta_rmse_cl = round(cand_res.rmse_cl - base_res.rmse_cl, 4)
        delta_r2_cl = round(cand_res.r2_cl - base_res.r2_cl, 4)
        delta_rmse_cd = round(cand_res.rmse_cd - base_res.rmse_cd, 5)
        delta_r2_cd = round(cand_res.r2_cd - base_res.r2_cd, 4)
        delta_stall = round(cand_res.stall_regime_rmse_cl - base_res.stall_regime_rmse_cl, 4)

        warnings = []
        regressed = False

        # Degradation check: did RMSE worsen significantly?
        if base_res.rmse_cl > 0:
            cl_deg_pct = ((cand_res.rmse_cl - base_res.rmse_cl) / base_res.rmse_cl) * 100.0
            if cl_deg_pct > max_allowed_regression_pct:
                regressed = True
                warnings.append(f"CL RMSE regressed by {cl_deg_pct:.2f}% (exceeds {max_allowed_regression_pct}% limit).")

        if base_res.rmse_cd > 0:
            cd_deg_pct = ((cand_res.rmse_cd - base_res.rmse_cd) / base_res.rmse_cd) * 100.0
            if cd_deg_pct > max_allowed_regression_pct:
                regressed = True
                warnings.append(f"CD RMSE regressed by {cd_deg_pct:.2f}% (exceeds {max_allowed_regression_pct}% limit).")

        # Check physical gate preservation
        if cand_res.cd_positivity_pass_rate_pct < 100.0:
            regressed = True
            warnings.append("Candidate violated CD positivity gate.")
        if cand_res.cl_monotonicity_pass_rate_pct < 100.0:
            regressed = True
            warnings.append("Candidate violated CL linear monotonicity gate.")

        improved = (delta_rmse_cl <= 0.0 and delta_r2_cl >= 0.0 and not regressed)

        if regressed:
            verdict = "REJECTED_REGRESSION: Candidate exhibits unacceptable degradation on benchmark physics."
        elif improved:
            verdict = "PROMOTABLE: Candidate demonstrates superior or non-regressive accuracy across benchmarks."
        else:
            verdict = "EQUIVALENT: Candidate performance matches baseline within tolerance."

        return ModelComparisonReport(
            baseline_model_id=baseline_id,
            candidate_model_id=candidate_id,
            baseline_eval=base_res,
            candidate_eval=cand_res,
            delta_rmse_cl=delta_rmse_cl,
            delta_r2_cl=delta_r2_cl,
            delta_rmse_cd=delta_rmse_cd,
            delta_r2_cd=delta_r2_cd,
            delta_stall_rmse_cl=delta_stall,
            improved=improved,
            regressed=regressed,
            regression_warnings=warnings,
            summary_verdict=verdict
        )
