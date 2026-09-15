# AASI System Architecture: Autonomous Aerospace Scientific Intelligence

**Document Version:** 25.0.0 (Final Phase 25 Architecture Reference)  
**Governing Standard:** ASME V&V 20 / ISO 9001 Cryptographic Scientific Integrity  
**Core Architectural Doctrine:** Absolute Anti-Fabrication Rule & Fail-Closed Scientific Governance  

---

## 1. Executive System Overview

The **Autonomous Aerospace Scientific Intelligence (AASI)** platform is an advanced, end-to-end scientific research environment designed for autonomous aerodynamic discovery, surrogate model training, uncertainty-guided experiment design, and rigorous computational fluid dynamics (CFD) validation.

Unlike conventional machine learning platforms that permit synthetic mocks or unvalidated proxy models, AASI enforces a **fail-closed, evidence-based scientific architecture**. Every claim, prediction, and mesh generation step is cryptographically bound, independently verifiable, and protected against scientific fabrication.

---

## 2. The Human Execution Boundary Principle

A fundamental architectural breakthrough of Phase 24 and Phase 25 is the formal definition of the **Autonomous Discovery with Human Execution Boundary** (`AUTONOMOUS_DISCOVERY_WITH_HUMAN_EXECUTION_BOUNDARY`).

```mermaid
flowchart TB
    subgraph AutonomousAI ["AASI AI Autonomous Domain"]
        direction TB
        A1["Active Learning Engine<br/>(Conformal Uncertainty)"] --> A2["Geometry Profiler<br/>(Procedural NACA / Custom)"]
        A2 --> A3["OpenFOAM Deck Synthesizer<br/>(0/, constant/, system/)"]
        A3 --> A4["Colab Notebook Generator<br/>(15 Hardened Execution Steps)"]
        A4 --> A5["Cryptographic Case Packager<br/>(case.tar.gz + notebook.ipynb)"]
    end

    subgraph Boundary ["Human Execution Boundary"]
        direction TB
        H1["Human Operator Authenticates<br/>& Dispatches Google Colab Session"]
        H2["Operator Runs Notebook on<br/>Google Colab Hardware (T4 / High-RAM)"]
        H3["Operator Downloads<br/>Verified results.tar.gz"]
    end

    subgraph IngestionGovernance ["AASI Scientific Ingestion & Governance"]
        direction TB
        G1["Ingestion API<br/>POST /api/compute/jobs/{id}/import"]
        G2["Cryptographic Digest &<br/>Merkle DAG Provenance Validator"]
        G3["ASME V&V 20 & Physics Gatekeeper<br/>(Bernoulli Cp ≤ 1.05, CD > 0)"]
        G4["Stage-10 Governance Auditor<br/>(Fail-Closed Promotion Gate)"]
    end

    A5 ==>|"Staged Deck Handoff"| H1
    H1 --> H2 --> H3
    H3 ==>|"Tarball Upload"| G1
    G1 --> G2 --> G3 --> G4
```

### 2.1 Autonomous Domain Capabilities
The AASI autonomous system operates without human intervention to:
1. **Identify Epistemic Gaps:** Conformal prediction intervals and Mahalanobis distance metrics highlight airfoil geometries where model uncertainty is highest.
2. **Synthesize Aerodynamic Geometries:** Procedural generators construct smooth, cambered, or supercritical profiles (e.g., NACA 0012, NACA 4412, NACA 6409) with cosine-clustered coordinates.
3. **Generate Valid OpenFOAM Dictionaries:** Generates `blockMeshDict`, `fvSchemes`, `fvSolution`, `controlDict`, and turbulence model configurations (`kOmegaSST`).
4. **Compile Colab Automation Notebooks:** Packages a standalone, hardened 15-cell Python notebook that installs OpenFOAM, meshes the domain, runs `simpleFoam`, and extracts force coefficients.
5. **Stage Bundles:** Commits all inputs, configuration checksums, and metadata to `data/compute_jobs/<job_id>/`.

