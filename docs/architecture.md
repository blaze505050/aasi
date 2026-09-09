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

## Future Architecture (Upcoming Phases)

```
                          ┌───────────────────────────┐
                          │   AASI Scientific Agent   │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│  Scientific Tools   │      │   Knowledge & RAG   │      │ Physics AI & Sim    │
│ ─────────────────── │      │ ─────────────────── │      │ ─────────────────── │
│ • Orbital Mechanics │      │ • NASA NTRS & NACA  │      │ • PINN / PINO / FNO │
│ • RocketPy Engine   │      │ • Hybrid Retriever  │      │ • OpenFOAM Sweeps   │
│ • Symbolic Math     │      │ • Wind Tunnel Polars│      │ • MeshGraphNet      │
│ • Pint Units        │      │ • Provenance Audit  │      │ • Neural Surrogates │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │ Autonomous Research Loops │
                          │ • Hypothesis formulation  │
                          │ • Multi-fidelity sweeps   │
                          │ • Technical publication   │
                          └───────────────────────────┘
```

- **Phase 4**: Physics AI Models & Neural Surrogates (PINNs, PINO, FNO, MeshGraphNet, verification engine).
- **Phase 5**: Autonomous Simulation & Meshing (OpenFOAM automation, SU2 integration, grid convergence studies).
- **Phase 6**: Autonomous Scientific Research Loops (hypothesis generation, active learning experiment design).

