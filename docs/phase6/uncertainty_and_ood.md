# Epistemic Uncertainty Quantification & Out-of-Distribution Routing

## Principles of Scientific Uncertainty

A physical surrogate must know what it does not know. Predicting a single scalar number without an epistemic confidence boundary is unscientific and dangerous for aerospace applications.

`backend/physics_ai/uncertainty.py` (`EpistemicUncertaintyEngine`) evaluates:
1. Hard boundaries against the calibrated validity envelope
2. Feature-space Mahalanobis distance to the training centroid
3. Nearest-neighbor density estimation in normalized condition space
4. Bounded uncertainty estimates ($\pm \sigma_{CL}$, $\pm \sigma_{CD}$, $\pm \sigma_{CM}$).

---

## Mathematical Formulation

### 1. Mahalanobis Feature Distance
Let $x \in \mathbb{R}^3$ be the normalized condition vector $[M, \log_{10}(Re), \alpha]$, $\mu$ the empirical training centroid, and $\Sigma$ the covariance matrix:

$$d_M(x) = \sqrt{(x - \mu)^T \Sigma^{-1} (x - \mu)}$$

### 2. Nearest-Neighbor Density Score
Measures local support in the authentic training manifold:
$$\rho(x) = \exp\left(-1.5 \min_{i \in \text{Train}} \|x - x_i\|_2\right) \in (0, 1]$$

### 3. Out-of-Distribution (OOD) Metric
$$\text{OOD Score} = 0.4 \, d_M(x) + 0.6 \min_{i} \|x - x_i\|_2$$

---

## Domain Classification & Escalation Hierarchy

| Domain Classification | Criteria | Confidence Level | Uncertainty Multiplier | Routing Action |
| :--- | :--- | :--- | :--- | :--- |
| **`IN_DOMAIN`** | Within envelope, $\text{OOD} \le 1.8$, $|\alpha| \le 12^\circ$ | **`HIGH`** (70–98%) | $1.0\times$ ($\sigma_{CL} = 0.015, \sigma_{CD} = 0.0012$) | Return `SURROGATE_PREDICTION` directly |
| **`EXTRAPOLATION_NEAR_BOUNDARY`** | $1.8 < \text{OOD} \le 3.0$ or $12^\circ < |\alpha| \le 18^\circ$ | **`MEDIUM`** (35–69%) | $2.0\times$ ($\sigma_{CL} = 0.030, \sigma_{CD} = 0.0024$) | Return prediction with boundary alert banner |
| **`SURROGATE_OUT_OF_DOMAIN`** | Outside envelope ($M > 0.40$ or $Re > 6\times 10^6$) or $\text{OOD} > 3.0$ | **`OOD`** (&lt; 35%) | $4.0\times$ | **Reject surrogate inference.** Fall through to Level 5 (Analytical) or Level 6 (Simulation Fabric) |

---

## Scientific Resolution Level 4 Escalation Integration

When an aerodynamic query is received:
```
User Query: "Drag coefficient of NACA 0012 at Mach 0.85"
  ↓
ScientificResolutionEngine (Level 4 Check)
  ↓
Operational Envelope: Mach 0.85 > 0.40 max envelope
  ↓
Status: SURROGATE_OUT_OF_DOMAIN
  ↓
Action: Rejects surrogate inference. NEVER fabricates transonic drag.
  ↓
Escalates to Level 5 (Analytical) -> Level 6 (Local Solvers) -> Level 7 (NO_RESULT)
```
