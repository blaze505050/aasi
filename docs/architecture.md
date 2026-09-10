# AASI System Architecture

## Overview

**AASI (Autonomous Aerospace Scientific Intelligence)** is an experimental AI research assistant designed specifically for aerospace engineering, space science, and related computational disciplines.

> **Important Framing:**
> AASI is **not** an AGI, ASI, or superintelligence system. It is a domain-adapted AI assistant constructed with standard software engineering practices, open-weight language models, and structured tool orchestration.

---

## Phase 2 Architecture: Engineering Tool Intelligence

In Phase 2, AASI establishes the fundamental architectural principle:

### Core Principle: LLM $\neq$ Calculator

```
[ LLM (Language Model) ]                    [ Scientific Tool Subsystem ]
  • Natural language understanding            • Precise orbital mechanics (Astropy)
  • Problem formulation & intent parsing      • Propulsion sizing & Tsiolkovsky (RocketPy)
  • Tool selection & parameter extraction     • Symbolic algebra & verification (SymPy)
  • Technical explanation synthesis           • Explicit SI dimensional units (Pint)
```

**The language model is NEVER allowed to invent or fabricate engineering numbers.**  
When a calculation is required, the task is routed to Python engineering libraries, and the exact verified outputs are fed back to the LLM for contextual explanation.

---

## Execution Pipeline

```
[ User Query ]
      │
      ▼
[ Next.js Frontend ]
      │  HTTP / JSON (REST)
      ▼
[ FastAPI Gateway (/api/chat, /api/tools, /api/health) ]
      │
      ▼
[ AASI Agent Layer ]
      │
      ├───► [ Intent Classification ]
      │        ├── Conceptual? ──────────────► [ Direct LLM Inference ] ─────────┐
      │        │                                                                   │
      │        └── Computational?                                                 │
      │                 │                                                         │
      │                 ▼                                                         │
      │        [ Parameter Extraction & Validation ]                              │
      │                 │                                                         │
      │                 ▼                                                         │
      │        [ Tool Registry Dispatcher ]                                       │
      │                 ├── orbit.py (Astropy constants & two-body physics)       │
      │                 ├── rocket.py (RocketPy standard equations & sizing)      │
      │                 └── math_utils.py (SymPy symbolic verification)           │
      │                 │                                                         │
      │                 ▼                                                         │
      │        [ Structured Numerical Result ]                                    │
      │                 │                                                         │
      │                 ▼                                                         │
      │        [ Contextual Synthesis via LLM (Ollama) ]                          │
      │                 │                                                         │
      ▼                 ▼                                                         │
[ Unified Response: Trace + Calculations + Verification + Explanation ] ◄─────────┘
      │
      ▼
[ Next.js Telemetry UI: Trace badges, Calculation card, Explanations ]
```

---

## Tool Subsystem Architecture (`backend/tools/`)

The tool subsystem is modular and extensible via `backend/tools/registry.py`:

1. **Orbital Mechanics (`backend/tools/orbit.py`)**:
   - Backed by `astropy.constants` and `astropy.units`.
   - Operations: `circular_orbit`, `escape_velocity`, `hohmann_transfer`.
   - Supports Earth, Moon, Mars, Sun with exact gravitational parameters ($\mu = GM$) and radii.
   - Outputs: orbital radii, velocities, period, $\Delta v_1$, $\Delta v_2$, transfer duration, and explicit physical assumptions.

2. **Rocket Propulsion (`backend/tools/rocket.py`)**:
   - Standard SI rocketry formulations and RocketPy constants ($g_0 = 9.80665\text{ m/s}^2$).
   - Operations: `rocket_equation` (Tsiolkovsky $\Delta v = g_0 I_{sp} \ln(m_0/m_f)$), `required_mass_ratio`, `propellant_mass_estimation`.
   - Outputs: $\Delta v$, mass ratio, propellant mass, mass fraction, exhaust velocity, and assumptions.

