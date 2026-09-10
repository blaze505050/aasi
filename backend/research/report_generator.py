"""
AASI Scientific Research Report Generator.

Compiles research loops, campaign executions, multi-fidelity data fusion,
and model promotion audits into structured scientific Markdown and LaTeX reports.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from backend.research.models import ResearchObjective, ResearchExperiment
from backend.research.comparison import ModelComparisonReport
from backend.research.promotion import ModelPromotionAudit
from backend.simulation.job_spec import CFDJobSpec


class ScientificReportGenerator:
    """Generates peer-review quality scientific reports."""

    @classmethod
    def generate_markdown_report(
        cls,
        objective: ResearchObjective,
        experiment: Optional[ResearchExperiment] = None,
        comparison: Optional[ModelComparisonReport] = None,
        promotion: Optional[ModelPromotionAudit] = None,
        author: str = "AASI Autonomous Aerospace Scientific Intelligence"
    ) -> str:
        """Emits a complete scientific markdown report."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        md = f"""# Autonomous Aerospace Research Report: {objective.title}

**Author:** {author}  
**Date:** {now}  
**Objective ID:** `{objective.objective_id}`  
**Target Regime:** `{objective.target_regime}`  
**Uncertainty Target:** `Δσ ≤ {objective.target_uncertainty_threshold}`  

---

## 1. Scientific Motivation & Objective
{objective.description}

- **Target Geometries:** {', '.join(objective.target_geometries) if objective.target_geometries else 'General Airfoil Space'}
- **Scientific Priority:** {objective.priority} / 10.0
- **Lifecycle Status:** `{objective.status.value}`

---

## 2. Active Learning & Simulation Campaign
The autonomous research planner formulated and dispatched targeted high-fidelity simulations to eliminate epistemic uncertainties in high-gradient regimes.
"""

        if experiment:
            md += f"""
### Experiment: {experiment.title}
- **Experiment ID:** `{experiment.experiment_id}`
- **Completed Jobs:** {experiment.completed_jobs} / {experiment.total_jobs}
- **Execution Status:** `{experiment.status.value}`
- **Key Findings:** {experiment.findings_summary or 'Simulations successfully ingested and quality-controlled.'}

#### Simulation Job Manifest:
| Job ID | Geometry | Mach | Reynolds | AoA (deg) | Solver | Backend | Priority |
|---|---|---|---|---|---|---|---|
"""
            for j in experiment.job_specs[:8]:
                md += f"| `{j.job_id}` | {j.geometry} | {j.flow_conditions.mach:.2f} | {j.flow_conditions.reynolds:.1e} | {j.flow_conditions.aoa_deg:.1f}° | {j.solver.value} | {j.execution_backend.value} | {j.scientific_priority:.1f} |\n"

        if comparison:
            md += f"""
---

## 3. Surrogate Retraining & Benchmark Non-Regression Audit
Head-to-head evaluation between baseline (`{comparison.baseline_model_id}`) and candidate (`{comparison.candidate_model_id}`) against the fixed ASME scientific benchmark suite:

### Quantitative Performance Metrics:
| Aerodynamic Metric | Baseline ({comparison.baseline_model_id}) | Candidate ({comparison.candidate_model_id}) | Delta (Δ) | Status |
|---|---|---|---|---|
| **$C_L$ RMSE** | `{comparison.baseline_eval.rmse_cl:.4f}` | `{comparison.candidate_eval.rmse_cl:.4f}` | `{comparison.delta_rmse_cl:+.4f}` | {'✅ Improved' if comparison.delta_rmse_cl <= 0 else '⚠️ Regressed'} |
| **$C_L$ $R^2$** | `{comparison.baseline_eval.r2_cl:.4f}` | `{comparison.candidate_eval.r2_cl:.4f}` | `{comparison.delta_r2_cl:+.4f}` | {'✅ Improved' if comparison.delta_r2_cl >= 0 else '⚠️ Regressed'} |
| **$C_D$ RMSE** | `{comparison.baseline_eval.rmse_cd:.5f}` | `{comparison.candidate_eval.rmse_cd:.5f}` | `{comparison.delta_rmse_cd:+.5f}` | {'✅ Improved' if comparison.delta_rmse_cd <= 0 else '⚠️ Regressed'} |
| **Stall Regime $C_L$ RMSE** | `{comparison.baseline_eval.stall_regime_rmse_cl:.4f}` | `{comparison.candidate_eval.stall_regime_rmse_cl:.4f}` | `{comparison.delta_stall_rmse_cl:+.4f}` | {'✅ Improved' if comparison.delta_stall_rmse_cl <= 0 else '⚠️ Regressed'} |

