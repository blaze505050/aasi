# AASI Phase 23 Forensic Preflight Audit: Remote Compute Fabric & Colab Reality

**Directive:** AASI Master Engineering Directive — Phase 23  
**Governing Doctrine:** Absolute Anti-Fabrication Rule (Zero synthetic shortcuts, zero fabricated CFD outputs, zero unearned model promotion, fail-closed scientific governance)  
**Date:** September 14, 2026  
**System:** Autonomous Aerospace Scientific Investigator (AASI)  
**Host Platform:** Windows 11 Enterprise (AMD/Intel x86_64, 12 cores, 16 GB RAM)  

---

## 1. Executive Summary & Problem Context

In Phase 22, AASI successfully demonstrated autonomous closed-loop scientific governance on the host workstation. However, empirical solver probing verified that native Windows `simpleFoam.exe` was absent, WSL2 was offline (virtual disk located on detached volume `D:\`), and Docker was offline. As mandated by the Absolute Anti-Fabrication Rule, AASI properly halted in `USER_EXECUTED_REQUIRED` with Stage 8 model promotion (`AUTONOMOUS_ACTIVE_LEARNING_VALIDATED`). Promotion to Stage 9 (`REAL_CFD_CLOSED_LOOP_VALIDATED`) and Stage 10 (`SCIENTIFICALLY_TRUSTED`) remained blocked strictly due to the lack of live, verified solver execution.

Phase 23 directly addresses this computational bottleneck by establishing a **Remote Compute Fabric** with **Google Colab** as the initial opportunistic external execution backend. This preflight audit establishes the physical, legal, and operational realities governing this architecture.

---

## 2. Host Reality & Hardware Safety Boundaries

### 2.1 Host Resource Audit
A live audit of the local workstation confirms:
- **Available Storage:** $20.82\text{ GB}$ free on volume `C:\`.
- **Mandatory Storage Reserve:** $\ge 15.0\text{ GB}$ must remain untouched at all times.
- **Physical RAM:** $15.84\text{ GB}$ total ($83.2\%$ current utilization, leaving $\sim 2.66\text{ GB}$ free).
- **CPU:** 12 logical processors.

### 2.2 Workstation Execution Policy
Under Phase 23 engineering doctrine:
1. **The user's local Windows workstation must NOT execute heavy CFD calculations.** Local activities are restricted to lightweight orchestration, API serving, frontend rendering, mesh quality verification, preflight checks, and physical validation gating.
2. If any local operation threatens the $15.0\text{ GB}$ storage reserve or projects memory exhaustion ($< 1.0\text{ GB}$ free), the system unconditionally halts with `RESOURCE_LIMITED`.
3. Heavy OpenFOAM solves are delegated exclusively to the remote compute fabric.

---

## 3. Remote Compute Reality: Google Colab Policy & Governance

### 3.1 Platform Capabilities & Epistemic Boundaries
Google Colab provides ephemeral Linux virtual machines (Ubuntu 22.04 LTS, x86_64) equipped with multi-core CPUs, system memory ($\sim 12\text{--}25\text{ GB}$), and optional hardware accelerators (NVIDIA T4 / V100 / A100 GPUs).

However, Colab is fundamentally an **opportunistic computing platform**, not a persistent dedicated HPC cluster:
- Runtimes are ephemeral and may disconnect upon inactivity (idle timeout $\sim 90$ minutes, max session length $\sim 12$ hours).
- OpenFOAM is not pre-installed in standard Colab environments; it must be provisioned during runtime initialization (e.g. via `apt-get install openfoam` or containerized Apptainer/Singularity execution).
- Storage within the virtual machine instance is non-persistent unless explicitly mounted to Google Drive or exported via bundle artifacts.

### 3.2 Strict Anti-Circumvention Doctrine (Section P23-2)
AASI unconditionally prohibits any violation of Google Colab Terms of Service:
- **NO Account Automation:** AASI will never attempt automated Google account logins or credential harvesting.
- **NO CAPTCHA Bypass:** AASI will never attempt to evade human interaction challenges.
- **NO Anti-Idle Hacks:** AASI will never generate fake mouse/keyboard events or JavaScript console loops designed to prevent idle disconnection.
- **NO Persistent Web Service Tunnels:** AASI will never deploy unauthorized reverse proxies, SSH tunnels (e.g. ngrok, localtunnel), or hidden background daemons inside Colab to create persistent servers.
- **NO Resource Circumvention:** AASI will never bypass GPU allocation or memory limits.

### 3.3 The Legitimate Colab Execution Bundle Architecture
AASI interfaces with Colab exclusively through **supported, transparent, reproducible notebook and script bundles**:
1. AASI stages a complete, cryptographically hashed job bundle in `data/compute_jobs/{job_id}/`.
2. The bundle contains a fully reproducible Jupyter notebook (`notebook.ipynb`) alongside self-contained bash scripts (`run_openfoam.sh`), compressed case geometries (`case.tar.gz`), and manifest files (`job_manifest.json`).
3. The user or operator opens the notebook in Google Colab, executes the runtime verification and solver cells, and exports the signed result bundle back to AASI.
4. AASI independently verifies the integrity, convergence logs, and physical fields of the returned artifacts before admitting them to the scientific database.

---

## 4. Pre-Registered Scientific Experiment Matrix

To prevent p-hacking, outcome fabrication, and retroactive hypothesis fitting, Phase 23 pre-registers five empirical experiments:

| Experiment ID | Title | Core Scientific Question | Primary Metric / Gate |
| :--- | :--- | :--- | :--- |
| **P23-E001** | Remote CFD Execution Verification | Can AASI generate a compliant OpenFOAM case deck, package it into a Colab bundle, and execute `simpleFoam` on a remote Linux runtime? | Valid solver exit code 0, residual logs, force coefficients generated. |
| **P23-E002** | Remote CFD Ingestion Verification | Can AASI independently validate, unpack, and verify the physical realism of returned remote CFD fields without trust assumptions? | Physical Validation Gate: Bernoulli limit $\max C_p \le 1.05$, suction peak $\min C_p < 0$, drag $C_D \ge 0$. |
| **P23-E003** | Closed-Loop Retraining on Frozen Benchmark | Does adding genuine remote CFD data improve the physics surrogate on the pre-registered frozen test set? | Frozen test set evaluation ($26$ points, SHA-256 `9bc0be25...`): $\Delta R^2, \Delta\text{MAE}$. Verdict: `IMPROVED`, `UNCHANGED`, or `DEGRADED`. |
| **P23-E004** | Multi-Fidelity Discrepancy Calibration | Does calibrating low-fidelity empirical models with remote high-fidelity CFD observations reduce discrepancy on held-out geometries? | Multi-fidelity RMSE comparison: Low-fidelity vs High-fidelity vs Discrepancy model. |
| **P23-E005** | Uncertainty-Driven Autonomous Acquisition | Does the closed-loop discovery engine select future candidates based on measured conformal uncertainty and geometry OOD distance rather than arbitrary heuristics? | Acquisition score correlation with model prediction error across candidate pool. |

---

## 5. Frozen Test Discipline & Anti-Fabrication Safeguards

### 5.1 Immutable Frozen Test Set Preservation
The frozen out-of-distribution evaluation set generated in Phase 22 (`data/experiments/phase22_frozen_test.json`) contains 26 evaluation points spanning NACA 6409 (cambered thin profile) and NACA 4415 (cambered thick profile) across $\alpha \in [-2^\circ, 10^\circ]$ at Mach $0.15$ and Reynolds $3 \times 10^6$.
- **Expected SHA-256 Hash:**
  $$\mathbf{H}_{\text{frozen}} = \texttt{9bc0be258074900a35942fc6977ca3ffda73ad7ff392a2a07c3973c52a322421}$$
- This dataset is strictly held out. It will **never** be used for surrogate training, calibration, or hyperparameter tuning.

### 5.2 Model Promotion Governance
Model promotion adheres to the following immutable rules:
- **Stage 8 $\to$ Stage 9 (`REAL_CFD_CLOSED_LOOP_VALIDATED`):** Granted ONLY if live OpenFOAM execution is verified, all physical validation gates pass, cryptographic provenance DAG is complete, and frozen test evaluation demonstrates valid generalization.
- **Stage 9 $\to$ Stage 10 (`SCIENTIFICALLY_TRUSTED`):** Strenuously prohibited on a single successful run. Requires repeated, verified autonomous closed-loop iterations across multiple distinct geometries.