3. **Symbolic Mathematics & Verification (`backend/tools/math_utils.py`)**:
   - Backed by `sympy` and Python `ast` security validator.
   - Operations: `symbolic_evaluation`, `solve_equation`, `verify_calculation`.
   - Protects against code injection via AST parsing (`validate_safe_math_expression`).
   - Provides independent re-computation of numerical results from first principles to ensure consistency.

4. **Dimensional Analysis & Units (`backend/tools/units.py`)**:
   - Backed by `pint.UnitRegistry`.
   - Operations: `convert`.
   - Provides verified conversion across distance, velocity, mass, time, and acceleration dimensions.

5. **Central Registry (`backend/tools/registry.py`)**:
   - Dynamic discovery and signature inspection.
   - Allows future engineering domains (aerodynamics, thermal, CFD, flight dynamics) to register without altering agent code.

For complete verification test matrices, see [Phase 2 Validation Report](qa/PHASE_2_VALIDATION.md).

---

## Tool Execution Trace

All computational responses include a user-safe execution trace:
```json
{
  "tool_calls": [
    {
      "tool": "orbit",
      "operation": "circular_orbit",
      "status": "success",
      "trace": [
        "Identified aerospace calculation: orbit.circular_orbit",
        "Extracted input parameters: {'altitude_km': 500.0, 'central_body': 'Earth'}",
        "Executing verified tool 'orbit' (operation: 'circular_orbit')",
        "Executed calculation successfully with physical constants",
        "Independently verified orbital velocity with SymPy",
        "Generating technical synthesis with open-weight model",
        "Completed response synthesis"
      ]
    }
  ]
}
```
**Safety Guarantee:** Private chain-of-thought is never exposed; only auditable operational milestones are presented.

---

## Phase 3 Architecture: Scientific Knowledge & Dataset Foundation

In Phase 3, AASI introduces a provenance-first scientific knowledge and dataset retrieval infrastructure that enforces the principle:

### Core Principle: Literature & Datasets Are Not Ground Truth Without Provenance

```
                              [ User Scientific Query ]
                                          │
                                          ▼
                       [ Result Resolution Dispatcher ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     [ Exact Parameterized Query ]                 [ General Literature / Inquiry ]
                  │                                               │
                  ▼                                               ▼
       [ Dataset Registry ]                            [ Hybrid Retriever ]
    • Experimental Wind Tunnel Polars               • FAISS Vector Similarity (Dense)
    • Validated CFD Benchmarks                      • BM25 Aerospace Keyword Scoring
    • Normalized Condition Matching                 • Metadata Filtering (Organization, Type)
                  │                                               │
                  ▼                                               ▼
     [ Validated Dataset Record ]                      [ Scored Document Chunks ]
    • Provenance (SHA-256, Report #)                • Section & Page Hierarchy
    • Grid / Mesh Classification                    • LaTeX Equation Preservation
    • Uncertainty / Error Bounds                                  │
                  │                                               ▼
                  │                                  [ Quarantine Sanitizer ]
                  │                                 • Strips Prompt Injection Attacks
                  │                                 • Isolates Untrusted Text Data
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          │
                                          ▼
                         [ Context-Enriched Scientific LLM ]
                                          │
                                          ▼
                       [ Verified Response + Full Citations ]
                      • Mathematical Equations ($C_L$, $C_D$)
                      • Direct Report Numbers (e.g. NACA-TR-824)
                      • Cryptographic Hashes & Verification Tags
```

### Knowledge Subsystem Architecture (`backend/knowledge/`)

1. **Information Models (`backend/knowledge/models.py`)**:
   - `ScientificObjectType`: Categorizes documents, datasets, experimental data, simulation benchmarks, surrogates, analytical results, and retrieved references.
   - `Provenance`: Full metadata tracking (title, authors, organization, report number, DOI, license, publication date, SHA-256 hash).
   - `Equation`: Preserves LaTeX syntax, plain text, variable definitions, and dimensional units.
   - `CFDDataModel`: Captures solver, mesh type, cell count, turbulence model, $y^+$, convergence criteria, and boundary conditions.
   - `Chunk`: Preserves section hierarchy, page numbers, equation bindings, and token lengths.

