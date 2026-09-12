# AASI Multi-Dataset Aerodynamic Uncertainty Framework

**Document ID**: `UNC-MULTI-DATASET-01`  
**Governing Standard**: ISO/IEC Guide 98-3 (GUM) & ASME V&V 20  
**Last Updated**: 2026-09-12  

---

## 1. Mathematical Formulation

When comparing surrogate models against multi-source datasets (such as wind tunnel polars and RANS simulations), deterministic point comparisons are scientifically invalid. AASI decomposes uncertainty into five distinct components:

$$u_c = \sqrt{u_{\text{input}}^2 + u_{\text{numerical}}^2 + u_{\text{model}}^2 + u_{\text{measurement}}^2}$$

The expanded uncertainty at the 95% confidence level ($k = 1.96$) is:
$$U_{95} = 1.96 \cdot u_c$$

---

## 2. Five-Tier Uncertainty Breakdown

### 2.1 Input Uncertainty ($u_{\text{input}}$)
Uncertainty propagated from flight condition tolerances:
- $\delta M = \pm 0.002$
- $\delta \alpha = \pm 0.05^\circ$
- $\delta Re / Re = \pm 1.0\%$
- Propagated lift error:
  $$u_{\text{input}} = \left| \frac{\partial C_L}{\partial \alpha} \right| \delta \alpha \approx 0.1097 \cdot 0.05 = 0.0055$$

### 2.2 Numerical Discretization Uncertainty ($u_{\text{numerical}}$)
Derived from ASME V&V 20 Grid Convergence Index (GCI) and iterative residual monitoring:
- Fine grid GCI on $C_L$: $GCI_{\text{fine}} \approx 0.0080$
- Iterative convergence residual: $\epsilon_{\text{iter}} \approx 0.0002$
- $$u_{\text{numerical}} = \sqrt{GCI^2 + \epsilon_{\text{iter}}^2} \approx 0.0082$$

### 2.3 Model & Turbulence Closure Uncertainty ($u_{\text{model}}$)
Captures surrogate epistemic uncertainty and turbulence model discrepancy:
- Surrogate epistemic standard deviation: $\sigma_{\text{surrogate}} \approx 0.0150$
- Turbulence model closure (Spalart-Allmaras vs Experiment):
  - Linear regime ($\alpha < 12^\circ$): $\delta_{\text{turb}} \approx 0.0200$
  - Stall regime ($\alpha \ge 12^\circ$): $\delta_{\text{turb}} \approx 0.0650$
- $$u_{\text{model}} = \sqrt{\sigma_{\text{surrogate}}^2 + \delta_{\text{turb}}^2}$$

### 2.4 Experimental Measurement Uncertainty ($u_{\text{measurement}}$)
Facility balance accuracy from NASA Langley LTPT calibration reports (NASA TM-4083):
- Sectional force balance accuracy: $u_{\text{meas}} = \pm 0.0050 C_L$, $\pm 0.0003 C_D$.

### 2.5 Combined Multi-Dataset Budget

| Regime | Input $u_{\text{inp}}$ | Numerical $u_{\text{num}}$ | Model $u_{\text{mod}}$ | Meas $u_{\text{meas}}$ | Combined $u_c$ | Expanded $U_{95}$ |
|---|---|---|---|---|---|---|
| **Linear ($\alpha = 8^\circ$)** | 0.0055 | 0.0082 | 0.0250 | 0.0050 | **0.0275** | **$\pm 0.0539$** |
| **Stall ($\alpha = 14^\circ$)** | 0.0055 | 0.0082 | 0.0667 | 0.0050 | **0.0677** | **$\pm 0.1326$** |

---

## 3. Decision Rule for Model Acceptance

A surrogate prediction $C_{L,\text{pred}}$ is scientifically consistent with dataset ground truth $C_{L,\text{data}}$ if and only if:
$$\left| C_{L,\text{pred}} - C_{L,\text{data}} \right| \le U_{95}$$

If discrepancy exceeds $U_{95}$, the result is classified as a physics discrepancy requiring either model retraining or mesh refinement, and is automatically tagged in the AASI research ledger.
