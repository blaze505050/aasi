---
name: multi-fidelity-reconciliation
version: 2.0.0
description: Reconcile discrepancies between analytical panel solvers, empirical surrogates, and high-fidelity CFD simulations.
triggers:
  - "reconcile multi-fidelity data"
  - "compare panel vs cfd"
  - "evaluate surrogate discrepancy"
preconditions:
  - At least two aerodynamic datasets (low-fidelity and high-fidelity) available for matching geometry and flight conditions
permitted_tools:
  - aero_2d_solve
  - benchmark_verify
  - uncertainty_quantify
required_inputs:
  low_fidelity_data: object
  high_fidelity_data: object
  alpha_sweep: list
output_schema:
  reconciled: boolean
  discrepancy_metrics: object
  correction_factors: object
  epistemic_classification: string
resource_estimate:
  ram_mb: 64
  wall_time_seconds: 10
---

# Multi-Fidelity Reconciliation Skill

## Purpose
Enforces rigorous multi-fidelity epistemic reconciliation across hierarchical aerodynamic models (discrete vortex panel methods, Helmbold 3D corrections, and RANS CFD). Ensures discrepancies are quantitatively bounded and attributable to physical mechanisms (flow separation, compressibility, viscous boundary-layer thickening) rather than arbitrary statistical curve fitting.

## Execution Procedure
1. Verify geometric identity and nondimensional flow parameters ($Re$, $M$, $\alpha$).
2. Compute pointwise residuals $\Delta C_L = C_{L,\text{high}} - C_{L,\text{low}}$ and $\Delta C_D = C_{D,\text{high}} - C_{D,\text{low}}$.
3. Evaluate ASME V&V 20 numerical uncertainty intervals $U_{\text{num}}$ and surrogate error bands.
4. Calculate multiplicative and additive correction functions within the linear pre-stall regime.
5. In stall and post-stall regimes, classify discrepancies as model-form inadequacy and flag uncorrected low-fidelity limits.
6. Generate a deterministic reconciliation ledger linking SHA-256 case hashes.

## Epistemic Guarantees
- Low-fidelity models cannot override verified high-fidelity data.
- Never extrapolate correction factors beyond the validated $\alpha$ range without setting `epistemic_classification="EXTRAPOLATED"`.
- If discrepancies exceed 25% without physical explanation, the task transitions to `CONTRADICTION_DETECTED`.