2. **Source Registries (`backend/knowledge/source_registry.py`)**:
   - Manages authorized aerospace repositories: `NASA_NTRS`, `NACA`, `ARXIV`, `ESA` (Planned), `ISRO` (Planned), and `OPEN_DATASETS`.
   - Explicitly reports unsupported / planned sources with honest technical reasons (e.g. lack of public open-access REST APIs).

3. **Hybrid Scientific Retrieval (`backend/knowledge/retriever.py`)**:
   - Combines 384-dimensional dense semantic vector similarity (backed by `FAISSVectorIndex`) with exact aerospace keyword boosting (NACA identifiers, Mach numbers, Reynolds numbers, turbulence models).
   - Enforces metadata filters (e.g., organization `NASA`, type `EXPERIMENT`).

4. **Condition-Aware Dataset Registry (`backend/knowledge/dataset_registry.py` & `resolution.py`)**:
   - Resolves queries matching explicit experimental conditions (e.g. NACA 0012 at $M=0.3$, $Re=5\times 10^5$, $\alpha=8^\circ$) directly to validated wind tunnel polars or benchmark OpenFOAM RANS CFD results rather than loose text approximations.

5. **Prompt-Injection Quarantined RAG (`backend/knowledge/rag.py`)**:
   - Wraps all retrieved literature text in `<UNTRUSTED_REFERENCE_DATA>` isolation blocks.
   - Neutralizes control instruction strings (e.g. "Ignore all previous instructions") before feeding context to the LLM.

6. **Physics AI Neural Surrogate Stubs (`backend/physics/models.py`)**:
   - Establishes clean abstract interfaces (`PINNModel`, `PINOModel`, `FNOModel`, `MeshGraphNetModel`, `DoMINOModel`, etc.) raising explicit `NotImplementedError("Planned for Phase 4")` to prepare the foundation without prematurely destabilizing the stack.

For detailed knowledge subsystem documentation, see:
- [Knowledge Architecture](knowledge/architecture.md)
- [Data Sources](knowledge/data-sources.md)
- [Provenance System](knowledge/provenance.md)
- [Dataset Schema](knowledge/dataset-schema.md)
- [Retrieval Architecture](knowledge/retrieval.md)

---

## Phase 4 Architecture: Scientific Result Resolution & Simulation Fabric

Phase 4 elevates AASI from a literature retrieval and tool-calling system to an integrated, provenance-enforcing scientific resolution engine backed by a sandboxed simulation execution fabric.

### Core Principle: Deterministic Pre-Resolution & Strict Epistemic Honesty

```
                                [ Scientific User Query ]
                                            │
                                            ▼
                           [ Parameter Normalizer & Auditor ]
                         (Level 0: α in deg, M, Re, T, p audit)
                                            │
                                            ▼
                           [ 8-Level Resolution Engine ]
       ┌────────────────────────────────────┼──────────────────────────────────┐
       │                                    │                                  │
       ▼                                    ▼                                  ▼
[ Level 1 & 2: Experiment ]       [ Level 3: Validated CFD ]       [ Level 4: Surrogate AI ]
NASA Wind Tunnel Polars           Benchmark RANS Simulations       PINN / PINO Registry
(NACA-TR-824, Abbott 1959)        (OpenFOAM, SA/SST models)        (Strict Validity Domain)
Status: OFFICIAL_EXPERIMENT       Status: VALIDATED_CFD            Status: SURROGATE_PREDICTION
       │                                    │                                  │
       └────────────────────────────────────┼──────────────────────────────────┘
                                            │ (If no pre-computed data)
                                            ▼
                              [ Level 5: Analytical Solvers ]
                                Thin Airfoil / Vortex Lattice
                                Status: ANALYTICAL_RESULT
                                            │
                                            │ (If local execution requested)
                                            ▼
                             [ Level 6: Simulation Fabric ]
                                Sandboxed OpenFOAM / SU2 / XFOIL
                                Status: LOCAL_CFD
                                            │
                                            │ (If inputs ambiguous / unresolvable)
                                            ▼
                             [ Level 7: Parameter Clarification ]
                                Status: NO_RESULT (Requests exact inputs)
```

