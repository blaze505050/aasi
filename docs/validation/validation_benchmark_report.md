# AASI Empirical Validation Benchmark Report

> **Automated Verification Run:** Comparing deterministic panel physics with empirical corrections against authentic wind tunnel datasets.

---

## NACA 0012
- **Reference:** NASA TN-D-628 / Abbott & von Doenhoff (1959)
- **Conditions:** $Re = 3,000,000$, $Mach = 0.15$
- **Error Metrics:** Lift MAE = `0.009`, Drag MAE = `0.0019`
- **Derived Slopes:** $C_{L_\alpha} = 0.1086^\circ$, $\alpha_{0L} = 0.0^\circ$, $C_{D0} = 0.006$

| Alpha (deg) | Exp Cl | AASI Cl | Delta Cl | Exp Cd | AASI Cd | Delta Cd |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.0° | 0.000 | 0.000 | 0.0000 | 0.0058 | 0.0060 | 0.0002 |
| 2.0° | 0.220 | 0.217 | 0.0029 | 0.0068 | 0.0063 | 0.0005 |
| 4.0° | 0.440 | 0.434 | 0.0058 | 0.0082 | 0.0071 | 0.0011 |
| 6.0° | 0.650 | 0.651 | 0.0013 | 0.0105 | 0.0085 | 0.0020 |
| 8.0° | 0.860 | 0.868 | 0.0084 | 0.0135 | 0.0105 | 0.0030 |
| 10.0° | 1.050 | 1.085 | 0.0354 | 0.0178 | 0.0131 | 0.0047 |

---

## NACA 4412
- **Reference:** Abbott & von Doenhoff, Theory of Wing Sections
- **Conditions:** $Re = 3,000,000$, $Mach = 0.15$
- **Error Metrics:** Lift MAE = `0.0363`, Drag MAE = `0.0014`
- **Derived Slopes:** $C_{L_\alpha} = 0.1085^\circ$, $\alpha_{0L} = -4.0^\circ$, $C_{D0} = 0.0068$

| Alpha (deg) | Exp Cl | AASI Cl | Delta Cl | Exp Cd | AASI Cd | Delta Cd |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| -4.0° | 0.000 | 0.000 | 0.0000 | 0.0068 | 0.0080 | 0.0012 |
| 0.0° | 0.410 | 0.434 | 0.0242 | 0.0075 | 0.0068 | 0.0007 |
| 4.0° | 0.830 | 0.868 | 0.0384 | 0.0094 | 0.0079 | 0.0015 |
| 8.0° | 1.220 | 1.302 | 0.0825 | 0.0135 | 0.0114 | 0.0021 |

---

## Eppler E387
- **Reference:** UIUC Low-Speed Airfoil Tests (Vol 1-5, Selig et al.)
- **Conditions:** $Re = 200,000$, $Mach = 0.05$
- **Error Metrics:** Lift MAE = `0.3869`, Drag MAE = `0.0069`
- **Derived Slopes:** $C_{L_\alpha} = 0.1085^\circ$, $\alpha_{0L} = 0.0^\circ$, $C_{D0} = 0.009$

| Alpha (deg) | Exp Cl | AASI Cl | Delta Cl | Exp Cd | AASI Cd | Delta Cd |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.0° | 0.380 | 0.000 | 0.3800 | 0.0125 | 0.0090 | 0.0035 |
| 2.0° | 0.610 | 0.217 | 0.3929 | 0.0140 | 0.0093 | 0.0047 |
| 4.0° | 0.830 | 0.434 | 0.3958 | 0.0175 | 0.0103 | 0.0072 |
| 6.0° | 1.030 | 0.651 | 0.3787 | 0.0240 | 0.0119 | 0.0121 |

---

## RAE 2822
- **Reference:** AGARD Advisory Report AR-138 (Transonic)
- **Conditions:** $Re = 6,500,000$, $Mach = 0.68$
- **Error Metrics:** Lift MAE = `0.2996`, Drag MAE = `0.0066`
- **Derived Slopes:** $C_{L_\alpha} = 0.1086^\circ$, $\alpha_{0L} = 0.0^\circ$, $C_{D0} = 0.0054$

| Alpha (deg) | Exp Cl | AASI Cl | Delta Cl | Exp Cd | AASI Cd | Delta Cd |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1.0° | 0.350 | 0.108 | 0.2415 | 0.0095 | 0.0054 | 0.0041 |
| 2.0° | 0.520 | 0.217 | 0.3029 | 0.0118 | 0.0056 | 0.0062 |
| 3.0° | 0.680 | 0.326 | 0.3544 | 0.0155 | 0.0060 | 0.0095 |

---

