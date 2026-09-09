# AASI Solver Adapters

## 1. Adapter Architecture Overview

AASI interacts with computational fluid dynamics (CFD) and aerodynamic codes through dedicated adapter modules implementing the `BaseSolverAdapter` interface.

```
                  ┌──────────────────────┐
                  │  BaseSolverAdapter   │
                  └──────────┬───────────┘
                             │
     ┌───────────────────────┼───────────────────────┬──────────────────────┐
     ▼                       ▼                       ▼                      ▼
OpenFOAMAdapter         SU2Adapter             XFOILAdapter           XFLR5Adapter
(RANS incompressible/   (Compressible Euler/   (2D Viscous Panel      (Airfoil/Wing
 compressible)           RANS)                  Method)                Design)
```

Each adapter is responsible for:
1. **Case Deck Generation**: Writing formatted solver input decks (e.g. OpenFOAM dictionaries, SU2 configuration files, XFOIL batch scripts).
2. **Case Validation**: Checking boundary condition syntax, cell counts, and numerical schemes.
3. **Execution Command Formatting**: Emitting allowlisted executable arguments.
4. **Log & Residual Parsing**: Extracting convergence metrics (continuity, velocity, turbulence residuals) and integrated force coefficients ($C_l, C_d, C_m$).

---

## 2. OpenFOAM Adapter (`OpenFOAMAdapter`)

### Supported Solvers
- `simpleFoam`: Steady-state incompressible Navier-Stokes with turbulence modeling.
- `rhoCentralFoam`: Density-based compressible solver for transonic and supersonic flows.

### Directory Structure Generated
```
data/simulations/{case_id}/
├── 0/
│   ├── U               # Velocity boundary conditions (freestream vector at AoA)
│   ├── p               # Kinematic pressure boundary conditions
│   ├── k               # Turbulent kinetic energy
│   ├── omega           # Specific dissipation rate
│   └── nut             # Turbulent kinematic viscosity
├── constant/
│   ├── transportProperties  # Kinematic viscosity (nu = U * c / Re)
│   └── turbulenceProperties # RAS simulationType, kOmegaSST / SpalartAllmaras
└── system/
    ├── controlDict     # simpleFoam application, time step, output intervals
    ├── fvSchemes       # Gauss linear / linearUpwind schemes
    ├── fvSolution      # GAMG / smoothSolver linear equation settings
    └── blockMeshDict   # Parametric 2D C-grid mesh definition
```

### Residual & Force Parsing
The `OpenFOAMLogParser` extracts:
- Initial and final residuals for `p`, `Ux`, `Uy`, `k`, `omega` per iteration.
- Force coefficients from `forces` functionObject:
  $$C_l = \frac{F_{\text{lift}}}{\frac{1}{2}\rho U_\infty^2 S}, \quad C_d = \frac{F_{\text{drag}}}{\frac{1}{2}\rho U_\infty^2 S}, \quad C_m = \frac{M}{\frac{1}{2}\rho U_\infty^2 S c}$$

---

## 3. SU2 Adapter (`SU2Adapter`)

### Supported Solvers
- `SU2_CFD`: Multiphysics compressible and incompressible CFD solver.

### Configuration Deck Generation
Generates `default.cfg` containing:
- Governing equations: `EULER`, `NAVIER_STOKES`, or `RANS`
- Turbulence closure: `SA` (Spalart-Allmaras) or `SST` ($k-\omega$ Shear Stress Transport)
- Freestream conditions: `MACH_NUMBER`, `AOA`, `FREESTREAM_REYNOLDS`
- Numerical schemes: Roe, JST, AUSM, or Jameson
- Convergence criteria: `CONV_RESIDUAL_MINVAL = 1e-6`

---

## 4. XFOIL Adapter (`XFOILAdapter`)

### Capabilities
- 2D inviscid panel method with coupled integral boundary layer equations.
- Rapid polar sweep across angle of attack range.
- Laminar-to-turbulent transition prediction via the $e^n$ method.

### Batch Script Generation
Generates headless XFOIL command sequences (`xfoil_input.txt`):
```text
NACA 0012
PANE
OPER
VISC 3000000
MACH 0.15
ALFA 4.0
CPWR cp_out.dat
QUIT
```

---

## 5. Security & Sandbox Constraints
Adapters never directly spawn OS shell subprocesses. Execution is delegated exclusively to the `SimulationSecuritySandbox`, ensuring:
- Working directory isolation within `data/simulations/{case_id}/`.
- Allowlisting of solver binaries only.
- Strict timeout enforcement.
- Cryptographic hashing of generated dictionary files into `EXP-{case_id}.manifest.json`.