### 1. Scientific Resolution Subsystem (`backend/science/`)

- **Condition Normalization (`normalizer.py`)**: Normalizes Mach number, Reynolds number, angle of attack (degrees/radians), chord length, pressure, temperature, and aerodynamic coefficients ($C_L, C_D, C_M$).
- **Dataset Matcher (`matcher.py`)**: Evaluates Euclidean condition distance ($d \le 0.05$) across normalized aerodynamic parameter spaces.
- **Epistemic Classification**: Assigns definitive tags to all numerical results:
  - `OFFICIAL_EXPERIMENT`: Validated wind tunnel literature (NASA, NACA, AGARD).
  - `VALIDATED_CFD`: Established peer-reviewed CFD benchmark cases.
  - `SURROGATE_PREDICTION`: In-domain neural surrogate inference.
  - `ANALYTICAL_RESULT`: First-principles engineering formulations.
  - `LOCAL_CFD`: Sandboxed local solver execution.
  - `NO_RESULT`: Unresolved query triggering explicit parameter clarification.
- **Discrepancy Reconciliation (`conflict.py`)**: Automatically detects divergence between experimental and CFD data (e.g. $\Delta C_D > 10\%$) and provides physical reconciliation (boundary layer tripping, wind tunnel wall interference, turbulence model eddy viscosity damping).

### 2. Simulation Execution Fabric (`backend/simulation/`)

```
[ Simulation Request ]
          │
          ▼
[ Simulation Runner ]
          │
          ├──► [ Security Sandbox ]
          │       • Binary allowlist: simpleFoam, blockMesh, SU2_CFD, xfoil
          │       • Execution directory isolation: cases/<case_id>/
          │       • Execution timeouts (default: 300s, max: 1800s)
          │       • Maximum output cap: 50MB
          │       • Environment sanitization (no arbitrary shell injection)
          │
          ├──► [ Solver Adapters ]
          │       • OpenFOAM (0/, constant/, system/ dictionaries)
          │       • SU2 (.cfg config writer & surface flow parser)
          │       • XFOIL (NACA profile polar generation & viscous sweeps)
          │       • XFLR5 (project deck generator)
          │
          └──► [ Artifact & Provenance Manager ]
                  • SHA-256 digest of input mesh and configuration files
                  • Execution logs and convergence history
                  • Reproducible manifest: EXP-<case_id>.manifest.json
```

- **Honest Solver Detection (`detector.py`)**: Autonomously inspects native Windows binaries and WSL2 Linux distributions. Honestly reports `NOT_AVAILABLE` when solvers are not installed, without fabricating capabilities.
- **Dry-Run Case Deck Generation**: Generates syntactically correct case decks and manifests for OpenFOAM, SU2, and XFOIL even when physical solvers are uninstalled.

---

## Phase 5 Architecture: Tri-Layer Scientific Intelligence

Phase 5 establishes the full **Tri-Layer Architecture** for autonomous aerospace scientific intelligence:

