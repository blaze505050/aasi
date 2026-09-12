"""
AASI Multi-Dataset Benchmark Engine.

Evaluates aerodynamic prediction models simultaneously against diverse ground truths:
- Experimental Wind Tunnel Polars (NASA Langley LTPT / TM-4083)
- Numerical RANS Simulations (AirfRANS OpenFOAM simpleFoam / NeurIPS 2022)

Computes cross-dataset fidelity metrics, decomposing discrepancies into
experimental measurement uncertainty and numerical turbulence model divergence.
"""

from __future__ import annotations

import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.datasets.catalog import DatasetCatalog
from backend.datasets.adapters.base import DatasetCase
from backend.physics.uncertainty_model import (
    AerodynamicUncertaintyQuantifier,
    UncertaintyAssessment,
    UncertaintyStatus,
)


class BenchmarkPointComparison(BaseModel):
    geometry: str
    aoa_deg: float
    mach: float
    reynolds: float
    pred_cl: float
    pred_cd: float
    dataset_id: str
    dataset_cl: float
    dataset_cd: float
    delta_cl: float
    delta_cd: float
    cl_error_pct: float
    cd_error_pct: float
    is_ood: bool = False
    notes: str = ""


class DatasetBenchmarkSummary(BaseModel):
    dataset_id: str
    dataset_type: str  # "EXPERIMENTAL" or "SIMULATION_RANS"
    sample_count: int
    mean_cl_rmse: float
    mean_cd_rmse: float
    max_cl_error: float
    max_cd_error: float
    within_uncertainty_count: int
    uncertainty_coverage_pct: float


class MultiDatasetBenchmarkResult(BaseModel):
    benchmark_id: str
    model_name: str
    datasets_evaluated: List[str]
    total_comparisons: int
    comparisons: List[BenchmarkPointComparison] = Field(default_factory=list)
    dataset_summaries: Dict[str, DatasetBenchmarkSummary] = Field(default_factory=dict)
    rans_vs_exp_bias_cl: float = 0.0
    overall_scientific_consistency_score: float = 1.0  # 0.0 to 1.0 scale
    uncertainty_assessment: Optional[UncertaintyAssessment] = None
    summary_verdict: str = ""


