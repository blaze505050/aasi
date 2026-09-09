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

## Future Architecture (Upcoming Phases)

```
                          ┌───────────────────────────┐
                          │   AASI Scientific Agent   │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│  Scientific Tools   │      │   Retrieval & RAG   │      │ Verification Engine │
│ ─────────────────── │      │ ─────────────────── │      │ ─────────────────── │
│ • Orbital Mechanics │      │ • ArXiv & NASA NTRS │      │ • Dimensional Check │
│ • RocketPy Engine   │      │ • AIAA Papers       │      │ • Unit Sanity Tests │
│ • Aerodynamics / CFD│      │ • Vector DB Index   │      │ • Cross-Model Audit │
│ • Thermal Analysis  │      │ • Formula Parsing   │      │ • Code Sandbox      │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │ Autonomous Research Loops │
                          │ • Hypothesis formulation  │
                          │ • Iterative simulation    │
                          │ • Report generation       │
                          └───────────────────────────┘
```

- **Phase 3**: Aerospace Literature RAG (NASA Technical Reports, ArXiv papers, AIAA standards).
- **Phase 4**: Verification engine & dimensional consistency checks.
- **Phase 5**: Autonomous scientific research loops and simulation sweeps.