```
                            ┌─────────────────────────────────────────┐
                            │          AASI Scientific Agent          │
                            │      (LLM Context & Orchestrator)       │
                            └────────────────────┬────────────────────┘
                                                 │
          ┌──────────────────────────────────────┼──────────────────────────────────────┐
          ▼                                      ▼                                      ▼
┌──────────────────────────────┐       ┌──────────────────────────────┐       ┌──────────────────────────────┐
│  LAYER A: KNOWLEDGE & SOURCES│       │  LAYER B: PHYSICS AI & DATA  │       │  LAYER C: SIMULATION & COMP  │
│ ──────────────────────────── │       │ ──────────────────────────── │       │ ──────────────────────────── │
│ • 15 Scientific Disciplines  │       │ • Open Dataset Factory       │       │ • Multi-Backend Dispatch     │
│ • NASA NTRS & NACA Connectors│       │   (AirfRANS, CRM, Abbott)    │       │   (Local, Remote, User, Cache│
│ • ISRO / ESA Public Registrie│       │ • Leakage-Free Geometry Split│       │ • Standalone aasi_case/ Deck │
│ • Strict SpaceX Claim Refusal│       │ • PhysicsNeMo Recipe Foundatn│       │ • 14-Section Execution Guide │
│ • Dynamic Current Events     │       │ • PhysicsModelRegistry       │       │ • Artifact Ingestion Service │
│   (ISO Temporal Separation)  │       │ • Monotonicity & Symm Audits │       │ • OpenFOAM / SU2 / XFOIL     │
│ • 16-Entity Knowledge Graph  │       │ • Active Learning Loop       │       │ • SHA-256 Provenance Manifest│
└──────────────────────────────┘       └──────────────────────────────┘       └──────────────────────────────┘
```

### 1. Layer A: Knowledge Federation & Dynamic Temporal Separation
- **15 Aerospace Disciplines:** Comprehensive taxonomy from aerodynamics, propulsion, and orbital mechanics to EDL, space weather, and life support.
- **Authentic Registries:** Real public connectors for NASA NTRS, NACA, ISRO, and ESA without simulated or fabricated private APIs.
- **Strict Commercial Guardrail:** Rejects claims of access to internal SpaceX or proprietary corporate design files (`CitationGuardrail`).
- **Dynamic Current Events:** Events (`CurrentInformationService`) are timestamped with ISO-8601 UTC and separated from immutable physical citations (`CURRENT_INFORMATION` vs `SCIENTIFIC_REFERENCE`).
- **Semantic Knowledge Graph:** In-memory graph linking 16 entity types via 10 directed relation types (`USES`, `SIMULATED_BY`, `MEASURED_BY`, etc.).

### 2. Layer B: Physics AI & Dataset Factory
- **High-Value Open Datasets:** Manifests for AirfRANS (1,000 RANS simulations), NASA CRM, and Abbott & von Doenhoff wind tunnel polars.
- **Hardware-Aware Download-on-Demand:** Enforces a 2 GB local storage ceiling to protect developer laptops.
- **Zero Geometry Leakage:** `GeometryLevelSplitter` strictly isolates airfoil geometries between partitions ($\text{Geometries}_{\text{Train}} \cap \text{Geometries}_{\text{Test}} = \emptyset$).
- **PhysicsNeMo Exportable Recipes:** Standalone GPU training scripts for AeroGraphNet (GNN) and 2D Fourier Neural Operator (FNO-2D) in `training/physicsnemo/`.
- **Model Registry & Integrity:** Versioned surrogates with validity envelopes, parameter counts, and SHA-256 weight checksums.
- **Physical Monotonicity Gates:** Rejects surrogates violating pre-stall lift monotonicity ($dC_L/d\alpha > 0$) or symmetric airfoil zero-lift sanity ($C_L(0) \approx 0$).
- **Active Learning Engine:** Exploits epistemic uncertainty in stall and transonic shock onset to rank candidate simulation points.

### 3. Layer C: Deterministic Engineering Agent & User-Executed CFD
- **Multi-Backend Compute Fabric:** Flexible dispatch across `LOCAL`, `REMOTE`, `USER_EXECUTED`, and `CACHED` modes.
- **Standalone `aasi_case/` Generator:** Creates self-contained OpenFOAM directories with dictionary files (`0/`, `constant/`, `system/`), mesh scripts (`blockMeshDict`), shell runners (`run.sh`, `clean.sh`), and the mandatory 14-section `README.md`.
- **Artifact Ingestion Engine:** Parses returned `forceCoeffs.dat`, SU2 `history.csv`, or XFOIL polars, checks physical bounds ($C_D > 0, |C_L| \le 3.5$), and logs SHA-256 provenance.



