# AASI Phase 20 Scientific Methodology & Evaluation Protocols

**Document ID:** AASI-METH-PHASE20-001  
**Status:** Canonical Scientific Methodology Specification  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Date:** September 13, 2026  
**Governing Rule:** Absolute Anti-Fabrication Rule (Zero synthetic placeholders, fail-closed evaluation)

---

## 1. Scientific Hypotheses & Evidence Criteria

Phase 20 formulates four explicit scientific hypotheses:

### Hypothesis H1: Geometry-Aware Representation
> **Hypothesis:** Explicit geometry coordinate representations (Representations B, C, D) improve generalization to unseen airfoil geometries compared with low-dimensional scalar engineering descriptors (Representation A).
- **Target Metric:** Geometry-OOD $R^2$ on held-out test shapes.
- **Evaluation Criteria:**
  - `SUPPORTED`: Geometry-OOD $R^2$ improves over baseline ($R^2 > -7.777$) by at least $+2.0$ with zero increase in physical violations.
  - `PARTIALLY_SUPPORTED`: Geometry-OOD $R^2$ improves, but remains negative or exhibits localized instability.
  - `NOT_SUPPORTED`: Coordinate representations produce equal or worse $R^2$ compared with engineering descriptors.
  - `INCONCLUSIVE`: Insufficient authentic samples to determine significance.

### Hypothesis H2: Physics-Constrained Learning
> **Hypothesis:** Physics-informed regularization reduces unphysical aerodynamic predictions (negative drag, non-monotonic lift, excessive stagnation pressure) without degrading in-domain accuracy beyond 5% relative $R^2$.
- **Target Metric:** Physical violation count across validation sweep and $R^2_{\text{ID}}$ retention.
- **Evaluation Criteria:**
  - `SUPPORTED`: Zero drag positivity or stagnation violations with $R^2_{\text{ID}} \ge 0.95 \cdot R^2_{\text{unconstrained}}$.
  - `NOT_SUPPORTED`: Regularization fails to eliminate violations or degrades valid-domain $R^2$ by more than 5%.

### Hypothesis H3: Calibrated Uncertainty Quantification
> **Hypothesis:** Conformal and ensemble uncertainty quantification provides empirically calibrated error bounds on held-out test splits, identifying geometry regions where predictions are unreliable.
- **Target Metric:** Empirical coverage $| \text{Coverage}_{0.95} - 0.95 | \le 0.08$ on validation split, and interval width correlation with true error magnitude.
- **Evaluation Criteria:**
  - `SUPPORTED`: Empirical coverage is within nominal bounds ($87\% \le \text{Coverage} \le 100\%$) and sharpness remains bounded.
  - `NOT_SUPPORTED`: Model remains severely overconfident (coverage $< 80\%$) or underconfident (coverage $= 100\%$ with infinite interval width).

### Hypothesis H4: Active Scientific Experimentation
> **Hypothesis:** Targeted active learning case selection (combining epistemic uncertainty, OOD distance, and parameter diversity) identifies high-value CFD experiments that reduce surrogate epistemic uncertainty more efficiently than non-targeted sampling.
- **Target Metric:** Acquisition ranking score and staged case diversity.
- **Evaluation Criteria:**
  - `SUPPORTED`: Active learner successfully stages authentic case decks targeting high-uncertainty regions.
  - `USER_EXECUTED_REQUIRED`: If external CFD solver cannot execute to produce new labels, the active learning validation remains `USER_EXECUTED_REQUIRED` without fabricating completion.

---

## 2. Quantitative Metric Formulations

### 1. Coefficient of Determination ($R^2$)
$$R^2 = 1 - \frac{\sum_{i=1}^n (y_i - \hat{y}_i)^2}{\sum_{i=1}^n (y_i - \bar{y})^2}$$
*Note:* Negative $R^2$ indicates that the model predicts worse than the simple sample mean of the target. Negative values are never clamped to 0.0.

### 2. Root Mean Squared Error (RMSE) & Mean Absolute Error (MAE)
$$\text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2}, \quad \text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|$$

### 3. Empirical Coverage & Miscalibration Delta
$$\text{Coverage}_{1-\alpha} = \frac{1}{n} \sum_{i=1}^n \mathbb{I}\left(y_i \in [\hat{y}_i - z_{\alpha} \hat{\sigma}_i, \, \hat{y}_i + z_{\alpha} \hat{\sigma}_i]\right)$$
$$\Delta_{\text{cal}} = |\text{Coverage}_{1-\alpha} - (1 - \alpha)|$$

### 4. Mean Prediction Interval Width (Sharpness)
$$\bar{W} = \frac{1}{n} \sum_{i=1}^n 2 z_{\alpha} \hat{\sigma}_i$$

---

## 3. Physical Consistency & Law Enforcement

Every prediction $\hat{y} = [\hat{C}_L, \hat{C}_D, \hat{C}_m]$ is evaluated against core fluid mechanics constraints:
1. **Drag Positivity Gate:**
   $$\hat{C}_D(\alpha, Re) > 0 \quad \forall \alpha, Re$$
   A negative drag coefficient violates the second law of thermodynamics (unpowered perpetual motion) and triggers an immediate verification failure.
2. **Stagnation Pressure Coefficient Ceiling:**
   $$\hat{C}_p(x) \le 1.0 \quad \text{in incompressible / subsonic flow}$$
3. **Attached-Flow Lift Monotonicity:**
   $$\frac{\partial \hat{C}_L}{\partial \alpha} > 0 \quad \text{for } \alpha \in [-4^\circ, 8^\circ]$$