### 2.2 Human Boundary Requirements
Direct execution on unmanaged external cloud servers (Google Colab) requires a human operator for:
1. **Interactive Session Initialization:** Authenticating to Google services and provisioning cloud GPU/CPU hardware.
2. **Interactive Run Execution:** Executing the staged notebook within the ephemeral Colab runtime.
3. **Artifact Retrieval:** Downloading `results.tar.gz` and delivering it to AASI's import endpoint.

This architecture ensures zero unverified mock execution: the system never pretends an experiment has completed when it is merely staged.

---

## 3. End-to-End System Architecture

```mermaid
graph LR
    subgraph DataTier ["Data & Knowledge Tier"]
        DB1[("Literature Polars<br/>NACA / Abbott & von Doenhoff")]
        DB2[("AirfRANS CFD<br/>1,000 Incompressible Meshes")]
        DB3[("Cryptographic Bundles<br/>Phases 21–24 JSON")]
        DB4[("Frozen Benchmark<br/>phase22_frozen_test.json")]
    end

    subgraph CoreEngine ["Aerospace Scientific Backend (FastAPI / PyTorch)"]
        AS["AeroSurrogateV1<br/>Dual-Stream Neural Operator"]
        UQ["Conformal UQ &<br/>Mahalanobis Router"]
        CFD["CFD Ingestion &<br/>Parser Engine"]
        MERKLE["12-Node Merkle DAG<br/>Provenance Engine"]
        STAGE10["Stage-10 Auditor<br/>(12 Criteria)"]
    end

    subgraph PresentationTier ["User Experience Tier (Next.js 14 / React)"]
        MC["Phase 25 Scientific<br/>Mission Control"]
        COLAB_CR["Phase 24 Colab<br/>Workflow Room"]
        PHYS_LAB["Physics-AI Lab &<br/>Polar Sweeps"]
        VV["ASME V&V 20 &<br/>GCI Calculator"]
    end

    DB1 --> AS
    DB2 --> AS
    AS --> UQ
    UQ --> CFD
    CFD --> MERKLE
    MERKLE --> STAGE10
    DB4 --> STAGE10
    
    STAGE10 --> MC
    CFD --> COLAB_CR
    AS --> PHYS_LAB
    CFD --> VV
```

---

## 4. Cryptographic Provenance Architecture

AASI establishes mathematical guarantees of scientific integrity using an unbroken **12-Node Cryptographic Merkle DAG**:

```
Node 01: Airfoil Geometry Coordinates (SHA-256)
Node 02: Inflow Physics & Reynolds / Mach Specification (SHA-256)
Node 03: Boundary Layer & Domain Extents (SHA-256)
Node 04: Mesh Generation & blockMeshDict / snappyHexMesh (SHA-256)
Node 05: Discretization Schemes & Solver Configuration (SHA-256)
Node 06: Solver Execution Transcript & Convergence History (SHA-256)
Node 07: Raw Volumetric / Surface Velocity & Pressure Fields (SHA-256)
Node 08: Post-Processed Force Coefficients CL, CD, CM (SHA-256)
Node 09: ASME V&V 20 Grid Convergence & Uncertainty (SHA-256)
Node 10: Model Fine-Tuning Hyperparameters & Data Split (SHA-256)
Node 11: Candidate Checkpoint Weights (SHA-256)
Node 12: Frozen Benchmark Evaluation & Scientific Conclusion (SHA-256)
```

Each node includes the hash of its parent node. Any tampering with raw flow field data, convergence iterations, or benchmark scores invalidates the entire DAG root hash.

---

## 5. ASME V&V 20 Physical Validation Gates

Before any simulation or surrogate output is admitted to the scientific knowledge base, it must pass automated physical validation gates:

1. **Bernoulli Total Pressure Ceiling:** Surface pressure coefficient $C_p$ cannot exceed $1.05$:
   $$C_p \le 1.05$$
2. **Suction Peak Integrity:** Minimum surface pressure $C_{p,\min} < 0.0$ on the upper surface for positive angles of attack ($\alpha > 0^\circ$).
3. **Physical Drag Positivity:** Total drag coefficient must be strictly positive:
   $$C_D > 0.0001$$
