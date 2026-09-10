# Grid Convergence Index & Richardson Extrapolation

## Methodology Overview (ASME V&V 20-2009 Standard)

Numerical solutions from Computational Fluid Dynamics (CFD) are inherently contaminated by spatial discretization error. To verify whether a CFD solution is in the asymptotic range of convergence and quantify mesh uncertainty, AASI implements the **Roache / Celik / ASME V&V 20** standard procedure in `backend/validation/grid_convergence.py`.

---

## The 5-Step ASME V&V 20 Formulation

Given three geometrically similar grid solutions:
- $f_1$: Fine grid solution (mesh spacing $h_1$)
- $f_2$: Medium grid solution (mesh spacing $h_2$)
- $f_3$: Coarse grid solution (mesh spacing $h_3$)
- Grid refinement ratios: $r_{21} = h_2 / h_1 > 1.0$, $r_{32} = h_3 / h_2 > 1.0$ (recommended $r \ge 1.3$).

### 1. Differences & Convergence Ratio
$$\epsilon_{21} = f_2 - f_1, \quad \epsilon_{32} = f_3 - f_2$$
$$R = \frac{\epsilon_{21}}{\epsilon_{32}}$$
- $0 < R < 1$: **Monotonic convergence** (differences shrink on refinement)
- $-1 < R < 0$: **Oscillatory convergence**
- $R > 1$: **Monotonic divergence**
- $R < -1$: **Oscillatory divergence**.

### 2. Apparent Order of Convergence ($p$)
For equal refinement ratios ($r_{21} = r_{32} = r$):
$$p = \frac{\ln|\epsilon_{32} / \epsilon_{21}|}{\ln(r)}$$

For non-constant refinement ratios ($r_{21} \neq r_{32}$), fixed-point transcendental solve:
$$p = \frac{1}{\ln(r_{21})} \left| \ln\left|\frac{\epsilon_{32}}{\epsilon_{21}}\right| + q(p) \right|, \quad q(p) = \ln\left( \frac{r_{21}^p - s}{r_{32}^p - s} \right)$$
where $s = \text{sign}(\epsilon_{32} / \epsilon_{21})$.

### 3. Richardson Extrapolated Zero-Grid Value ($f_{ext}$)
$$f_{ext}^{21} = \frac{r_{21}^p f_1 - f_2}{r_{21}^p - 1}$$

### 4. Approximate & Extrapolated Relative Error
$$e_a^{21} = \left| \frac{f_1 - f_2}{f_1} \right|, \quad e_{ext}^{21} = \left| \frac{f_{ext}^{21} - f_1}{f_{ext}^{21}} \right|$$

### 5. Grid Convergence Index (GCI)
With standard safety factor $F_s = 1.25$ for 3-grid studies:
$$\text{GCI}_{fine}^{21} = \frac{1.25 \, e_a^{21}}{r_{21}^p - 1}$$
$$\text{GCI}_{medium}^{32} = \frac{1.25 \, e_a^{32}}{r_{32}^p - 1}$$

### 6. Verification of Asymptotic Range
$$\text{Asymptotic Ratio} = \frac{\text{GCI}_{medium}^{32}}{r_{21}^p \, \text{GCI}_{fine}^{21}} \approx 1.0$$
If the ratio lies within $[0.85, 1.15]$, the solutions are mathematically confirmed to be in the asymptotic range of convergence.

---

## NACA 0012 Benchmark Verification Study

Subsonic RANS simulation (Mach 0.15, $Re = 3\times 10^6$, $\alpha = 4.0^\circ$, Spalart-Allmaras turbulence model):
- Fine Grid ($N_1 = 256,000$ cells, $h_1 = 1.0$): $C_L = 0.4285$, $C_D = 0.00845$
- Medium Grid ($N_2 = 64,000$ cells, $h_2 = 1.414$): $C_L = 0.4210$, $C_D = 0.00868$
- Coarse Grid ($N_3 = 16,000$ cells, $h_3 = 2.0$): $C_L = 0.4070$, $C_D = 0.00912$

### Results:
- **Observed Apparent Order ($p$):** `1.801` (close to formal 2nd order accuracy)
- **Richardson Extrapolated Value ($C_{L, ext}$):** `0.4371`
- **Fine Grid Discretization Uncertainty ($\text{GCI}_{fine}$):** `2.52%`
- **Medium Grid Discretization Uncertainty ($\text{GCI}_{med}$):** `4.67%`
- **Convergence Regime:** `MONOTONIC_CONVERGENCE`
