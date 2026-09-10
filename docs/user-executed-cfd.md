# Standalone User-Executed CFD & Artifact Ingestion

## Overview
AASI recognizes that developers and researchers frequently work on hardware where local OpenFOAM or heavy CFD solvers cannot or should not be executed directly. Phase 5 introduces a clean separation between **case deck synthesis** and **solver execution**:
1. **Case Deck Generation (`aasi_case/`):** AASI deterministically writes a complete, standalone, syntactically verified CFD case bundle.
2. **14-Section Execution Guide:** The directory includes a comprehensive `README.md` and automated shell scripts (`run.sh`, `clean.sh`, `postProcess.sh`) for execution on a lab workstation, Docker container, or high-performance computing (HPC) cluster.
3. **Artifact Ingestion Service:** When simulation completes on the user's cluster, the researcher uploads the resulting output (e.g. `forceCoeffs.dat`, `history.csv`, or polar). AASI parses and validates the aerodynamic coefficients ($C_L, C_D$), verifies residuals, checks physical boundaries, and attaches cryptographic SHA-256 provenance.

---

## Standalone Case Deck Structure (`aasi_case/`)

```
aasi_case/
├── 0/
│   ├── U                  # Freestream velocity boundary conditions (dirichlet inlet, zeroGradient outlet, noSlip wall)
│   ├── p                  # Pressure boundary conditions (zeroGradient inlet, fixedValue outlet)
│   ├── k                  # Turbulent kinetic energy
│   ├── omega              # Specific dissipation rate
│   └── nut                # Turbulent kinematic viscosity wall functions
├── constant/
│   ├── transportProperties# Kinematic viscosity (nu) computed from Mach and Reynolds
│   └── turbulenceProperties# Simulation type (RAS) and model (kOmegaSST)
├── system/
│   ├── controlDict        # Solver selection (simpleFoam), endTime, writeInterval, forceCoeffs functionObject
│   ├── fvSchemes          # Discretization schemes (linear, upwind, steadyState)
│   ├── fvSolution         # Linear solvers (GAMG, smoothSolver), tolerances (1e-6), and relaxation factors
│   └── blockMeshDict      # Parametric 2D C-grid mesh generator
├── scripts/
│   ├── run.sh             # Self-contained execution script with error traps
│   ├── clean.sh           # Reset directory to pre-run state
│   └── postProcess.sh     # Extract forceCoeffs and residuals
├── manifest.json          # Input parameters, conditions, and SHA-256 hashes of all dictionary files
├── validation_checklist.md# Pre-flight checklist for mesh quality, CFL, and boundary alignment
└── README.md              # Complete 14-section execution guide
```

---

## 14-Section Execution Guide Specifications
The generated `README.md` inside `aasi_case/` covers all 14 mandatory operational sections:
1. **Case Overview & Physical Objective:** Airfoil geometry, target Mach, Reynolds number, and Angle of Attack.
2. **Prerequisites & Solver Version:** Supported OpenFOAM versions (v2012, v2112, v2212, v2312, OpenFOAM 9/10/11).
3. **Hardware & Resource Sizing:** Recommended CPU cores, memory requirements, and disk footprint.
4. **Environment Setup & Sourcing:** Shell initialization (`source /usr/lib/openfoam/openfoam.../etc/bashrc`).
5. **Geometry & Meshing Procedure:** Mesh generation steps (`blockMesh`, `checkMesh`).
6. **Boundary Conditions & Fluid Properties:** Physical values specified in `0/` and `constant/`.
7. **Numerical Schemes & Discretization:** Explanation of convective and Laplacian schemes in `system/fvSchemes`.
8. **Linear Equation Solvers & Convergence Tolerances:** Relaxation factors and target residual thresholds ($10^{-6}$).
9. **Step-by-Step Execution Workflow:** Running serial or parallel execution (`decomposePar`, `mpirun`).
10. **Runtime Monitoring & Convergence Inspection:** Real-time log monitoring (`tail -f log.simpleFoam`).
11. **Post-Processing & Aerodynamic Coefficient Extraction:** Locating `postProcessing/forceCoeffs/0/forceCoeffs.dat`.
12. **Troubleshooting & Common Failure Modes:** Divergence remedies, negative turbulent viscosity, mesh skewness.
13. **Artifact Return & Ingestion Instructions:** How to upload `forceCoeffs.dat` back to AASI.
14. **Cryptographic Checksums & Manifest Verification:** `manifest.json` SHA-256 hashes for data integrity.

---

## Artifact Ingestion Service
The `ArtifactIngestionService` accepts uploaded simulation outputs via the REST endpoint `/api/compute/upload-artifact` or via the interactive frontend drawer.

### Supported Artifact Formats
1. **OpenFOAM `forceCoeffs.dat`:** Extracts iterations, $C_L$, $C_D$, $C_M$, pitch moments, and convergence status.
2. **SU2 Convergence History (`history.csv`):** Parses iterations, residual reductions (RMS Pressure, RMS Momentum), and integrated coefficients.
3. **XFOIL Polar (`.pol` / `.dat`):** Parses multi-angle sweeps ($\alpha, C_L, C_D, C_{Dp}, C_M$).

### Physical Validation Checks
Upon ingestion, the artifact is subjected to automated validation:
- **Positive Drag Check:** Verifies $C_D > 0$.
- **Lift Range Check:** Flags values outside physical bounds for subsonic unpowered airfoils ($-3.0 \le C_L \le 3.5$).
- **Residual Convergence:** Verifies that forces achieved steady oscillations or monotonically decreased.
- **Cryptographic Provenance:** Generates a SHA-256 hash of the uploaded artifact and stores it in the experiment manifest.
