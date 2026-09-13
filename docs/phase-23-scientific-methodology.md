# AASI Phase 23 Scientific Methodology: Verification, Validation & Autonomous Discovery

**Directive:** AASI Master Engineering Directive — Phase 23  
**Governing Doctrine:** Absolute Anti-Fabrication Rule  
**System:** Autonomous Aerospace Scientific Investigator (AASI)  

---

## 1. Scientific Verification & Validation Framework

AASI Phase 23 implements a dual verification and validation (V&V) architecture aligned with **ASME V&V 20** (Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer) and AIAA G-077-1998 guidelines.

### 1.1 Numerical Verification (Code and Solution Verification)
- **Geometry Preflight:** Before meshing, the airfoil profile is evaluated for:
  1. *Geometric Closure:* Euclidean distance $|(x_0, y_0) - (x_N, y_N)| \le 10^{-4}$ chord.
  2. *Self-Intersection:* Ray-casting and orientation tests guarantee the upper and lower surfaces do not intersect between $x \in (0, 1)$.
  3. *Chord Normalization:* Boundary coordinates are strictly rescaled such that $x_{\min} = 0.0$ and $x_{\max} = 1.0$.
- **Solution Verification (Convergence):**
  A solution is verified converged only when:
  $$\max\left(r_p, r_{Ux}, r_{Uy}, r_k, r_\omega\right) < 1.0 \times 10^{-4}$$
  and the aerodynamic force variation over the final 100 iterations satisfies:
  $$\frac{|\Delta C_L|}{C_L} \le 0.005, \quad \frac{|\Delta C_D|}{C_D} \le 0.005$$

### 1.2 Physical Validation Gate
Raw solver outputs are subjected to automated physics gates before ingestion:
1. **Bernoulli Stagnation Limit:**
   $$C_{p,\max} \le 1.05$$
2. **Suction Peak Check:** For positive angles of attack ($\alpha > 0$):
   $$C_{p,\min} < 0.0$$
3. **Viscous Drag Positivity:**
   $$C_D > 0.0$$
4. **Physical Subsonic Lift Bounds:**
   $$-2.5 \le C_L \le 3.5$$
5. **Turbulence Quantity Positivity:**
   $$k \ge 0, \quad \omega \ge 0, \quad \nu_t \ge 0$$

---

## 2. Frozen Test Set Discipline

To prevent data contamination, leakage, and artificial inflation of surrogate metrics, Phase 23 strictly freezes the held-out evaluation dataset created in Phase 22 (`data/experiments/phase22_frozen_test.json`).

### 2.1 Frozen Dataset Specification
- **File:** `data/experiments/phase22_frozen_test.json`
- **SHA-256 Checksum:**
  $$\mathbf{H}_{\text{frozen}} = \texttt{9bc0be258074900a35942fc6977ca3ffda73ad7ff392a2a07c3973c52a322421}$$
- **Composition:** 26 test points:
  - NACA 6409 (highly cambered, thin, out-of-distribution geometry) across $\alpha \in \{-4^\circ, -2^\circ, 0^\circ, 2^\circ, 4^\circ, 6^\circ, 8^\circ, 10^\circ, 12^\circ, 14^\circ\}$
  - NACA 4415 (moderately cambered, thick, out-of-distribution geometry) across $\alpha \in \{-4^\circ, -2^\circ, 0^\circ, 2^\circ, 4^\circ, 6^\circ, 8^\circ, 10^\circ, 12^\circ, 14^\circ\}$
  - Flow conditions: Mach $0.15$, Reynolds $3.0 \times 10^6$.

### 2.2 Comparison Metric Thresholds
Surrogate models before and after assimilation of new CFD observations are evaluated on the exact same frozen test set. Metrics computed:
- Coefficient of Determination: $R^2(C_L)$
- Mean Absolute Error: $\text{MAE}(C_L), \text{MAE}(C_D)$
- Root Mean Squared Error: $\text{RMSE}(C_L)$
- Maximum Error: $\max_i |y_i - \hat{y}_i|$

Scientific verdicts are assigned objectively based on the pre-registered equivalence margin $\epsilon = 0.005$:
- **`IMPROVED`:** If $\Delta R^2 > +0.005$ and $\Delta\text{MAE}_{CL} \le 0.0$
- **`DEGRADED`:** If $\Delta R^2 < -0.005$
- **`UNCHANGED`:** If $|\Delta R^2| \le 0.005$

Under the Absolute Anti-Fabrication Rule, `UNCHANGED` is reported with complete scientific pride when new observations do not alter global representation on out-of-distribution profiles.

---

## 3. Model Promotion Governance Hierarchy

AASI enforces a 10-stage model promotion hierarchy. Each promotion requires verified, uncompromised empirical evidence:

```
Stage 1: UNTRAINED
Stage 2: IN_DOMAIN_VALIDATED (R² ≥ 0.90 on in-distribution airfoils)
Stage 3: PHYSICS_CONSTRAINED (CD > 0, pre-stall lift monotonicity)
Stage 4: UNCERTAINTY_CALIBRATED (Conformal coverage ≥ 90%)
Stage 5: CROSS_DATASET_VALIDATED (AirfRANS benchmark generalization)
Stage 6: GEOMETRY_AWARE (Geometric encoding with zero coordinate leakage)
Stage 7: GEOMETRY_OOD_VALIDATED (Bounded error on unseen geometry)
Stage 8: AUTONOMOUS_ACTIVE_LEARNING_VALIDATED (Conformal candidate selection)
Stage 9: REAL_CFD_CLOSED_LOOP_VALIDATED (Live solver execution + physical gates)
Stage 10: SCIENTIFICALLY_TRUSTED (Repeated multi-geometry closed-loop validation)
```

### Stage 9 Requirements
1. The solver must have executed genuinely (local host or verified remote Colab).
2. Complete execution artifacts (logs, residuals, forces, fields) must be cryptographically hashed.
3. The Physical Field Validation Gate must pass without violations.
4. The 12-node Merkle provenance DAG must be complete and uncorrupted.
5. Independent reproduction must confirm bit-identical evaluation.
6. The frozen test set evaluation must be completed without synthetic bypass.

### Stage 10 Requirements
Stage 10 represents the pinnacle of autonomous scientific credibility. It requires at least three independent, successful, closed-loop iterations across diverse aerodynamic profiles. A single successful experiment run is strictly insufficient for Stage 10 promotion.
