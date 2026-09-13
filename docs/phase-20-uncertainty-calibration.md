# AASI Phase 20: Uncertainty Quantification & Calibration Specification

**Document ID:** AASI-SPEC-PHASE20-UQ-001  
**Status:** Canonical Calibration Specification  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Date:** September 13, 2026  
**Governing Rule:** Absolute Anti-Fabrication Rule

---

## 1. The Calibration Imperative

In aerodynamic design, an overconfident surrogate is catastrophic. A model that reports a 95% confidence interval that only covers 50% of true values will lead an autonomous scientist to make false claims of optimal performance or stability.

Phase 19 baseline revealed that standard Bayesian linear regression suffers from severe overconfidence under distribution shift ($50.0\%$ empirical coverage vs $95.0\%$ target). Phase 20 resolves this via Split Conformal Prediction and an empirical hard calibration gate.

---

## 2. Split Conformal Prediction Formulation

Given a trained surrogate $\hat{f}$ and an independent calibration set $\mathcal{D}_{\text{cal}} = \{(x_i, y_i)\}_{i=1}^n$:
1. **Non-Conformity Scoring:**
   $$s_i = \max_{j} \frac{|y_{i,j} - \hat{f}_j(x_i)|}{\hat{\sigma}_j(x_i) + \epsilon}$$
2. **Conformal Quantile:**
   $$\hat{q} = \text{Quantile}\left(\{s_i\}_{i=1}^n, \, \frac{\lceil (n+1)(1-\alpha)\rceil}{n}\right)$$
3. **Finite-Sample Prediction Interval:**
   $$\mathcal{C}(x) = \left[\hat{f}(x) - \hat{q} \cdot \hat{\sigma}(x), \, \hat{f}(x) + \hat{q} \cdot \hat{\sigma}(x)\right]$$
   guarantees:
   $$\mathbb{P}\left(y \in \mathcal{C}(x)\right) \ge 1 - \alpha$$

---

## 3. Hard Calibration Gate Protocol

A model can only receive the status `UNCERTAINTY_CALIBRATED` if:
$$|\text{Empirical Coverage}_{0.95} - 0.95| \le 0.08$$
and
$$\text{Empirical Coverage}_{0.95} \ge 0.87$$

If empirical coverage is below $87\%$, the model is classified as `UNCERTAINTY_NOT_CALIBRATED` and its scientific promotion is blocked.
