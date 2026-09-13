# AASI Phase 20: Out-of-Distribution (OOD) Generalization Specification

**Document ID:** AASI-SPEC-PHASE20-OOD-001  
**Status:** Canonical OOD Evaluation Specification  
**Author:** Google DeepMind Pair-Programming Agent (Antigravity) & Lead Aerospace Scientist  
**Date:** September 13, 2026  
**Governing Rule:** Absolute Anti-Fabrication Rule

---

## 1. 7-Tier Evaluation Matrix

To prevent misleading claims of generalizability, all models are evaluated across 7 orthogonal distribution tiers:

| Tier | Name | Target Regime | Pass Criteria |
| :---: | :--- | :--- | :--- |
| **1** | In-Distribution (ID) | Training geometries, $Re \in [2\times 10^6, 4\times 10^6]$, $\alpha \in [0^\circ, 8^\circ]$ | $R^2 \ge 0.85$, $C_D > 0$ |
| **2** | Geometry-OOD | Held-out shapes (NACA 6409, NACA 4415, Clark Y, RAE 2822) | Honest reporting; baseline $R^2 = -7.777$ |
| **3** | Reynolds-OOD | $Re > 10^7$ or $Re < 5\times 10^5$ | `INSUFFICIENT_EVIDENCE` if unacquired |
| **4** | AoA-OOD | $\alpha > 15^\circ$ (post-stall separated flow) | `INSUFFICIENT_EVIDENCE` if unacquired |
| **5** | Joint-OOD | High $\alpha$ + high $Re$ + unseen geometry | `INSUFFICIENT_EVIDENCE` if unacquired |
| **6** | Thickness-OOD | Extremely thin ($t/c \le 0.06$) or thick ($t/c \ge 0.18$) | Honest $R^2$ evaluation |
| **7** | Camber-OOD | High camber profiles ($m \ge 0.04$) | Honest $R^2$ evaluation |

---

## 2. Quantitative Distance Metrics

Every sample evaluated in an OOD tier is annotated with exact distance from the training distribution:
1. **Contour Hausdorff Distance:** $d_H(G_{\text{test}}, G_{\text{train}}) = \max( \dots )$
2. **Mean Euclidean Contour Distance:** $\bar{d}_E(G_{\text{test}}, G_{\text{train}})$
3. **Feature Mahalanobis Distance:** $d_M = \sqrt{(x - \mu)^T \Sigma^{-1} (x - \mu)}$
4. **Normalized Parameter Distance:** $d_P = \|\tilde{x} - \tilde{\mu}\|_2$

A sample is strictly classified as out-of-distribution when:
$$d_M > 2.5 \quad \text{or} \quad d_H > 0.03 \quad \text{or} \quad \text{Geometry} \notin \mathcal{G}_{\text{train}}$$
