# AASI 5-Tier Epistemic Aerodynamic Uncertainty Quantification Framework

## 1. Executive Summary & GUM Compliance
Governing Directive: **Real Scientific Execution, Evidence Integrity & Independent Reproducibility.**

The AASI Epistemic Uncertainty Engine (`backend/physics/uncertainty_model.py`) establishes a formal 5-tier uncertainty budget compliant with the **ISO/IEC Guide to the Expression of Uncertainty in Measurement (GUM)**. Rather than treating AI surrogate or CFD predictions as deterministic point values, AASI maps, quantifies, and propagates all dominant uncertainty components to produce combined expanded $U_{95}$ coverage intervals.

---

## 2. The 5-Tier Uncertainty Budget

```
┌─────────────────────────────────────────────────────────────┐
│                   5-Tier Uncertainty Budget                 │
├─────────────────────────────────────────────────────────────┤
│ 1. Input Uncertainty (Flight Condition Tolerances)          │
│    - Mach number tolerance (delta_M = 0.002)                │
│    - Angle of attack tolerance (delta_alpha = 0.05 deg)     │
│    - Reynolds number variation (delta_Re = 1%)              │
│    - Propagated via thin-airfoil sensitivity:               │
│      u_input = delta_alpha * (dCL/dalpha) = 0.0055          │
├─────────────────────────────────────────────────────────────┤
│ 2. Numerical Discretization & Iterative Uncertainty         │
│    - ASME V&V 20 Fine GCI: u_gci = 0.0080                   │
│    - Iterative convergence residual: u_iter = 0.0002        │
│    - Total numerical: u_num = sqrt(u_gci^2 + u_iter^2)      │
├─────────────────────────────────────────────────────────────┤
│ 3. Model Discrepancy & Epistemic Distance                   │
│    - Surrogate epistemic std dev: u_surr = 0.015            │
│    - Turbulence closure (k-omega SST):                      │
│      * Linear regime (alpha < 12 deg): u_turb = 0.020       │
│      * Separated regime (alpha >= 12 deg): u_turb = 0.065   │
│    - Total model: u_mod = sqrt(u_surr^2 + u_turb^2)         │
├─────────────────────────────────────────────────────────────┤
│ 4. Experimental Measurement Uncertainty                     │
│    - NASA LTPT strain-gauge balance: u_meas_CL = 0.0050     │
│    - Pressure transducer accuracy: u_meas_CD = 0.0003       │
├─────────────────────────────────────────────────────────────┤
│ 5. Combined Expanded Uncertainty (U_95)                     │
│    - Root-Sum-of-Squares:                                   │
│      u_c = sqrt(u_input^2 + u_num^2 + u_mod^2 + u_meas^2)   │
│    - Expanded coverage interval (k = 1.96, 95% confidence): │
│      U_95 = 1.96 * u_c                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Regime-Dependent Uncertainty Expansion

A critical physical insight in aerodynamics is that epistemic uncertainty is non-uniform across the flight envelope:

1. **Linear Attached Flow ($\alpha \in [-4^\circ, 8^\circ]$)**:
   - Dominant source: Discretization ($u_{\text{num}} \approx 0.008$) and input tolerances.
   - Combined $U_{95} \approx \pm 0.053$.
   - Classification: `HIGH_CONFIDENCE`.

2. **Pre-Stall Boundary Layer Thickening ($\alpha \in [8^\circ, 12^\circ]$)**:
   - Viscous-inviscid interaction begins.
   - Combined $U_{95} \approx \pm 0.054$.
   - Classification: `MODERATE_CONFIDENCE`.

3. **Non-Linear Stall & Flow Separation ($\alpha \ge 12^\circ$)**:
   - Severe boundary layer separation renders low-order potential models invalid and triggers high Reynolds-Averaged Navier-Stokes (RANS) turbulence modeling discrepancies ($u_{\text{turb}} = 0.065$).
   - Combined $U_{95} \approx \pm 0.134$.
   - Classification: `HIGH_EPISTEMIC_UNCERTAINTY`.
   - The system strictly flags this regime and requires external high-fidelity CFD or user execution before asserting design safety.
