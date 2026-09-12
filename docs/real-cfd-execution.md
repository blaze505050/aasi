# AASI Real CFD Execution & Convergence Monitoring Engine

## 1. Directive & Architecture
Governing Directive: **Real Scientific Execution, Evidence Integrity & Independent Reproducibility.**

In compliance with the master engineering directive, AASI refuses to fake, mock, or hallucinate CFD solver execution. The `OpenFOAMExecutionEngine` in `backend/simulation/executor.py` manages genuine CFD execution with strict physical convergence contracts:
1. **Host Solver Detection**: Probes host environment (`PATH`, Linux, WSL2) for `simpleFoam`.
2. **Deterministic Fallback**: If the solver is unavailable, returns `SOLVER_UNAVAILABLE` and stages the verified case deck as `USER_EXECUTED_REQUIRED`.
3. **Log & Stream Monitoring**: When executed, continuously tracks residuals ($U_x, U_y, p, \text{continuity}$) and parses force coefficients ($C_L, C_D, C_M$).
4. **Decoupled Convergence Contract**: Strictly differentiates process exit code `0` from physical aerodynamic convergence.

---

## 2. Solver Detection Protocol

```python
is_installed, binary_path = OpenFOAMExecutionEngine.detect_solver("simpleFoam")
```

The detector checks:
- System `PATH` via `shutil.which("simpleFoam")`.
- Canonical OpenFOAM installation directories:
  - `/usr/bin/simpleFoam`
  - `/opt/openfoam10/platforms/linux64GccDPInt32Opt/bin/simpleFoam`
  - `/opt/openfoam11/platforms/linux64GccDPInt32Opt/bin/simpleFoam`
  - `/opt/openfoam2306/platforms/linux64GccDPInt32Opt/bin/simpleFoam`

If absent, the engine constructs a full `ConvergenceReport` with `is_converged = False` and status `USER_EXECUTED_REQUIRED`, preventing downstream routines from treating missing data as valid physics.

---

## 3. Physical Convergence vs. Process Termination

Standard CFD automation frameworks commit a critical fallacy: assuming that `exit_code == 0` implies valid physics. `OpenFOAMExecutionEngine` evaluates:

| Criterion | Threshold | Physical Rationale |
|---|---|---|
| **Max Residual** | $\le 1.0 \times 10^{-4}$ | Ensures conservation equations are satisfied across all cells. |
| **Force Stabilization ($C_L$)** | $\sigma_{C_L, 50} \le 1.0 \times 10^{-3}$ | Standard deviation over last 50 iterations verifies boundary-layer pressure and shear forces have reached steady state. |
| **Continuity Error** | Local bounded | Prevents artificial mass creation or destruction. |
| **Divergence Guard** | No `NaN`, `Inf`, or $> 10^4$ | Detects unphysical numerical explosions. |

If residuals remain high ($> 10^{-4}$) or forces continue oscillating ($\sigma > 10^{-3}$), the run is categorized as `UNCONVERGED` or `OSCILLATING`, regardless of exit code.

---

## 4. Execution Staging Output

When staged for external or cluster execution, the engine produces:
- `system/controlDict`, `system/fvSchemes`, `system/fvSolution`.
- `constant/transportProperties`, `constant/turbulenceProperties` ($k$-$\omega$ SST).
- `0/U`, `0/p`, `0/k`, `0/omega`, `0/nut`.
- Meshing scripts (`blockMeshDict` with grading and $y^+ \approx 1$ wall spacing).
- Autonomous launch script `run.sh` with residual logging redirect:
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  simpleFoam -case . > log.simpleFoam 2>&1
  ```