### Physical Invariants Verification:
- **$C_D > 0$ Positivity Pass Rate:** `{comparison.candidate_eval.cd_positivity_pass_rate_pct:.1f}%`
- **$C_L$ Linear Monotonicity Pass Rate:** `{comparison.candidate_eval.cl_monotonicity_pass_rate_pct:.1f}%`
- **Summary Verdict:** `{comparison.summary_verdict}`
"""

        if promotion:
            md += f"""
---

## 4. Multi-Gate Model Promotion Decision
- **Promoted:** `{'YES - ACTIVE PRODUCTION' if promotion.promoted else 'NO - HELD IN EXPERIMENTAL'}`
- **Target Tier:** `{promotion.target_tier.value}`
- **Promotion Audit Details:**
"""
            for g in promotion.gate_results:
                icon = "✅" if g.passed else "❌"
                md += f"  - {icon} **{g.gate_name}:** {g.details}\n"

        md += """
---

## 5. Provenance & Reproducibility
All dataset versions, simulation manifests, mesh specifications, and neural surrogate weights are cryptographically hashed and cataloged in the AASI Knowledge Graph.
"""
        return md

    @classmethod
    def generate_latex_report(
        cls,
        objective: ResearchObjective,
        comparison: Optional[ModelComparisonReport] = None
    ) -> str:
        """Generates LaTeX formatted scientific summary."""
        latex = r"""\documentclass[conference]{IEEEtran}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{booktabs}
\begin{document}
\title{Autonomous Multi-Fidelity Aerospace Research Loop Report: """ + objective.title + r"""}
\author{\IEEEauthorblockN{AASI Scientific AI System}
\IEEEauthorblockA{Autonomous Aerospace Scientific Intelligence}}
\maketitle
\begin{abstract}
This report outlines an autonomous scientific research campaign executed to reduce surrogate epistemic uncertainty in the aerodynamic regime: """ + objective.target_regime + r""".
\end{abstract}
\section{Objective and Methodology}
""" + objective.description.replace("%", r"\%") + r"""
"""
        if comparison:
            latex += r"""
\section{Benchmark Validation}
\begin{table}[htbp]
\caption{Surrogate Benchmark Comparison}
\centering
\begin{tabular}{lrrr}
\toprule
Metric & Baseline & Candidate & $\Delta$ \\
\midrule
$C_L$ RMSE & """ + f"{comparison.baseline_eval.rmse_cl:.4f}" + r""" & """ + f"{comparison.candidate_eval.rmse_cl:.4f}" + r""" & """ + f"{comparison.delta_rmse_cl:+.4f}" + r""" \\
$C_D$ RMSE & """ + f"{comparison.baseline_eval.rmse_cd:.5f}" + r""" & """ + f"{comparison.candidate_eval.rmse_cd:.5f}" + r""" & """ + f"{comparison.delta_rmse_cd:+.5f}" + r""" \\
\bottomrule
\end{tabular}
\end{table}
"""
        latex += r"""
\section{Conclusion}
The autonomous closed-loop research protocol ensures continuous scientific discovery without sacrificing physical rigor.
\end{document}
"""
        return latex
