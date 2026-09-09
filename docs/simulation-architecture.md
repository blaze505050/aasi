# AASI Simulation Architecture & Execution Fabric

## 1. Overview & Core Tenets

AASI (Autonomous Aerospace Scientific Intelligence) is designed as a hybrid scientific engineering assistant.
In this architecture, **the LLM is an orchestrator, not a CFD solver**.

The Simulation Execution Fabric provides a secure, deterministic, and reproducible runtime environment for executing and validating computational physics tools, including:
- **OpenFOAM** (RANS solvers: `simpleFoam`, `rhoCentralFoam`)
- **SU2** (Compressible/Incompressible CFD: `SU2_CFD`)
- **XFOIL** (Viscous/Inviscid 2D Panel Method)
- **XFLR5** (Airfoil and wing aerodynamic design)

---

## 2. High-Level Architecture

```
User Query / Simulation Request
             │
             ▼
    Scientific Agent
             │
             ▼
┌────────────────────────────────────────────────────────┐
│             SimulationRunner (Central Hub)             │
└────────────────────────────┬───────────────────────────┘
                             │
     ┌───────────────────────┼────────────────────────┐
     ▼                       ▼                        ▼
SolverDetector      SimulationCaseValidator    SimulationRegistry
(Host & WSL2)        (Boundary/Mesh Check)    (OpenFOAM, SU2, XFOIL)
     │                       │                        │
     └───────────────────────┼────────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────┐
│             SimulationSecuritySandbox                  │
│  - Executable allowlist: simpleFoam, blockMesh, SU2... │
│  - Working directory isolation: data/simulations/{id}  │
│  - Path traversal protection (no ../)                  │
│  - Wall-clock timeout enforcement (default 600s)       │
│  - Output size limit (100 MB max)                      │
└────────────────────────────┬───────────────────────────┘
                             │
     ┌───────────────────────┴────────────────────────┐
     ▼                                                ▼
DRY_RUN / VALIDATION                             FULL_RUN
- Case directory setup                     - Allowlisted binary
- Dictionaries generated                   - Isolated subprocess / WSL2
- Boundary validation                      - Real-time log capture
- Manifest with input hashes               - Residual & force parsing
     │                                                │
     └───────────────────────┬────────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────┐
│             SimulationArtifactManager                  │
│  - Cryptographic SHA-256 manifest: EXP-{case_id}.json  │
│  - Input/Output hashes, command line, execution time   │
│  - Residual summaries & convergence status             │
└────────────────────────────────────────────────────────┘
```

---

## 3. Security Sandbox Design

Untrusted code or raw shell commands must never be executed. The `SimulationSecuritySandbox` enforces:

1. **Strict Executable Allowlisting**:
   Only explicitly approved binaries can be invoked:
   ```python
   ALLOWED_EXECUTABLES = {
       "simpleFoam", "rhoCentralFoam", "blockMesh", "checkMesh", "decomposePar",
       "reconstructPar", "snappyHexMesh", "SU2_CFD", "SU2_SOL", "SU2_DEF",
       "xfoil", "xflr5"
   }
   ```
2. **Rejection of Shell Metacharacters & Injections**:
   Commands with `;`, `&`, `|`, `` ` ``, `$`, `\n`, or path traversal sequences (`..`) are immediately rejected with a `SecurityException`.
3. **Working Directory Isolation**:
   Every simulation case executes inside a designated case folder under `data/simulations/{case_id}/`. The sandbox verifies that the execution path cannot escape this boundary.
4. **Execution Timeouts & Process Cleanup**:
   Subprocesses are governed by strict timeouts (default: 300s, max: 3600s). If a process hangs or fails to converge, the sandbox terminates the process tree cleanly.
5. **Output Size Caps**:
   Standard output and error streams are capped (default: 100 MB) to prevent denial-of-service via infinite log flooding.

---

## 4. Host & WSL2 Solver Discovery

AASI discovers available solvers transparently across Windows and WSL2 without fabricating availability:

- **Windows Native**: Probes the host system `PATH` for Windows executables (`.exe`).
- **WSL2 Subsystem**: Probes active WSL2 distributions (`Ubuntu-22.04`, `Ubuntu`) using `wsl.exe -d <distro> which <solver>`.
- **Honest Telemetry**: If a solver or WSL disk is unattached/unavailable, AASI accurately reports `is_available: False, status: NOT_INSTALLED` or `DETECTION_ERROR`. It does not invent solver availability.

---

## 5. Execution Modes

The simulation fabric supports three operational modes:

| Mode | Purpose | Execution Behavior |
| :--- | :--- | :--- |
| `DRY_RUN` | Case deck generation & manifest verification | Generates full case directory, writes all solver dictionaries (`0/`, `system/`, `constant/`), validates boundary conditions and schemes, computes file hashes, produces `EXP-<case_id>.manifest.json` without spawning external solver. |
| `VALIDATION_RUN` | Syntax & mesh integrity check | Generates case deck, runs mesh validation utilities (`blockMesh`, `checkMesh`), verifies initial condition consistency. |
| `FULL_RUN` | Complete CFD solver execution | Executes solver binary within the sandbox, monitors residuals and force coefficients, produces converged aerodynamic coefficients. |

---

## 6. Reproducibility & Provenance Manifests

Every simulation execution produces an authenticated JSON manifest `EXP-{case_id}.manifest.json` containing:
- `manifest_id`: Unique identifier (e.g. `EXP-naca0012-simplefoam-subsonic-001`)
- `case_id`: Case reference name
- `solver`: Target solver and version
- `run_mode`: `DRY_RUN`, `VALIDATION_RUN`, or `FULL_RUN`
- `status`: Final execution status (`DRY_RUN_COMPLETED`, `CONVERGED`, `FAILED`)
- `case_directory`: Path to isolated case folder
- `input_hashes`: Cryptographic SHA-256 checksums of every input dictionary and mesh file
- `output_hashes`: SHA-256 checksums of residual logs and force coefficient tables
- `command_executed`: Allowlisted command invoked
- `validation_passed`: Boolean flag from boundary and schema validator
