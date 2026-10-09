# AASI Phase 27: Remote Compute Fabric & Execution Providers

## 1. Executive Summary
The **Remote Compute Fabric** decouples AASI's autonomous scientific discovery agent from physical solver execution hardware. By routing computational jobs to external infrastructure, AASI completely protects the operator's machine from CPU/GPU and thermal load while ensuring absolute scientific integrity.

---

## 2. Compute Provider Hierarchy & Capability Matrix

| Provider | Execution Mode | Unattended | Observability Level | Verification | Laptop CPU Load |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Google Colab** | User-Authorized 1-Click | No | Limited (`UNKNOWN` while running) | Mandatory SHA-256 & Token | **0% (Zero)** |
| **Remote HPC** | Batch Scheduler (SLURM) | Yes | Polling Milestones via SSH/REST | Mandatory ASME V&V 20 | **0% (Zero)** |
| **Local OpenFOAM** | Local Process Daemon | Yes | Process / Tail Logs | Cryptographic Hash | **High (Disabled by Policy)** |

---

## 3. Google Colab 1-Click Provider (`ColabProvider`)

### A. Terms of Service & Anti-Circumvention Doctrine
AASI operates under strict compliance with Google Colab's acceptable use policies:
1. **Zero Browser Automation**: AASI never launches automated headless puppeteers or bypasses Google account authentication/CAPTCHAs.
2. **Minimal Operator Authorization**: A single human click (`Open in Google Colab`) transitions the state and opens the staged runner notebook in Colab.
3. **Honest Observability**: AASI does not possess telemetry access into Google's isolated virtual machines. While the simulation runs in Colab, AASI honestly reports:
   $$\mathbf{REMOTE\ STATUS:\ UNKNOWN}$$
   rather than fabricating artificial progress bars or synthetic intermediate values.

### B. Session Bundle Synthesis (`ColabSessionPackager`)
When a case is staged for Colab, the session packager generates:
1. `job_manifest.json`: Cryptographic specification containing `job_id`, `geometry_id`, flow conditions, `case_tar_hash`, and timestamp.
2. `case.tar.gz`: Pre-configured OpenFOAM case directory containing `0/`, `constant/`, `system/`, and `boundaryData/`.
3. `notebook.ipynb`: An all-in-one hardened runner that:
   - Installs OpenFOAM 10 in Colab via `apt-get` with zero user configuration.
   - Extracts and meshes the geometry via `blockMesh` and `checkMesh`.
   - Executes `simpleFoam` with convergence tracking.
   - Packages `results.tar.gz` with cryptographic checksums and output fields (`p`, `U`, `k`, `omega`, `forceCoeffs.dat`).
4. `launch_url`: Direct URL linking to Google Colab.

---

## 4. Remote HPC Provider (`RemoteHPCProvider`)

### A. SLURM Batch Script Generation
For institutional and supercomputing clusters, `RemoteHPCProvider` synthesizes `#SBATCH` submission decks:
```bash
#!/bin/bash
#SBATCH --job-name=JOB-NACA4412-AOA4
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%j.out

module load openfoam/10
source /opt/openfoam10/etc/bashrc

tar -xzf case.tar.gz
cd case
blockMesh > log.blockMesh 2>&1
checkMesh > log.checkMesh 2>&1
simpleFoam > log.simpleFoam 2>&1
tar -czf ../results.tar.gz postProcessing/ 0/ [1-9]*/ log.*
```

### B. Non-Mutating Failure Recovery
If a solver fails due to numerical divergence:
1. Residual history is diagnosed via `NumericalDivergenceError` classifier.
2. Safe repair rules propose parameter adjustments (e.g., reduce Courant number from $1.0$ to $0.5$, or relax pressure under-relaxation factor from $0.3$ to $0.2$).
3. A **new immutable case hash** is synthesized and staged. Up to 3 automatic retries are allowed before escalating to `HUMAN_REVIEW_REQUIRED`.

---

## 5. Persistent 15-State Monotonic Job Lifecycle

Each job in `PersistentJobQueue` moves through deterministic states recorded with HMAC-SHA256 transition tokens:

```
[CREATED] ──> [QUEUED] ──> [ALLOCATED] ──> [STAGED] ──> [AUTHORIZATION_REQUIRED]
                                                                  │
                                                                  ▼
[RESULTS_READY] <── [RUNNING] <── [DISPATCHED] <──────────────────┘
      │
      ▼
[INGESTING] ──> [VERIFYING] ──> [VALIDATED] ──> [COMPLETED]
      │              │               │
      └──────────────┴───────────────┴────────> [FAILED] ──> [STAGED] (Safe Retry)
                                                   │
                                                   └───> [HUMAN_REVIEW_REQUIRED]
```
1. `CREATED`: Job planned by scientific intent.
2. `QUEUED`: Enqueued in persistent queue.
3. `ALLOCATED`: Remote provider selected by resource governance.
4. `STAGED`: Case deck, mesh, and execution package synthesized.
5. `AUTHORIZATION_REQUIRED`: Operator handoff boundary.
6. `DISPATCHED`: Staged package transferred/prepared for execution.
7. `RUNNING`: External hardware running simulation.
8. `RESULTS_READY`: Remote results archive available.
9. `INGESTING`: Raw results archive downloaded to content-addressed storage.
10. `VERIFYING`: HMAC-SHA256 signature and file integrity verified.
11. `VALIDATED`: ASME V&V 20 physical validation gate passed.
12. `COMPLETED`: Ingested into verified knowledge fabric.
13. `FAILED`: Simulation crashed or diverged.
14. `CANCELLED`: Operator aborted job.
15. `HUMAN_REVIEW_REQUIRED`: Exceeded retry limits or unrecoverable mesh defect.
