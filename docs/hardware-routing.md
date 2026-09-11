# AASI Hardware Capability Matrix & Resource Routing

## 1. Workstation Constraints & Hardware Safety

AASI is designed to run reliably on resource-constrained developer hardware without causing kernel freezes, memory thrashing, or out-of-memory crashes:

- **Host Processor:** 4 CPU cores
- **System Memory:** 8 GB RAM (typically $\sim 1.5 - 2.5$ GB free under load)
- **Host Operating System:** Windows 10/11 with WSL2 Linux available
- **Acceleration:** No discrete NVIDIA GPU / CUDA runtime
- **Available Solvers:** No mandatory host OpenFOAM, SU2, or XFOIL binaries

To respect these physical constraints, AASI implements an **automated Hardware Capability Matrix** in `backend/compute/hardware_matrix.py` that probes host resources and enforces fail-closed workload routing.

---

## 2. Hardware Detection Engine (`HardwareMatrixManager`)

Host capabilities are detected safely without third-party binary dependencies:

- **Logical & Physical CPU Cores:** `os.cpu_count()`.
- **System RAM:** Native Windows memory probe via `ctypes.windll.kernel32.GlobalMemoryStatusEx` (`TotalPhys`, `AvailPhys`) with `/proc/meminfo` fallback for Linux/WSL2.
- **Disk Free Space:** `shutil.disk_usage(".")`.
- **CUDA & GPU:** Safe dynamic import of PyTorch inside try-catch blocks to prevent crashes from missing Visual C++ redistributables or OS security policies.
- **WSL2 Discovery:** Probes `wsl.exe` in Windows PATH.
- **Solver Probing:** `SolverDetector` inspects Windows PATH and WSL2 distributions for `simpleFoam`, `SU2_CFD`, and `xfoil`.

---

## 3. Workload Classification & Routing Rules

Every computational task is evaluated against the active hardware profile:

```text
COMPUTATIONAL WORKLOAD
           │
           ▼
TASK TYPE & RESOURCE REQUIREMENT AUDIT
           │
  ┌────────┼───────────────────────────┐
  ▼        ▼                           ▼
SURROGATE  2D CFD SIMULATION          3D CFD / DEEP NEURAL OPERATOR
INFERENCE  │                           │
  │        ├─ Solver Absent ───────────┼─ Exceeds 8GB RAM ──────────┐
  │        ├─ Cells > 50,000 ──────────┤                            │
  ▼        ▼                           ▼                            ▼
LOCAL CPU  LOCAL CPU               USER-EXECUTED               REMOTE HPC
EXECUTION  (If installed & small)   OpenFOAM CASE DECK          SLURM SCRIPT
```

| Task Category | Computational Demand | Local Execution Allowed? | Recommended Backend | Rationale |
|:---|:---|:---:|:---|:---|
| `SURROGATE_INFERENCE` | $< 10$ ms, $< 50$ MB RAM | ✅ Yes | `LOCAL` | Higher-order polynomial/ridge evaluation evaluates deterministically on pure CPU in milliseconds. |
| `SURROGATE_TRAINING` (Small CPU) | $< 5$ sec, $< 150$ MB RAM | ✅ Yes | `LOCAL` | Pure-CPU deterministic training (`seed=42`) with UIUC 1,008-point dataset runs without GPU requirement. |
| `SURROGATE_TRAINING` (Deep FNO / GNN) | $> 4$ GB VRAM, Hours | ❌ No | `REMOTE` | Deep neural operators require discrete CUDA GPUs not available on this host. Generates Slurm recipe. |
| `CFD_2D` (Missing local binary) | Dependent on OpenFOAM | ❌ No | `USER_EXECUTED` | Fails closed; generates standalone `aasi_case/` directory with `Allrun` scripts for execution on external machine. |
| `CFD_2D` (Cells $> 50,000$) | $> 2$ GB RAM | ❌ No | `USER_EXECUTED` | Exceeds safe workstation memory quota ($50,000$ cells) to prevent host thrashing. |
| `CFD_3D` (Navier-Stokes) | Multi-million cells, $> 16$ GB RAM | ❌ No | `USER_EXECUTED` / `REMOTE` | 3D simulations cannot run on a 4-core 8GB edge host; requires dedicated cluster execution. |

---

## 4. API Endpoints

- `GET /api/system/capabilities`: Returns the current host hardware profile, detected solvers, and safe operational bounds.
- `POST /api/compute/route-request`: Accepts simulation or training parameters and returns a fail-closed `RoutingDecision` with explicit bottleneck explanations.
