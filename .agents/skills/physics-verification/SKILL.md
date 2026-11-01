---
name: physics-verification
description: Rigorous verification and validation procedures conforming to ASME V&V 20-2009 and NASA-STD-7009B CAS: Richardson extrapolation, grid convergence index (GCI), asymptotic range checks, and analytical solution comparisons.
---

# Physics Verification & Validation (ASME V&V 20 & NASA-STD-7009B)

## 1. Discretization Error Estimation (ASME V&V 20-2009)
- **Grid Refinement Ratio**:
  $$r = \left(\frac{N_{fine}}{N_{coarse}}\right)^{1/D}$$
  where $r \ge 1.3$ across 3 systematically refined grids ($h_1 < h_2 < h_3$).
- **Observed Order of Accuracy ($p$)**:
  $$p = \frac{\ln\left(\frac{f_3 - f_2}{f_2 - f_1}\right)}{\ln(r)}$$
- **Richardson Extrapolation**:
  $$f_{extrapolated} = f_1 + \frac{f_1 - f_2}{r^p - 1}$$
- **Grid Convergence Index ($GCI$)**:
  $$GCI_{fine} = \frac{F_s |\epsilon_{21}|}{r^p - 1}$$
  where safety factor $F_s = 1.25$ for 3-grid systematic studies.
- **Asymptotic Range Verification**:
  Check ratio:
  $$\frac{GCI_{medium}}{r^p \cdot GCI_{fine}} \approx 1.0 \pm 0.05$$

## 2. NASA-STD-7009B Credibility Assessment Scorecard (CAS)
Evaluate 8 key pillars on a scale of 0 to 4:
1. **Development Pedigree**: Documented physical equations and governing assumptions.
2. **Verification**: Code verification (order of accuracy) and solution verification (GCI).
3. **Empirical Validation**: Comparison against canonical benchmark datasets (NASA LTPT, AGARD AR-138).
4. **Input Pedigree**: Traceable geometric coordinates and atmospheric boundary conditions.
5. **Uncertainty Quantification**: 95% expanded confidence intervals (GUM standard).
6. **Results Robustness**: Sensitivity derivatives and boundary breakdown alerts.
7. **Use History**: Regression test suite coverage across aerospace families.
8. **M&S Process & Quality**: Immutable cryptographic audit logs and configuration control.

