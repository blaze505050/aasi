# AASI Phase 21 Scientific Methodology & Hypotheses

**Document ID:** AASI-METH-PHASE21-001  
**Status:** Canonical Scientific Specification  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Governing Rule:** Absolute Anti-Fabrication Rule  

---

## 1. Central Scientific Question

Phase 21 addresses the fundamental question:
> **"Can AASI autonomously identify scientifically valuable aerodynamic experiments, execute or externally validate them using real physics solvers, assimilate the resulting data, update its surrogate, quantify uncertainty, and select the next experiment without fabricating any missing evidence?"**

The core pipeline is defined by:
$$\text{REAL DATA} \longrightarrow \text{GEOMETRY} \longrightarrow \text{SOLVER / EXPERIMENT} \longrightarrow \text{OBSERVATIONS} \longrightarrow \text{SURROGATE} \longrightarrow \text{CALIBRATED UNCERTAINTY} \longrightarrow \text{ACQUISITION} \longrightarrow \text{SELECTION} \longrightarrow \text{VALIDATION} \longrightarrow \text{UPDATE}$$

---

## 2. Five Formal Scientific Hypotheses

### Hypothesis H1: Real CFD Closure & Solver Adapter
- **Statement:** AASI can automatically submit, monitor, validate, and ingest a genuine OpenFOAM aerodynamic simulation across 5 operational execution modes (Native Linux, WSL2, Docker, Remote API, Degraded/No Solver), establishing solver convergence from residual and force histories rather than trivial exit codes.
- **Null Hypothesis ($H_{1,0}$):** The system cannot reliably determine simulation convergence or solver availability without manual intervention, or requires synthetic fallbacks.
- **Success Criteria:**
  1. Live probing of host solver availability without hardcoded assumptions.
  2. Complete extraction of residual history ($p, Ux, Uy, k, \omega$) and force histories ($C_L, C_D, C_M$).
  3. Multi-criteria convergence gate: residual decay $< 10^{-4}$ and force variance $\le 0.5\%$.
  4. Honest reporting of `USER_EXECUTED_REQUIRED` or `SOLVER_UNAVAILABLE` when execution environment is absent.

### Hypothesis H2: Multi-Fidelity Surrogate Discrepancy Modeling
- **Statement:** Combining low-fidelity aerodynamic approximations ($\text{FIDELITY}_0 / \text{FIDELITY}_1$: analytical thin-airfoil theory and panel methods) with sparse high-fidelity Navier-Stokes CFD ($\text{FIDELITY}_2 / \text{FIDELITY}_3$: RANS $k$-$\omega$ SST) via residual discrepancy modeling improves out-of-distribution generalization compared to high-fidelity data alone.
- **Mathematical Formulation:**
  $$y_{\text{high}}(x) = y_{\text{low}}(x) + \delta(x) + \epsilon$$
  where $y_{\text{low}}(x)$ captures the global macroscopic aerodynamic trends and $\delta(x)$ models the viscous boundary-layer, separation, and wake discrepancy.
- **Null Hypothesis ($H_{2,0}$):** Multi-fidelity discrepancy modeling yields higher prediction error or masks high-fidelity physics disagreement compared to direct high-fidelity modeling.
- **Success Criteria:**
  1. Explicit multi-fidelity data schema recording fidelity level ($\text{FIDELITY}_0 \dots \text{FIDELITY}_4$).
  2. Residual model $\hat{f}_{\text{multi}}(x) = \hat{f}_{\text{low}}(x) + \hat{\delta}(x)$ evaluated against pure high-fidelity baseline.
  3. Strict refusal to label low-fidelity data as CFD.

### Hypothesis H3: Operator-Level Field Learning vs Scalar Prediction
- **Statement:** Predicting the continuous surface pressure coefficient distribution $C_p(x/c)$ and recovering aerodynamic forces via numerical integration produces physically consistent aerodynamics and superior geometry generalization compared to unconstrained scalar output models.
- **Mathematical Formulation:**
  $$\hat{C}_L^{\text{field}} = \int_0^1 (C_{p,\text{lower}}(x/c) - C_{p,\text{upper}}(x/c)) \, d(x/c) \cos\alpha + \dots$$
  $$\hat{C}_D^{\text{field}} = \int_0^1 (C_{p,\text{upper}}(x/c) - C_{p,\text{lower}}(x/c)) \frac{dy}{dx} \, d(x/c) + C_{D,\text{friction}}$$
- **Null Hypothesis ($H_{3,0}$):** Field-integrated force coefficients exhibit worse out-of-distribution generalization or fail stagnation pressure limits compared to direct scalar surrogates.
- **Success Criteria:**
  1. Continuous $C_p(x/c)$ prediction across upper and lower airfoil contours.
  2. Stagnation check ($C_p \le 1.0$) and suction-peak continuity check.
  3. Comparison of direct $\hat{C}_L, \hat{C}_D$ vs field-integrated $\hat{C}_L^{\text{field}}, \hat{C}_D^{\text{field}}$.

### Hypothesis H4: Adaptive Distance-Conditioned Conformal Uncertainty
- **Statement:** Scaling split conformal nonconformity intervals as a monotonically increasing function of out-of-distribution distance ($d_{\text{OOD}}$) maintains valid empirical coverage ($\ge 1 - \alpha$) under severe geometric and flow regime shifts where standard split conformal prediction fails.
- **Mathematical Formulation:**
  $$I_{\text{adaptive}}(x) = \left[ \hat{\mu}(x) - \hat{q}_{\alpha} \cdot \hat{\sigma}(x) \cdot (1 + \gamma \cdot d_{\text{OOD}}(x)), \quad \hat{\mu}(x) + \hat{q}_{\alpha} \cdot \hat{\sigma}(x) \cdot (1 + \gamma \cdot d_{\text{OOD}}(x)) \right]$$
- **Null Hypothesis ($H_{4,0}$):** Distance-conditioned conformal intervals do not significantly improve empirical coverage under joint OOD distribution shifts compared to fixed-width conformal prediction.
- **Success Criteria:**
  1. Empirical test coverage evaluated across in-distribution, geometry-OOD, Reynolds-OOD, AoA-OOD, and joint-OOD tiers.
  2. Quantitative comparison of standard vs distance-conditioned conformal prediction.

### Hypothesis H5: Closed-Loop Autonomous Scientific Discovery
- **Statement:** An autonomous discovery controller integrating multi-objective acquisition ranking, fail-closed solver execution, real-time physical validation, and automatic retrain/reevaluate cycles successfully executes iterative scientific investigations until triggered by rigorous stopping criteria.
- **Stopping Criteria:**
  1. **Evidence Saturation:** Expected Information Gain (EIG) falls below $\tau_{\text{EIG}} = 0.01$.
  2. **Performance Convergence:** $\Delta R^2_{\text{OOD}} < 0.005$ across 3 successive iterations.
  3. **Uncertainty Convergence:** Mean epistemic uncertainty reduction $< 2\%$.
  4. **Budget & Safety Reserve:** Available disk falls below $15.0\text{ GB}$ or RAM exceeds $85\%$.
  5. **Integrity / Physical Gate Failure:** Unphysical coefficients ($C_D < 0$) or numerical NaN detected.
- **Null Hypothesis ($H_{5,0}$):** The discovery loop requires human intervention to manage transitions or fails to halt upon encountering budget/safety limits.
