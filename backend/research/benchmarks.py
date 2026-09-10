"""
AASI Fixed Scientific Benchmark Suite.

Provides standardized evaluation datasets and rigorous physical validation tests
across reference airfoils (NACA 0012, NACA 2412, NACA 4412) to ensure new model
versions do not regress on foundational physics.
"""

from typing import Dict, List, Any, Tuple
from pydantic import BaseModel, Field
import numpy as np


class BenchmarkEvaluationResult(BaseModel):
    benchmark_id: str = "AERO-BENCHMARK-V1"
    total_eval_points: int = 0
    rmse_cl: float = 0.0
    r2_cl: float = 0.0
    rmse_cd: float = 0.0
    r2_cd: float = 0.0
    rmse_cm: float = 0.0
    max_error_cl: float = 0.0
    stall_regime_rmse_cl: float = 0.0
    cd_positivity_pass_rate_pct: float = 100.0
    cl_monotonicity_pass_rate_pct: float = 100.0
    passed_all_gates: bool = True
    gate_failures: List[str] = Field(default_factory=list)


class FixedBenchmarkSuite:
    """Fixed evaluation benchmark for model verification and comparison."""

    # Reference evaluation grid (subsonic + transonic + stall onset)
    BENCHMARK_CASES: List[Dict[str, Any]] = [
        # NACA 0012 standard polar
        {"geometry": "NACA 0012", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": -4.0, "exp_cl": -0.42, "exp_cd": 0.0075, "exp_cm": 0.0},
        {"geometry": "NACA 0012", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 0.0, "exp_cl": 0.00, "exp_cd": 0.0062, "exp_cm": 0.0},
        {"geometry": "NACA 0012", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 4.0, "exp_cl": 0.44, "exp_cd": 0.0072, "exp_cm": 0.0},
        {"geometry": "NACA 0012", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 8.0, "exp_cl": 0.88, "exp_cd": 0.0105, "exp_cm": 0.0},
        {"geometry": "NACA 0012", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 12.0, "exp_cl": 1.25, "exp_cd": 0.0180, "exp_cm": -0.008},
        {"geometry": "NACA 0012", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 15.0, "exp_cl": 1.42, "exp_cd": 0.0310, "exp_cm": -0.015},
        # NACA 2412 cambered polar
        {"geometry": "NACA 2412", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 0.0, "exp_cl": 0.24, "exp_cd": 0.0065, "exp_cm": -0.052},
        {"geometry": "NACA 2412", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 4.0, "exp_cl": 0.67, "exp_cd": 0.0078, "exp_cm": -0.053},
        {"geometry": "NACA 2412", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 8.0, "exp_cl": 1.08, "exp_cd": 0.0118, "exp_cm": -0.051},
        {"geometry": "NACA 2412", "mach": 0.15, "reynolds": 3.0e6, "aoa_deg": 12.0, "exp_cl": 1.45, "exp_cd": 0.0195, "exp_cm": -0.048},
        # NACA 4412 high-lift polar
        {"geometry": "NACA 4412", "mach": 0.20, "reynolds": 3.0e6, "aoa_deg": 0.0, "exp_cl": 0.45, "exp_cd": 0.0074, "exp_cm": -0.102},
        {"geometry": "NACA 4412", "mach": 0.20, "reynolds": 3.0e6, "aoa_deg": 6.0, "exp_cl": 1.05, "exp_cd": 0.0112, "exp_cm": -0.101},
        {"geometry": "NACA 4412", "mach": 0.20, "reynolds": 3.0e6, "aoa_deg": 12.0, "exp_cl": 1.58, "exp_cd": 0.0240, "exp_cm": -0.098},
        # Transonic sample
        {"geometry": "NACA 0012", "mach": 0.50, "reynolds": 5.0e6, "aoa_deg": 2.0, "exp_cl": 0.26, "exp_cd": 0.0089, "exp_cm": 0.0},
    ]

    @classmethod
    def evaluate_model(cls, predict_fn) -> BenchmarkEvaluationResult:
        """
        Runs full benchmark evaluation against any prediction callable.
        `predict_fn(geometry, mach, reynolds, aoa) -> dict(cl, cd, cm)`
        """
        cases = cls.BENCHMARK_CASES
        pred_cl_list = []
        exp_cl_list = []
        pred_cd_list = []
        exp_cd_list = []
        pred_cm_list = []
        exp_cm_list = []

        stall_errors_cl = []
        cd_positivity_count = 0
        gate_failures = []

        # Geometry linear sweep checks
        linear_aoas = [-4.0, 0.0, 4.0, 8.0]
        naca0012_cls = []

        for c in cases:
            pred = predict_fn(c["geometry"], c["mach"], c["reynolds"], c["aoa_deg"])
            pcl = pred.get("cl", 0.0)
            pcd = pred.get("cd", 0.0)
            pcm = pred.get("cm", 0.0)

            pred_cl_list.append(pcl)
            exp_cl_list.append(c["exp_cl"])
            pred_cd_list.append(pcd)
            exp_cd_list.append(c["exp_cd"])
            pred_cm_list.append(pcm)
            exp_cm_list.append(c["exp_cm"])

            if pcd > 0.0:
                cd_positivity_count += 1
            else:
                gate_failures.append(f"CD <= 0 violation for {c['geometry']} at AoA {c['aoa_deg']}")

            if c["aoa_deg"] >= 12.0:
                stall_errors_cl.append((pcl - c["exp_cl"])**2)

            if c["geometry"] == "NACA 0012" and c["mach"] == 0.15 and c["aoa_deg"] in linear_aoas:
                naca0012_cls.append((c["aoa_deg"], pcl))

        # Check linear monotonicity
        naca0012_cls.sort(key=lambda x: x[0])
        monotonic = True
        for i in range(len(naca0012_cls) - 1):
            if naca0012_cls[i+1][1] <= naca0012_cls[i][1]:
                monotonic = False
                gate_failures.append("Linear lift slope non-monotonicity detected.")
                break

        # Compute regression metrics
        pred_cl = np.array(pred_cl_list)
        exp_cl = np.array(exp_cl_list)
        pred_cd = np.array(pred_cd_list)
        exp_cd = np.array(exp_cd_list)

        rmse_cl = float(np.sqrt(np.mean((pred_cl - exp_cl)**2)))
        rmse_cd = float(np.sqrt(np.mean((pred_cd - exp_cd)**2)))
        max_err_cl = float(np.max(np.abs(pred_cl - exp_cl)))

        # R2
        ss_tot_cl = np.sum((exp_cl - np.mean(exp_cl))**2)
        ss_res_cl = np.sum((exp_cl - pred_cl)**2)
        r2_cl = float(1.0 - (ss_res_cl / ss_tot_cl)) if ss_tot_cl > 0 else 1.0

        ss_tot_cd = np.sum((exp_cd - np.mean(exp_cd))**2)
        ss_res_cd = np.sum((exp_cd - pred_cd)**2)
        r2_cd = float(1.0 - (ss_res_cd / ss_tot_cd)) if ss_tot_cd > 0 else 1.0

        stall_rmse = float(np.sqrt(np.mean(stall_errors_cl))) if stall_errors_cl else 0.0
        pos_rate = (cd_positivity_count / len(cases)) * 100.0
        mono_rate = 100.0 if monotonic else 0.0

        passed = (len(gate_failures) == 0 and r2_cl >= 0.90 and pos_rate == 100.0)

        return BenchmarkEvaluationResult(
            benchmark_id="AERO-BENCHMARK-V1",
            total_eval_points=len(cases),
            rmse_cl=round(rmse_cl, 4),
            r2_cl=round(r2_cl, 4),
            rmse_cd=round(rmse_cd, 5),
            r2_cd=round(r2_cd, 4),
            max_error_cl=round(max_err_cl, 4),
            stall_regime_rmse_cl=round(stall_rmse, 4),
            cd_positivity_pass_rate_pct=round(pos_rate, 1),
            cl_monotonicity_pass_rate_pct=round(mono_rate, 1),
            passed_all_gates=passed,
            gate_failures=gate_failures
        )
