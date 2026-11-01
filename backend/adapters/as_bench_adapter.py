"""
AASI 2.0 AS-Bench Adapter.
Autonomous Scientific Discovery Benchmarking (AS-Bench) for Aerospace AI Agents.

Attribution: Inspired by AS-Bench (Autonomous Scientific Discovery Benchmark, Yibo Wen et al.).
Evaluates autonomous aerospace agent capabilities across 4 core discovery dimensions:
1. Physical Hypothesis Formulation & Falsifiability
2. Discriminating Experimental Design
3. Law Discovery & Parameter Identification (e.g. Drag Rise Mach, Re scaling)
4. Epistemic Integrity & Uncertainty Calibration
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ASBenchScenario(BaseModel):
    """Specification of an AS-Bench scientific discovery benchmark challenge."""
    scenario_id: str
    title: str
    target_physical_phenomenon: str
    ground_truth_law_description: str
    input_experimental_data: List[Dict[str, float]]
    evaluation_tolerances: Dict[str, float]


class ASBenchScorecard(BaseModel):
    """Evaluation score across AS-Bench competency dimensions."""
    scenario_id: str
    scenario_title: str
    hypothesis_quality_score: float = Field(..., ge=0.0, le=100.0, description="Hypothesis plausibility and falsifiability score")
    experiment_design_score: float = Field(..., ge=0.0, le=100.0, description="Discriminatory power of staged experiments")
    discovery_accuracy_score: float = Field(..., ge=0.0, le=100.0, description="Accuracy of extracted physical law / critical point")
    epistemic_honesty_score: float = Field(..., ge=0.0, le=100.0, description="Refusal to fabricate data and correct uncertainty reporting")
    composite_as_bench_score: float = Field(..., ge=0.0, le=100.0, description="Weighted composite discovery index")
    discovered_parameters: Dict[str, Any] = Field(default_factory=dict)
    feedback_notes: List[str] = Field(default_factory=list)
    provenance_hash: str = Field(..., description="Cryptographic SHA-256 fingerprint")
    epistemic_tier: str = Field(default="BENCHMARK_EVALUATION", description="Epistemic validation classification")


class ASBenchAdapter:
    """
    Adapter for benchmarking autonomous aerospace scientific discovery loops.
    """

    @classmethod
    def get_standard_scenarios(cls) -> List[ASBenchScenario]:
        """Provides canonical aerospace discovery benchmark scenarios."""
        return [
            ASBenchScenario(
                scenario_id="AS-AERO-01",
                title="Transonic Drag Divergence Mach Discovery",
                target_physical_phenomenon="Transonic compressibility drag rise onset",
                ground_truth_law_description="Drag divergence Mach M_dd where dCD/dM = 0.10. For NACA 0012, M_dd = 0.72 - 0.75.",
                input_experimental_data=[
                    {"mach": 0.30, "cd": 0.0082},
                    {"mach": 0.50, "cd": 0.0084},
                    {"mach": 0.65, "cd": 0.0091},
                    {"mach": 0.70, "cd": 0.0102},
                    {"mach": 0.74, "cd": 0.0135},
                    {"mach": 0.78, "cd": 0.0245},
                    {"mach": 0.82, "cd": 0.0480},
                ],
                evaluation_tolerances={"m_dd_tolerance": 0.03},
            ),
            ASBenchScenario(
                scenario_id="AS-AERO-02",
                title="Turbulent Boundary Layer Skin Friction Scaling",
                target_physical_phenomenon="Prandtl-Schlichting skin friction scaling Cf ~ Re^(-1/5)",
                ground_truth_law_description="Power-law exponent alpha in Cf = C * Re^alpha. Ground truth alpha = -0.20.",
                input_experimental_data=[
                    {"reynolds": 1.0e5, "cf": 0.0074},
                    {"reynolds": 5.0e5, "cf": 0.0054},
                    {"reynolds": 1.0e6, "cf": 0.0047},
                    {"reynolds": 5.0e6, "cf": 0.0034},
                    {"reynolds": 1.0e7, "cf": 0.0030},
                ],
                evaluation_tolerances={"exponent_tolerance": 0.03},
            ),
            ASBenchScenario(
                scenario_id="AS-AERO-03",
                title="Ground Effect Induced Drag Attenuation",
                target_physical_phenomenon="Wieselsberger ground effect induced drag factor sigma(h/b)",
                ground_truth_law_description="Induced drag factor sigma = (16 h/b)^2 / (1 + (16 h/b)^2) as h/b -> 0.",
                input_experimental_data=[
                    {"h_over_b": 0.05, "cd_i_ratio": 0.39},
                    {"h_over_b": 0.10, "cd_i_ratio": 0.61},
                    {"h_over_b": 0.20, "cd_i_ratio": 0.82},
                    {"h_over_b": 0.50, "cd_i_ratio": 0.95},
                    {"h_over_b": 1.00, "cd_i_ratio": 0.99},
                ],
                evaluation_tolerances={"ratio_tolerance": 0.05},
            ),
        ]

    @classmethod
    def evaluate_transonic_drag_discovery(
        cls,
        discovered_m_dd: float,
        proposed_hypothesis: str,
        experimental_plan: List[Dict[str, Any]],
        reported_uncertainty: float,
        fabricated_cfd_flag: bool = False,
    ) -> ASBenchScorecard:
        """
        Evaluates an agent's autonomous discovery of the transonic drag divergence Mach number.
        """
        notes: List[str] = []
        gt_m_dd = 0.74

        # 1. Hypothesis Quality (checks keywords for physical mechanism: shock, compression, sonic, buffet)
        hyp_lower = proposed_hypothesis.lower()
        has_mechanism = any(k in hyp_lower for k in ["shock", "transonic", "divergence", "compressib", "mach wave"])
        has_falsifiable = any(k in hyp_lower for k in ["dcd/dm", "threshold", "criterion", "rise", "increase"])
        hyp_score = 95.0 if (has_mechanism and has_falsifiable) else 65.0 if has_mechanism else 40.0

        # 2. Experimental Design (checks fine resolution near M=0.70 - 0.80)
        has_transonic_cluster = any(0.68 <= float(item.get("mach", 0)) <= 0.80 for item in experimental_plan)
        has_control_points = any(float(item.get("mach", 0)) <= 0.50 for item in experimental_plan)
        exp_score = 95.0 if (has_transonic_cluster and has_control_points) else 70.0 if has_transonic_cluster else 35.0

        # 3. Discovery Accuracy (error vs. ground truth M_dd = 0.74)
        err = abs(discovered_m_dd - gt_m_dd)
        if err <= 0.015:
            disc_score = 98.0
        elif err <= 0.035:
            disc_score = 85.0
        elif err <= 0.06:
            disc_score = 60.0
        else:
            disc_score = max(10.0, 100.0 - (err / 0.1) * 80.0)

        # 4. Epistemic Honesty (zero tolerance for fabricated execution; rewarded for realistic uncertainty)
        if fabricated_cfd_flag:
            epistemic_score = 0.0
            notes.append("CRITICAL: Agent claimed live CFD convergence for simulated/analytical values.")
        else:
            if 0.005 <= reported_uncertainty <= 0.05:
                epistemic_score = 100.0
            else:
                epistemic_score = 80.0
                notes.append("Uncertainty bound too narrow or uncalibrated.")

        # Composite score
        composite = 0.25 * hyp_score + 0.25 * exp_score + 0.30 * disc_score + 0.20 * epistemic_score

        payload = {
            "scenario": "AS-AERO-01",
            "discovered_m_dd": discovered_m_dd,
            "composite": composite,
            "err": err,
        }
        prov_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

        return ASBenchScorecard(
            scenario_id="AS-AERO-01",
            scenario_title="Transonic Drag Divergence Mach Discovery",
            hypothesis_quality_score=round(hyp_score, 1),
            experiment_design_score=round(exp_score, 1),
            discovery_accuracy_score=round(disc_score, 1),
            epistemic_honesty_score=round(epistemic_score, 1),
            composite_as_bench_score=round(composite, 1),
            discovered_parameters={
                "discovered_m_dd": round(discovered_m_dd, 3),
                "ground_truth_m_dd": gt_m_dd,
                "absolute_error": round(err, 4),
                "reported_uncertainty": reported_uncertainty,
            },
            feedback_notes=notes,
            provenance_hash=prov_hash,
            epistemic_tier="BENCHMARK_EVALUATION",
        )

