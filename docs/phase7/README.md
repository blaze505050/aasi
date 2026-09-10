# AASI Phase 7: Multi-Fidelity Physics + Active Learning + Autonomous Research Loop

Autonomous Aerospace Scientific Intelligence (AASI) Phase 7 transitions the framework from a static Physics-AI surrogate to a continuous, self-improving, closed-loop scientific discovery engine.

```
+-----------------------------------------------------------------------------------+
|                        THE AASI CLOSED-LOOP RESEARCH PROTOCOL                      |
|                                                                                   |
|  [Active AeroSurrogateV1]                                                         |
|         │                                                                         |
|         ▼                                                                         |
|  [Epistemic Uncertainty & Domain Boundary Audit]                                  |
|         │                                                                         |
|         ▼                                                                         |
|  [Active Learning 2.0: COST_AWARE / UNCERTAINTY / OOD / SPACE_COVERAGE]            |
|         │                                                                         |
|         ▼                                                                         |
|  [Autonomous Simulation Planner: Canonical CFDJobSpec & Quality Gates]            |
|         │                                                                         |
|         ▼                                                                         |
|  [User-Executed High-Fidelity CFD Run] (ASME V&V 20 residual / force / positivity)|
|         │                                                                         |
|         ▼                                                                         |
|  [Automated Ingestion & Quality Control Engine]                                   |
|         │                                                                         |
|         ▼                                                                         |
|  [Immutable Dataset Factory: AERO-AIRFOIL-V1.0 ➔ V2.0]                            |
|         │                                                                         |
|         ▼                                                                         |
|  [Model Retraining & Fine-Tuning Pipeline: AeroSurrogateV2]                       |
|         │                                                                         |
|         ▼                                                                         |
|  [Standard Benchmark Suite: NACA 0012, 2412, 4412 Evaluation]                     |
|         │                                                                         |
|         ▼                                                                         |
|  [4-Gate Promotion Protocol: EXPERIMENTAL ➔ BENCHMARK ➔ VALIDATED ➔ ACTIVE]        |
|         │                                                                         |
|         ▼                                                                         |
|  [Automated Peer-Review Scientific Report Generation (Markdown & LaTeX)]          |
+-----------------------------------------------------------------------------------+
```

## Phase 7 Highlights

1. **Multi-Fidelity Scientific Fabric**:
   - 5-Tier Priority Cascade: `OFFICIAL_EXPERIMENT` $\to$ `VALIDATED_CFD` $\to$ `SURROGATE` $\to$ `ANALYTICAL` $\to$ `PLANNER`.
   - Physics-informed discrepancy modeling: $\Delta(\mathbf{x}) = y_{\text{high}}(\mathbf{x}) - \hat{y}_{\text{low}}(\mathbf{x})$.
   - Uncertainty calibration & conformal coverage metrics ($1\sigma, 2\sigma$).
   - Multi-fidelity data fusion: $\hat{y}_{\text{fused}}(\mathbf{x}) = \rho \cdot \hat{y}_{\text{low}}(\mathbf{x}) + \delta(\mathbf{x})$.

2. **Active Learning 2.0 Engine**:
   - 4 Acquisition strategies: `COST_AWARE`, `UNCERTAINTY`, `OOD_BOUNDARY`, `SPACE_COVERAGE`.
   - Acquisition score combining model variance, grid density, numerical cost penalty, and physics discrepancy.
   - Candidate lifecycle state machine: `PROPOSED` $\to$ `PLANNED` $\to$ `EXECUTED` $\to$ `INGESTED` $\to$ `EVALUATED` $\to$ `ARCHIVED`.
   - 2D Parameter coverage map generation (`aoa_vs_mach`, `mach_vs_re`, `aoa_vs_re`) with density and void detection.

3. **Canonical CFDJobSpec & ASME V&V 20 QC Engine**:
   - Machine-readable specification containing geometry, solver, numerical schemes, mesh refinement, boundary conditions, and acceptance criteria.
   - Comprehensive QC auditor: residual convergence ($< 10^{-4}$), force stability ($< 1\%$), pressure drag positivity ($C_D > 0$), and chordwise $C_p$ envelope check.

4. **Retraining & 4-Gate Model Promotion**:
   - Immutable dataset versioning with SHA-256 provenance tracking.
   - Fine-tuning and retraining pipeline generating next-generation surrogates (`AeroSurrogateV2`).
   - Fixed benchmark test suite across canonical airfoils (NACA 0012, NACA 2412, NACA 4412).
   - 4-Tier Promotion Gates: Check 1 (Loss Convergence), Check 2 (Benchmark Non-Regression), Check 3 (Physics Positivity $C_D > 0$, $C_{L,\alpha} > 0$), Check 4 (ASME V&V 20 GCI compatibility).

5. **Peer-Reviewed Scientific Report Generator**:
   - Markdown & LaTeX publication-ready report compilation.
   - Complete with methodology, parameter space coverage, error distributions, and benchmark tables.

6. **Interactive Next.js 14 Frontend**:
   - Autonomous Research Loop dashboard.
   - Real-time multi-fidelity resolver query console.
   - Active learning candidate ranking & 2D parameter coverage canvas.
   - Ingest & QC evaluation interface.
   - Retraining and promotion auditor.
   - Live Markdown and LaTeX export viewer.
