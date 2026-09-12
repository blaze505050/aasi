# AASI Dataset Generalization & Out-of-Distribution (OOD) Protocol

**Document ID**: `OOD-GENERALIZATION-PROTOCOL-01`  
**Governing Standard**: AASI Physics-AI Scientific Generalization Standard  
**Last Updated**: 2026-09-12  

---

## 1. Motivation: The Failure of Random Cross-Validation in Physics AI

Traditional machine learning relies on random i.i.d. (independent and identically distributed) train/test splits. In computational fluid dynamics, naive random splitting produces massive performance overestimation:
1. **Geometric Leakage**: The test set contains meshes of identical airfoils to those seen during training, merely at slight variations in velocity or angle of attack. The model memorizes boundary layer shapes rather than learning Navier-Stokes dynamics.
2. **In-Domain Interpolation**: Models evaluated strictly inside their training convex hull fail catastrophically when presented with separated stall regimes or higher Reynolds numbers.

AASI formalizes rigorous **Out-of-Distribution (OOD)** benchmarking across three distinct physical axes.

---

## 2. The Three Axes of Physical Generalization

```
                          [ Generalization Space ]
                                    ▲
                                    │  High Reynolds Extrapolation
                                    │  (Re > 4.5e6)
                                    │
                                    ┼───────────► Unseen Geometry
                                   /              (Supercritical / Novel NACA)
                                  /
                                 ▼
                     High Angle of Attack (AoA > 9°)
                     Separated Flow / Stall Regime
```

### 2.1 Geometric Generalization (`full_test` & `scarce_train`)
- **Training Set**: NACA 4-digit profiles with moderate camber ($m \le 0.04c$) and thickness ($t \in [0.09c, 0.15c]$).
- **Test Set**: Procedural NACA 5-digit profiles and extreme camber/thickness profiles ($t > 0.18c$, high-lift reflexed camber).
- **Integrity Rule**:
  $$\text{Intersection}(\text{Geometries}_{\text{train}}, \text{Geometries}_{\text{test}}) = \emptyset$$

### 2.2 Reynolds Number Generalization (`reynolds_test`)
- **In-Domain Training**: $Re \in [2.0 \times 10^6, 4.0 \times 10^6]$ (thick boundary layers, moderate skin friction).
- **OOD Testing**: $Re \in [4.5 \times 10^6, 6.0 \times 10^6]$ (thinner viscous sublayers, heightened turbulence production).
- **Evaluation Metric**: Relative error degradation ratio:
  $$\Delta_{\text{OOD}} = \frac{\text{RMSE}_{Re \text{ OOD}} - \text{RMSE}_{\text{IID}}}{\text{RMSE}_{\text{IID}}}$$

### 2.3 Angle of Attack & Stall Generalization (`aoa_test`)
- **In-Domain Training**: $\alpha \in [-5.0^\circ, 8.0^\circ]$ (linear attached potential-like flow regime).
- **OOD Testing**: $\alpha \in [9.0^\circ, 15.0^\circ]$ (leading-edge adverse pressure gradients, boundary layer separation, trailing-edge stall).
- **Evaluation Metric**: Lift slope breakdown error:
  $$\epsilon_{\text{stall}} = |C_{L,\text{pred}}(\alpha_{\text{stall}}) - C_{L,\text{CFD}}(\alpha_{\text{stall}})|$$

---

## 3. Mathematical Metric: Normalized OOD Distance

To quantify how far a test simulation resides outside the training convex hull, AASI implements normalized boundary distance:

$$d_{\text{OOD}}(x; [x_{\min}, x_{\max}]) = \begin{cases}
0, & \text{if } x_{\min} \le x \le x_{\max} \\
\frac{x_{\min} - x}{x_{\max} - x_{\min}}, & \text{if } x < x_{\min} \\
\frac{x - x_{\max}}{x_{\max} - x_{\min}}, & \text{if } x > x_{\max}
\end{cases}$$

When $d_{\text{OOD}} > 0$, the case is classified as out-of-distribution, and errors are tracked in the OOD generalization ledger rather than standard validation loss.

---

## 4. Benchmark Workflow in AASI

1. Models are trained on `full_train`, `reynolds_train`, or `aoa_train`.
2. Evaluator queries `DataSplitManager.evaluate_ood_distance(case, variable, bounds)`.
3. If `is_ood == True`, an `OOD_EVALUATION` node is minted in the research evidence ledger, recording both prediction error and normalized parameter distance.
4. Scientific reports tabulate IID vs OOD error decay, preventing misleading benchmark claims.
