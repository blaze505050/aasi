# AASI Cross-Dataset Generalization & Benchmark Evaluation

## The Cross-Domain Generalization Challenge
A primary pitfall in scientific machine learning is evaluating a surrogate trained on one CFD solver (e.g. OpenFOAM RANS $k$-$\omega$ SST) directly against another solver or experimental facility without establishing physical and dimensional compatibility.

For example, comparing a 2D infinite airfoil simulation with a 3D finite wing experiment violates basic physics due to induced drag, wingtip vortices, and aspect-ratio effects. Similarly, evaluating an incompressible solver against transonic data with shock-wave boundary-layer interactions (SWBLI) yields spurious errors that reflect modeling incompatibility rather than model inaccuracy.

AASI establishes a formal **Scientific Compatibility Contract** governing all cross-dataset evaluations.

---

## Capability Status Classification Matrix
| Benchmark / Engine | Classification | Description | Implementation Status |
| :--- | :--- | :--- | :--- |
| **Scientific Compatibility Contract** | `REAL IMPLEMENTED` | Enforces dimensional, Mach regime, and turbulence model compatibility gates. | Active (`backend/physics/generalization.py`) |
| **NASA TMR Verification Benchmark** | `REAL IMPLEMENTED` | NACA 0012 2D grid-converged RANS benchmarks (CFL3D, FUN3D). | Active (`NASATMR2DDatasetAdapter`) |
| **AirfRANS Cross-Solver Benchmark** | `REAL IMPLEMENTED` | Multi-airfoil RANS dataset generated with OpenFOAM `simpleFoam`. | Active (`AirfRANSAdapter`) |
| **NASA LTPT Experimental Benchmark** | `REFERENCED` | Low-Turbulence Pressure Tunnel wind tunnel measurements. | Curated literature values |
| **Transonic 3D Wing Benchmarks** | `RESOURCE LIMITED` | Onera M6, Common Research Model (CRM) high-Re transonic datasets. | Architectural Scaffold Ready |

---

## The Scientific Compatibility Matrix
Before comparing model predictions against external datasets, the compatibility engine evaluates four physical invariants:

| Source Dataset | Target Dataset | Dimensionality | Flow Regime | Turbulence Model | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AirfRANS (OpenFOAM) | NASA TMR (2D NACA 0012) | 2D vs 2D | Incompressible Subsonic ($M < 0.3$) | $k$-$\omega$ SST vs $k$-$\omega$ SST | `COMPATIBLE` |
| AirfRANS (2D Airfoil) | NASA LTPT (3D Finite Wing) | 2D vs 3D | Subsonic | RANS vs Wind Tunnel | `COMPARISON_NOT_VALID` (Aspect ratio / 3D induced drag) |
| AirfRANS (Incompressible) | Onera M6 (Transonic $M = 0.84$) | 2D vs 3D | Incompressible vs Transonic Shock | Incompressible vs Compressible | `COMPARISON_NOT_VALID` (Shock wave boundary-layer interaction) |
| NASA TMR (CFL3D) | NASA TMR (FUN3D) | 2D vs 2D | Subsonic / Transonic | SA vs SA | `COMPATIBLE` (Code-to-code verification) |

When an evaluation is requested across incompatible physics domains, the engine fails closed, returning:
```json
{
  "comparison_valid": false,
  "verdict": "COMPARISON_NOT_VALID",
  "reason": "Dimensionality mismatch: Source is 2D airfoil section while Target is 3D finite wing. Cannot equate 2D sectional lift with 3D finite wing lift due to induced drag and tip vortices."
}
```

---

## Multi-Tier Transferability Metrics
Compatible evaluations report standardized transfer metrics:
- **Mean Absolute Percentage Error (MAPE)**: $\frac{1}{N} \sum \left|\frac{y - \hat{y}}{y}\right| \times 100$
- **Root Mean Squared Error (RMSE)**: $\sqrt{\frac{1}{N}\sum (y - \hat{y})^2}$
- **Rank Correlation ($\rho$)**: Spearman rank correlation of lift curve slopes $\partial C_L / \partial \alpha$
- **Grid Convergence Index (GCI)**: Evaluated when comparing against multi-grid TMR levels (L1 through L5)
