# AASI Phase 23 Architecture: Remote Compute Fabric & Google Colab CFD Backend

**Directive:** AASI Master Engineering Directive — Phase 23  
**Governing Doctrine:** Absolute Anti-Fabrication Rule  
**System:** Autonomous Aerospace Scientific Investigator (AASI)  
**Package:** `backend/compute/`  

---

## 1. System Architectural Overview

The Phase 23 Remote Compute Fabric abstracts computational execution away from host workstation limitations, providing a standardized, backend-agnostic interface for deploying, monitoring, ingesting, and verifying computational fluid dynamics (CFD) simulations.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AASI Scientific Discovery Engine                     │
│    (Candidate Acquisition, Geometry Encoding, Conformal Uncertainty)    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Compute Fabric Manager                             │
│       (Backend Selection Policy: Local -> Colab -> HPC -> Fallback)     │
└───────┬────────────────────────────┬────────────────────────────┬───────┘
        │                            │                            │
        ▼                            ▼                            ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│LocalOpenFOAM     │       │ColabBackend      │       │FutureRemoteHPC   │
│Backend           │       │(Bundle & Probe)  │       │Backend (Slurm)   │
└───────┬──────────┘       └─────────┬────────┘       └─────────┬────────┘
        │                            │                          │
        └────────────────────────────┼──────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Execution State Machine & Jobs                      │
│ (QUEUED -> DISPATCHED -> RUNNING -> COMPLETED -> VERIFIED/FAIL_CLOSED)  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Artifact Ingestion & Physical Gate                    │
│    (Residual Convergence, Stagnation Bernoulli, Drag Positivity)        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                12-Node Cryptographic Merkle Provenance DAG              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The `ComputeBackend` Abstraction Contract

Every compute backend conforms to the abstract base contract defined in `backend/compute/base.py`:

```python
class ComputeBackend(ABC):
    @abstractmethod
    def probe(self) -> BackendProbeResult:
        """Measure real-time environment status, hardware, and solver availability."""
        ...

    @abstractmethod
    def submit(self, job: CFDJobManifest) -> CFDJobManifest:
        """Prepare and submit a compute job for execution."""
        ...

    @abstractmethod
    def status(self, job_id: str) -> JobStatusResult:
        """Poll the execution state of a previously submitted job."""
        ...

    @abstractmethod
    def cancel(self, job_id: str) -> bool:
        """Terminate a running or queued job cleanly."""
        ...

    @abstractmethod
    def collect(self, job_id: str) -> Dict[str, Any]:
        """Collect all solver logs, force records, and spatial flowfields."""
        ...

    @abstractmethod
    def verify(self, job_id: str) -> Dict[str, Any]:
        """Perform cryptographic checksum and physical consistency checks on outputs."""
        ...
```

### Supported Concrete Implementations
1. **`LocalOpenFOAMBackend`:** Direct execution bridge on host workstation (Windows native or WSL2). Enforces `CFDResourceGovernor` safety reserve ($\ge 15.0\text{ GB}$). Fails closed with `USER_EXECUTED_REQUIRED` if host solver is unavailable.
2. **`ColabBackend`:** Generates standalone, self-verifying Google Colab execution bundles (`notebook.ipynb`, `run_openfoam.sh`, `case.tar.gz`, `job_manifest.json`) without violating Google Colab terms of service. Ingests and audits returned artifacts.
3. **`FutureRemoteHPCBackend`:** Slurm/PBS batch scheduler interface for high-performance clusters and cloud VMs (GCP, AWS, Oracle Cloud).

---

## 3. Execution State Machine & Immutability Doctrine

Every job in the Remote Compute Fabric transitions through an explicit, monotonic state machine:

```
[NOT_CONFIGURED]
       │
       ▼
   [QUEUED] ─────────────► [BACKEND_UNAVAILABLE]
       │
       ▼
 [DISPATCHED]
       │
       ▼
   [RUNNING] ────────────► [TIMEOUT / FAILED]
       │
       ▼
  [COMPLETED]
       │
       ▼
┌──────┴──────────────────────────┐
│                                 │
▼                                 ▼
[PHYSICS_VALIDATION_FAILED]     [REPRODUCIBILITY_FAILED]
│                                 │
└──────────────┬──────────────────┘
               │ (Only if all gates pass)
               ▼
        [REAL_EXECUTED]
```

### State Definitions
- `NOT_CONFIGURED`: Backend credentials, paths, or execution templates are uninitialized.
- `BACKEND_UNAVAILABLE`: Target backend is offline, unreachable, or missing required binaries.
- `QUEUED`: Job is registered, geometry and mesh preflight checks have passed, and manifest is sealed.
- `DISPATCHED`: Job payload has been transmitted or staged for external execution.
- `RUNNING`: Remote runtime has confirmed active solver execution.
- `COMPLETED`: Solver process terminated with exit code 0 and generated output directories.
- `FAILED`: Solver crashed, diverged, or threw runtime errors.
- `TIMEOUT`: Execution exceeded the maximum allowed wall-clock limit ($1800\text{ s}$).
- `PHYSICS_VALIDATION_FAILED`: Results violate aerodynamic conservation laws.
- `REPRODUCIBILITY_FAILED`: Checksums of returned outputs do not match execution manifests.
- `REAL_EXECUTED`: Output verified by independent physical and cryptographic gates.
- `USER_EXECUTED_REQUIRED`: Safe fallback state requiring manual or external solver execution.