4. **Grid Convergence Index (GCI):** Roache GCI evaluated across fine, medium, and coarse meshes:
   $$GCI_{\text{fine}} = \frac{F_s |e_{\text{rel}}|}{r^p - 1}$$
   where $F_s = 1.25$, $r$ is the grid refinement ratio ($r \ge 1.3$), and $p$ is the observed order of convergence.

---

## 6. Frozen Benchmark Governance Architecture

To eliminate publication bias, data leakage, and artificial score inflation:

1. **Pre-Registration:** The test evaluation dataset is stored at `data/experiments/phase22_frozen_test.json`.
2. **Cryptographic Locking:** Its SHA-256 hash is permanently pinned in system governance:
   $$\text{Hash}_{\text{expected}} = \texttt{fa7b3d11b958cc85b2bad3167391c0514d00c097d0fb878e28a1c4aab048e3b8}$$
3. **Automated Rollback Engine:** If active learning fine-tuning causes performance degradation ($R^2_{\text{candidate}} < R^2_{\text{baseline}}$), the system logs the degradation honestly (`DEGRADED`), refuses promotion, and rolls back weights to the baseline checkpoint.

---

## 7. Storage & Directory Layout

```
AASI/
├── backend/
│   ├── api/                     # REST routers & controllers
│   ├── compute/                 # Colab fabric, remote staging & local solvers
│   │   ├── colab.py             # Colab execution manager & packager
│   │   ├── openfoam.py          # Native OpenFOAM deck generator
│   │   └── base.py              # Abstract compute interfaces
│   ├── cfd/                     # Meshing, ingestion & validation engines
│   │   ├── field_ingestion.py   # Raw OpenFOAM file parser & validator
│   │   ├── openfoam_bridge.py   # Solver bridging & verification
│   │   └── mesher.py            # NACA procedural coordinate mesher
│   ├── physics_ai/              # ML surrogates & uncertainty quantification
│   │   ├── aero_surrogate.py    # AeroSurrogateV1 neural operator
│   │   └── uncertainty.py       # Conformal Mahalanobis router
│   └── research/                # Scientific governance & reproduction
│       ├── stage10_governance.py# 12-point Stage-10 auditor
│       ├── reproduction_verifier_phase21.py
│       ├── reproduction_verifier_phase22.py
│       ├── reproduction_verifier_phase23.py
│       └── reproduction_verifier_phase24.py
├── data/
│   ├── compute_jobs/            # Staged & executed compute jobs
│   │   ├── P24-JOB-C1-NACA0012/ # Staged Colab bundle (Cycle 1)
│   │   ├── P24-JOB-C2-NACA4412/ # Staged Colab bundle (Cycle 2)
│   │   └── P24-JOB-C3-NACA6409/ # Staged Colab bundle (Cycle 3)
│   ├── experiments/             # Experiment registry & frozen benchmarks
│   │   └── phase22_frozen_test.json
│   └── reproduction/bundles/    # Standalone cryptographic verification bundles
│       ├── reproduction_bundle_phase21.json
│       ├── reproduction_bundle_phase22.json
│       ├── reproduction_bundle_phase23.json
│       └── reproduction_bundle_phase24.json
├── docs/                        # Complete scientific audit & documentation
│   ├── final-scientific-audit.md
│   ├── reproducibility-final-audit.md
│   ├── aasi-final-architecture.md
│   ├── aasi-final-user-guide.md
│   └── AASI-FINAL-SCIENTIFIC-REPORT.md
├── frontend/                    # Next.js 14 Web Application
│   └── app/page.tsx             # Scientific Mission Control & Lab Views
└── tests/                       # 100% Automated Test Suite
    ├── test_final_scientific_integrity.py  # 15 Adversarial attack tests
    └── ... (500+ comprehensive tests)
```

---

## 8. Architectural Summary

AASI establishes that genuine computational science does not require synthetic shortcuts. By decoupling **autonomous AI discovery** from the **human execution boundary**, and enforcing cryptographic verification at every boundary crossing, AASI provides an unassailable foundation for automated aerospace research.