class MultiDatasetBenchmarkEngine:
    """Orchestrates cross-dataset aerodynamic benchmarking."""

    def __init__(self, catalog: Optional[DatasetCatalog] = None):
        self.catalog = catalog or DatasetCatalog()

    def benchmark_model_predictions(
        self,
        model_name: str,
        predictions: List[Dict[str, Any]],
        dataset_ids: Optional[List[str]] = None
    ) -> MultiDatasetBenchmarkResult:
        """
        Benchmarks a list of predicted aerodynamic points:
        [{ "geometry": "NACA 0012", "aoa_deg": 4.0, "mach": 0.15, "reynolds": 3.0e6, "cl": 0.43, "cd": 0.008 }]
        against registered dataset ground truths.
        """
        active_ids = dataset_ids or ["DATASET-NACA-0012-LTPT", "DATASET-AIRFRANS-1K"]
        all_comparisons: List[BenchmarkPointComparison] = []
        dataset_points: Dict[str, List[BenchmarkPointComparison]] = {did: [] for did in active_ids}

        for did in active_ids:
            adapter = self.catalog.get_adapter(did)
            if not adapter:
                continue
            cases = adapter.list_cases(limit=500)
            
            for pred in predictions:
                p_geom = str(pred.get("geometry", "NACA 0012")).strip().upper()
                p_aoa = float(pred.get("aoa_deg", 0.0))
                p_cl = float(pred.get("cl", 0.0))
                p_cd = float(pred.get("cd", 0.01))
                p_re = float(pred.get("reynolds", 3.0e6))
                p_mach = float(pred.get("mach", 0.15))

                # Find closest matching case in dataset
                best_match: Optional[DatasetCase] = None
                best_dist = float("inf")

                for c in cases:
                    if c.geometry_name.strip().upper() != p_geom:
                        continue
                    # Match AoA closely (within 1.5 deg)
                    d_aoa = abs(c.aoa_deg - p_aoa)
                    if d_aoa > 1.5:
                        continue
                    d_total = d_aoa * 2.0 + abs(math.log10(max(1.0, c.reynolds)) - math.log10(max(1.0, p_re)))
                    if d_total < best_dist:
                        best_dist = d_total
                        best_match = c

                if best_match and best_match.cl is not None:
                    d_cl = p_cl - best_match.cl
                    d_cd = p_cd - (best_match.cd if best_match.cd is not None else 0.01)
                    cl_pct = abs(d_cl / max(1e-4, abs(best_match.cl))) * 100.0 if best_match.cl != 0.0 else abs(d_cl) * 100.0
                    cd_pct = abs(d_cd / max(1e-4, abs(best_match.cd if best_match.cd is not None else 0.01))) * 100.0

                    is_ood = (p_aoa > 10.0) or (p_re > 4.5e6)
                    comp = BenchmarkPointComparison(
                        geometry=p_geom,
                        aoa_deg=p_aoa,
                        mach=p_mach,
                        reynolds=p_re,
                        pred_cl=round(p_cl, 4),
                        pred_cd=round(p_cd, 5),
                        dataset_id=did,
                        dataset_cl=round(best_match.cl, 4),
                        dataset_cd=round(best_match.cd if best_match.cd is not None else 0.0, 5),
                        delta_cl=round(d_cl, 4),
                        delta_cd=round(d_cd, 5),
                        cl_error_pct=round(cl_pct, 2),
                        cd_error_pct=round(cd_pct, 2),
                        is_ood=is_ood,
                        notes=f"Matched case {best_match.case_id} (AoA {best_match.aoa_deg}°)"
                    )
                    all_comparisons.append(comp)
                    dataset_points[did].append(comp)

        # Compute summary statistics per dataset
        summaries: Dict[str, DatasetBenchmarkSummary] = {}
        for did, points in dataset_points.items():
            if not points:
                summaries[did] = DatasetBenchmarkSummary(
                    dataset_id=did,
                    dataset_type="EXPERIMENTAL" if "LTPT" in did else "SIMULATION_RANS",
                    sample_count=0,
                    mean_cl_rmse=0.0,
                    mean_cd_rmse=0.0,
                    max_cl_error=0.0,
                    max_cd_error=0.0,
                    within_uncertainty_count=0,
                    uncertainty_coverage_pct=0.0
                )
                continue

            cl_sq = sum(p.delta_cl ** 2 for p in points)
            cd_sq = sum(p.delta_cd ** 2 for p in points)
            cl_rmse = math.sqrt(cl_sq / len(points))
            cd_rmse = math.sqrt(cd_sq / len(points))
            max_cl = max(abs(p.delta_cl) for p in points)
            max_cd = max(abs(p.delta_cd) for p in points)
            
            # Count within uncertainty (U95 ~ 0.03 for CL)
            within_u = sum(1 for p in points if abs(p.delta_cl) <= 0.035)
            cov_pct = (within_u / len(points)) * 100.0

            summaries[did] = DatasetBenchmarkSummary(
                dataset_id=did,
                dataset_type="EXPERIMENTAL" if "LTPT" in did else "SIMULATION_RANS",
                sample_count=len(points),
                mean_cl_rmse=round(cl_rmse, 4),
                mean_cd_rmse=round(cd_rmse, 5),
                max_cl_error=round(max_cl, 4),
                max_cd_error=round(max_cd, 5),
                within_uncertainty_count=within_u,
                uncertainty_coverage_pct=round(cov_pct, 1)
            )

        # Compute cross-dataset discrepancy bias (RANS vs Wind Tunnel)
        bias_cl = 0.0
        ltpt_points = {round(p.aoa_deg, 1): p for p in dataset_points.get("DATASET-NACA-0012-LTPT", [])}
        airfrans_points = {round(p.aoa_deg, 1): p for p in dataset_points.get("DATASET-AIRFRANS-1K", [])}
        common_aoas = set(ltpt_points.keys()).intersection(set(airfrans_points.keys()))
        if common_aoas:
            diffs = [airfrans_points[a].dataset_cl - ltpt_points[a].dataset_cl for a in common_aoas]
            bias_cl = round(sum(diffs) / len(diffs), 4)

        # Compute combined uncertainty assessment
        unc_assessment = AerodynamicUncertaintyQuantifier.compute_naca0012_uncertainty(aoa_deg=8.0)

        # Overall scientific consistency score (1.0 = perfect match within uncertainty)
        all_rmses = [s.mean_cl_rmse for s in summaries.values() if s.sample_count > 0]
        mean_all_rmse = sum(all_rmses) / len(all_rmses) if all_rmses else 0.05
        consistency_score = max(0.0, min(1.0, 1.0 - (mean_all_rmse / 0.15)))

        verdict = (
            f"Multi-dataset evaluation complete across {len(active_ids)} benchmarks. "
            f"Cross-dataset RANS-vs-Experiment bias: {bias_cl:+.4f} CL. "
            f"Scientific consistency rating: {consistency_score * 100:.1f}%."
        )

        return MultiDatasetBenchmarkResult(
            benchmark_id="BM-MULTI-" + str(abs(hash(model_name + str(len(predictions)))) % 100000),
            model_name=model_name,
            datasets_evaluated=active_ids,
            total_comparisons=len(all_comparisons),
            comparisons=all_comparisons,
            dataset_summaries=summaries,
            rans_vs_exp_bias_cl=bias_cl,
            overall_scientific_consistency_score=round(consistency_score, 3),
            uncertainty_assessment=unc_assessment,
            summary_verdict=verdict
        )
