# AASI OpenFOAM User Execution & Simulation Fabric

## 1. Core Philosophy: Learn From CFD, Do Not Replace CFD

AASI treats high-fidelity Computational Fluid Dynamics (CFD) not as an internal black-box solver to be faked on a developer laptop, but as an authoritative external reality:

```text
USER PROBLEM / AIRFOIL DESIGN
             │
             ▼
SCIENTIFIC RESOLUTION & CHECKS (Analytical / Surrogate / Dataset Match)
             │
      ┌──────┴─────────────────────────────┐
      ▼                                    ▼
SURROGATE PREDICTION VALID          OUT-OF-DOMAIN / UNCERTAINTY HIGH
(Evaluate inside calibrated domain)   (Trigger OpenFOAM Case Generation)
                                                   │
                                                   ▼
                                      STANDALONE `aasi_case/` DECK
                                                   │
                                                   ▼
                                      USER / HPC RUNS OpenFOAM
                                      (simpleFoam / Allrun / Allrun.bat)
                                                   │
                                                   ▼
                                      ARTIFACT INGESTION & QC
                                      (Residuals, Force Stability, ASME V&V 20)
                                                   │
                                                   ▼
                                      DATASET ENRICHMENT & SURROGATE RETRAINING
```

---

## 2. Canonical Standalone `aasi_case/` Structure

When a computational CFD case is requested, AASI synthesizes a fully self-contained directory that requires no network connectivity to run:

```text
aasi_case/
├── README.md                   # Complete case overview and environment setup
├── manifest.json               # Cryptographic SHA-256 hash of all boundary settings
├── validation_checklist.md     # 14-point scientific pre-flight verification checklist
├── expected_results.md         # Estimated aerodynamic coefficients and stall bounds
├── Allrun                      # Linux / WSL2 bash execution entrypoint
├── Allrun.bat                  # Windows batch execution entrypoint
├── 0/                          # Initial and boundary conditions
│   ├── U                       # Velocity field with Dirichlet inlet and no-slip wall
│   ├── p                       # Kinematic pressure field with zero-gradient wall
│   ├── k                       # Turbulent kinetic energy ($k = \frac{3}{2}(U_\infty I)^2$)
│   ├── omega                   # Specific dissipation rate ($\omega = \frac{k^{1/2}}{C_\mu^{1/4} L}$)
│   └── nut                     # Turbulent kinematic viscosity wall functions
├── constant/                   # Physical and transport properties
│   ├── transportProperties     # Kinematic viscosity ($\nu$) derived from Reynolds number
│   └── turbulenceProperties    # Simulation type (RAS) and model (kOmegaSST)
├── system/                     # Solver numerical controls
│   ├── controlDict             # simpleFoam solver, writeInterval, forceCoeffs functionObject
│   ├── fvSchemes               # Discretization schemes (upwind/linearUpwind for convective terms)
│   ├── fvSolution              # GAMG/smoothSolver settings, relaxation factors (p=0.3, U=0.7)
│   └── blockMeshDict           # Structured C-grid or O-grid topology around airfoil
└── scripts/                    # Shell scripts for mesh generation, run, clean, and export
    ├── mesh.sh
    ├── run.sh
    └── clean.sh
```

---

## 3. The 14-Point Pre-Flight Validation Checklist

Every generated case includes `validation_checklist.md`, requiring the researcher to verify:
1. **Geometric Fidelity:** Airfoil coordinate points normalized to unit chord ($c = 1.0$).
2. **Boundary Inflation:** Wall $y^+ \le 1.0$ for low-Reynolds wall-resolved SST formulation.
3. **Farfield Distance:** Domain boundaries placed $\ge 25$ chord lengths away from airfoil.
4. **Viscosity Normalization:** $\nu = \frac{U_\infty c}{Re}$ matched to physical flow conditions.
5. **Turbulence Intensity:** Inlet freestream turbulence intensity $I = 0.1\%$ to $1.0\%$.
6. **Pressure Relaxation:** SIMPLE pressure under-relaxation factor $\le 0.3$ to prevent divergence.
7. **Momentum Relaxation:** Velocity under-relaxation factor $\le 0.7$.
8. **Convective Differencing:** Second-order bounded schemes (`linearUpwind`) for final convergence.
9. **Force Coeffs Alignment:** Lift and drag direction vectors properly rotated to angle of attack $\alpha$:
   $$\vec{d}_{drag} = (\cos\alpha, \sin\alpha, 0), \quad \vec{d}_{lift} = (-\sin\alpha, \cos\alpha, 0)$$
10. **Residual Convergence:** Equation residuals for $p, U_x, U_y, k, \omega$ drop below $10^{-4}$.
11. **Force Stability:** $C_L$ and $C_D$ oscillate by $< 0.5\%$ over the final 200 iterations.
12. **Positivity:** Drag coefficient $C_D > 0$.
13. **Mesh Sensitivity:** 3-mesh grid refinement planned for ASME V&V 20 Richardson extrapolation.
14. **Artifact Export:** Procedure to return `forceCoeffs.dat` and solver logs to AASI.

---

## 4. Artifact Ingestion & ASME V&V 20 Verification (`POST /api/compute/upload-artifact`)

When external simulation results are uploaded back to AASI:
1. **Dynamic Header Mapping:** Parses OpenFOAM `forceCoeffs.dat`, SU2 CSV files, or generic polars.
2. **Automated Quality Control:**
   - Residual convergence check: confirms steady-state convergence.
   - Force stability check: computes sliding-window variance over last $15\%$ of iterations.
   - Physical bounds check: flags negative drag ($C_D \le 0$) or extreme unphysical lift ($|C_L| > 3.0$).
3. **Cryptographic Tagging:** Computes SHA-256 hash of raw uploaded file content.
4. **ASME V&V 20 Grid Convergence Index (GCI):**
   Across 3 systematically refined grids (Fine $f_1$, Medium $f_2$, Coarse $f_3$), AASI calculates:
   - Grid refinement ratios: $r_{21} = h_2 / h_1$, $r_{32} = h_3 / h_2$
   - Apparent order of accuracy:
     $$p = \frac{|\ln| (f_3 - f_2) / (f_2 - f_1) | + q(p)|}{\ln(r_{21})}$$
   - Richardson extrapolated continuum solution:
     $$f_{ext}^{21} = \frac{r_{21}^p f_1 - f_2}{r_{21}^p - 1}$$
   - Fine Grid Convergence Index:
     $$GCI_{fine}^{21} = \frac{1.25 |e_{a}^{21}|}{r_{21}^p - 1}, \quad \text{where } e_a^{21} = \frac{f_2 - f_1}{f_1}$$
   - Verification of asymptotic range:
     $$\frac{GCI_{medium}^{32}}{r_{21}^p GCI_{fine}^{21}} \approx 1.0$$
