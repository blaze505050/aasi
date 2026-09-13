# AASI Phase 20: Model Benchmark Suite Specification

**Document ID:** AASI-SPEC-PHASE20-BENCH-001  
**Status:** Canonical Benchmark Specification  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Date:** September 13, 2026  
**Governing Rule:** Absolute Anti-Fabrication Rule

---

## 1. Unified Model Interface

All benchmark models inherit from `AeroSurrogateBase` (`backend/physics_ai/benchmark_models.py`), enforcing:
- `fit(X, y)`: Deterministic training with fixed seed.
- `predict(X)`: Vectorized inference.
- `predict_with_uncertainty(X)`: Returns point prediction $\hat{y}$ and epistemic uncertainty $\hat{\sigma}$.
- `evaluate(X, y)`: Computes $R^2$, RMSE, MAE, Max Error, and drag positivity violation count.
- `save(path)` / `load(path)`: Cryptographically verified persistence.
- `hash()`: SHA-256 parameter digest.

---

## 2. Model Family

| Model ID | Architecture | Uncertainty Engine | Hardware Footprint |
| :--- | :--- | :--- | :--- |
| `Phase19-Ridge-Baseline` | Analytical SVD $L_2$ Ridge | Bayesian Linear Posterior Covariance | $< 50 \text{ KB}$, $< 0.1 \text{s}$ train |
| `Polynomial-Ridge-Deg2` | Degree-2 Polynomial Expansion + Ridge | Residual Scaled Variance | $< 100 \text{ KB}$, $< 0.2 \text{s}$ train |
| `Random-Forest-Surrogate` | 50 Regression Trees (max depth 10) | Ensemble Tree Variance Across Leaves | $< 2 \text{ MB}$, $< 0.5 \text{s}$ train |
| `Gradient-Boosting-Surrogate`| Staged Gradient Boosting Trees | Empirical Residual Quantile Proxy | $< 1 \text{ MB}$, $< 0.8 \text{s}$ train |
| `Multilayer-Perceptron` | 3-Layer Feed-Forward Neural Net (GELU) | Residual Variance | $< 50 \text{ KB}$, $< 1.2 \text{s}$ train |
| `Geometry-Aware-MLP` | Coordinate Encoder + Flow Fusion | Epistemic Layer Variance | $< 100 \text{ KB}$, $< 1.5 \text{s}$ train |
| `Physics-Constrained` | Regularized Ridge with Positivity Bounds | Projected Parameter Covariance | $< 50 \text{ KB}$, $< 0.1 \text{s}$ train |
| `Model-Ensemble-Surrogate` | Variance-Weighted Linear/Tree Ensemble | Inter-Model Disagreement Standard Dev | $< 3 \text{ MB}$, $< 1.0 \text{s}$ train |

---

## 3. Target Hierarchy

- **Level 1 (Global Aerodynamic Forces):** $[C_L, C_D, C_m]$
- **Level 2 (Surface Distributions):** Pressure coefficient distribution $C_p(x)$
- **Level 3 (Viscous Wall Quantities):** Skin friction distribution $C_f(x)$
- **Level 4 (Physical Integration):** Forces derived directly from integration of $C_p$ and $C_f$:
  $$C_L = \oint C_p \cos(\theta) \, d\tilde{s} + \oint C_f \sin(\theta) \, d\tilde{s}$$
