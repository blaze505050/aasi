# AASI Phase 20: Geometry-Aware Representation Specification

**Document ID:** AASI-SPEC-PHASE20-GEOM-001  
**Status:** Canonical Geometry Specification  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Date:** September 13, 2026  
**Governing Rule:** Absolute Anti-Fabrication Rule

---

## 1. Mathematical Abstraction

The airfoil geometry is represented as an ordered discrete set of 2D coordinates:
$$G = \left(x_i, y_i\right)_{i=1}^N \subset \mathbb{R}^2$$
where points are ordered from the upper trailing edge, clockwise around the leading edge, and back to the lower trailing edge.

### Normalization Pipeline
1. **Chord Scaling:** $x_i \leftarrow \frac{x_i - \min(x)}{\max(x) - \min(x)}$, $y_i \leftarrow \frac{y_i}{\text{chord}}$
2. **Leading Edge Translation:** $(x_{\text{LE}}, y_{\text{LE}}) \to (0.0, 0.0)$
3. **Arc-Length Resampling:** Parametrization along contour length $s$:
   $$s_k = \sum_{j=1}^k \sqrt{(x_j - x_{j-1})^2 + (y_j - y_{j-1})^2}$$
   Evaluated at $N$ uniform arc-length nodes $s_i \in [0, s_{\text{total}}]$.

---

## 2. Cryptographic Geometry Identity

To guarantee deterministic provenance, normalized coordinates are rounded to 6 decimal places and serialized to JSON without whitespace:
$$\mathcal{H}_{\text{geom}} = \text{SHA-256}\left(\text{JSON}\left(\text{round}(G, 6)\right)\right)$$
Two airfoils with identical physical contours resolve to the exact same hash, preventing duplicate dataset entries.

---

## 3. Four Experimental Representations

| ID | Representation Name | Dimensionality | Formula / Features |
| :--- | :--- | :--- | :--- |
| **A** | Engineering Descriptors | 6 | $[\alpha, Re, t/c, m, p, \alpha^2]$ |
| **B** | Flattened Coordinates | $2N + 4$ ($N=64 \to 132$) | $[x_1, y_1, \dots, x_N, y_N, \alpha, \log_{10}(Re), M, \alpha^2]$ |
| **C** | Surface Separation | $2M + 4$ ($M=32 \to 68$) | $[y_u(x_1), \dots, y_u(x_M), y_l(x_1), \dots, y_l(x_M), \alpha, \log_{10}(Re), M, \alpha^2]$ |
| **D** | Hybrid Representation | 17 | Descriptors (6) + Local $t(x)$ at 5 stations + Local $m(x)$ at 5 stations + $r_{\text{LE}}$ proxy |

---

## 4. Quantitative Distribution Distance Metrics

1. **Contour Hausdorff Distance:** Maximum distance from any point on contour $A$ to nearest point on contour $B$:
   $$d_H(A, B) = \max\left(\max_{a \in A} \min_{b \in B} \|a - b\|, \, \max_{b \in B} \min_{a \in A} \|b - a\|\right)$$
2. **Mean Euclidean Contour Distance:** Pointwise $L_2$ average on arc-length resampled nodes:
   $$\bar{d}_E(A, B) = \frac{1}{N} \sum_{i=1}^N \|a_i - b_i\|_2$$
3. **Parameter Mahalanobis Distance:** Distance in standardized feature space weighted by inverse covariance $\Sigma^{-1}$.