---

## 4. Google Colab Execution Bundle Specification

When `ColabBackend` prepares a job, it constructs an isolated bundle directory in `data/compute_jobs/{job_id}/`:

```
data/compute_jobs/{job_id}/
├── job_manifest.json       # Immutable job descriptor with SHA-256 hashes
├── case.tar.gz             # Compressed OpenFOAM case (0/, constant/, system/)
├── environment.yml         # Conda environment definition for dependencies
├── requirements.txt        # Pip dependencies (PyFOAM, numpy, scipy)
├── run_openfoam.sh         # Shell script executing blockMesh and simpleFoam
├── verify_results.py       # Standalone convergence and residual verification script
├── collect_results.py      # Artifact packaging and SHA-256 hashing script
└── notebook.ipynb          # Clean, valid Jupyter notebook for Colab
```

### The 18-Step Colab Execution Sequence
The generated `notebook.ipynb` implements an 18-step verification pipeline:
1. **Runtime Reality Probe:** Query OS, Python, CPU cores, RAM, GPU availability.
2. **Environment Verification:** Check system utilities (`tar`, `gzip`, `wget`, `curl`).
3. **OpenFOAM Availability Check:** Probe `simpleFoam`; provision if absent (`sudo apt-get install openfoam`).
4. **Dependency Installation:** Install lightweight validation packages if necessary.
5. **Case Extraction:** Unpack `case.tar.gz` into working directory.
6. **Case Hash Verification:** Verify SHA-256 of extracted files against `job_manifest.json`.
7. **Geometry Hash Verification:** Audit coordinates array against expected geometry hash.
8. **Manifest Integrity Check:** Verify that job ID and target conditions match.
9. **Mesh Generation & Audit:** Run `blockMesh` and audit cell count / boundary names.
10. **Solver Execution:** Execute `simpleFoam > simpleFoam.log 2>&1`.
11. **Residual Monitoring:** Parse residual evolution ($p, U_x, U_y, k, \omega$).
12. **Convergence Verification:** Confirm all residuals $< 10^{-4}$ and force variation $< 0.5\%$.
13. **Force Extraction:** Parse `postProcessing/forces/0/forces.dat` for $C_L, C_D, C_M$.
14. **Field Extraction:** Extract surface pressure distribution $C_p(x/c)$ across 64 stations.
15. **Physical Validation Gate:** Check Bernoulli stagnation, suction peak, and drag non-negativity.
16. **Execution Manifest Generation:** Record timestamps, hardware IDs, and exit codes.
17. **Output Hashing:** Compute SHA-256 hashes for all output files.
18. **Package & Export:** Create signed `results.tar.gz` for ingestion by AASI.

---

## 5. Extended 12-Node Cryptographic Merkle Provenance DAG

Phase 23 extends the Phase 22 Merkle DAG to incorporate the remote execution environment:

$$\text{DAG Root Hash} = H(N_1 \parallel N_2 \parallel \dots \parallel N_{12})$$

| Node | Name | Content Bound |
| :---: | :--- | :--- |
| **$N_1$** | `geometry_hash` | Normalized $(x, y)$ coordinate array |
| **$N_2$** | `case_hash` | Case deck templates (`0/`, `constant/`, `system/`) |
| **$N_3$** | `mesh_hash` | `blockMeshDict` configuration and cell topology |
| **$N_4$** | `solver_config_hash` | Numerical schemes (`fvSchemes`) and solvers (`fvSolution`) |
| **$N_5$** | `solver_version_hash` | OpenFOAM binary version (e.g. `OpenFOAM-v2312`) |
| **$N_6$** | `runtime_env_hash` | Remote host OS, CPU, RAM, GPU, kernel version |
| **$N_7$** | `execution_log_hash` | Complete stdout/stderr solver log (`simpleFoam.log`) |
| **$N_8$** | `residual_history_hash` | Iteration-by-iteration convergence histories |
| **$N_9$** | `flowfield_hash` | Parsed scalar and vector internal fields ($p, U, k, \omega, \nu_t$) |
| **$N_{10}$** | `force_hash` | Integrated aerodynamic coefficients ($C_L, C_D, C_M$) |
| **$N_{11}$** | `physical_validation_hash` | Signed report from `PhysicalFieldValidator` |
| **$N_{12}$** | `dataset_record_hash` | Append-only database record (`AASI-P23-CFD-XXX`) |

Any tampering with remote solver logs, residual histories, or physical coefficients invalidates the root Merkle hash, causing the ingestion pipeline to reject the simulation immediately.
