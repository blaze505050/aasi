# AASI Scientific Result Resolution Hierarchy

## 1. Executive Summary

A core design principle of AASI (Autonomous Aerospace Scientific Intelligence) is:
> **The LLM is an orchestrator, not a CFD solver or numerical truth generator.**
> AASI must never fabricate quantitative engineering numbers when no verified dataset exists.

To enforce this, all quantitative engineering inquiries pass through a deterministic **8-level scientific resolution hierarchy**. Every result produced is assigned a strict **epistemic status tag** and a complete cryptographic and methodological provenance trace.

---

## 2. The 8-Level Resolution Hierarchy

```
Natural Language Engineering Query
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 0: Query Normalization & Completeness Audit           │
│  - Geometry canonicalization (e.g. "naca 0012" -> "NACA0012")│
│  - Pint unit conversions & normalization to SI              │
│  - Mach, Reynolds, AoA, and flow regime extraction           │
│  - Missing condition audit (checks for required parameters) │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Complete conditions)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 1: Scientific Dataset Registry Query                  │
│  - Indexes registered experimental & computational datasets │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 2: Official Experimental Database                     │
│  - Wind-tunnel polar data (NASA TN-D-628, NACA TR-824)     │
│  - Exact / near condition matching                          │
│  - Epistemic status: OFFICIAL_EXPERIMENT                    │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Cross-compare or fallback)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 3: Validated CFD Benchmark Database                   │
│  - High-fidelity RANS cases (simpleFoam, SST / SA models)   │
│  - Mesh cell counts, y+ < 1, residual convergence (< 1e-6)  │
│  - Epistemic status: VALIDATED_CFD                          │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Fallback if no database entry)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 4: Validated Physics AI Surrogate Models              │
│  - Fast surrogate inference (AeroGraphNet, PhysicsNeMo)     │
│  - Enforces declared validation domain envelope             │
│  - Rejects out-of-domain queries: SURROGATE_OUT_OF_DOMAIN   │
│  - Epistemic status: SURROGATE_PREDICTION                   │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Fallback if domain exceeded)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 5: Analytical / Numerical Engineering Solvers         │
│  - Classical mechanics & propulsion (Astropy, RocketPy)     │
│  - Symbolic verification & closed-form formulas (SymPy)     │
│  - Epistemic status: ANALYTICAL_RESULT                      │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Fallback if problem requires PDE)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 6: Simulation Execution Fabric                        │
│  - OpenFOAM / SU2 automated dictionary generation           │
│  - Dry-run validation & manifest generation                 │
│  - Epistemic status: LOCAL_CFD                              │
└──────────────────────────────┬──────────────────────────────┘
                               │ (If conditions incomplete / no solver)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 7: No Result & Parameter Clarification Request        │
│  - Never fabricates numbers                                 │
│  - Explicitly states which conditions are missing           │
│  - Epistemic status: NO_RESULT                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Epistemic Classification System

Every engineering answer or output in AASI must carry an explicit classification:

| Epistemic Status | UI Badge | Description |
| :--- | :--- | :--- |
| `OFFICIAL_EXPERIMENT` | Green | Authentic experimental measurements from accredited research facilities (NASA, DLR, ONERA). |
| `VALIDATED_CFD` | Cyan | Numerical CFD simulation converged with mesh independence and verified turbulence models. |
| `SURROGATE_PREDICTION` | Purple | Machine learning physics surrogate evaluating strictly within its validated training envelope. |
| `ANALYTICAL_RESULT` | Blue | Deterministic evaluation using verified equations (Astropy, RocketPy, SymPy). |
| `LOCAL_CFD` | Teal | Locally executed CFD solver run from the simulation fabric. |
| `DEMO_DATA` | Amber | Synthetic or demonstration test data; explicitly flagged to prevent confusion with truth. |
| `NO_RESULT` | Red | No verified data or solver available; prompts user for clarification. |

---

## 4. Multi-Source Conflict Resolution & Physics Reconciliation

When both Experimental and CFD records exist for the requested conditions (e.g. NACA 0012 at $M=0.15, Re=3\times 10^6, \alpha=4^\circ$), AASI does not randomly pick one.
The `ConflictResolutionEngine`:
1. Calculates the relative difference:
   $$\Delta = \frac{|V_{\text{exp}} - V_{\text{cfd}}|}{\frac{1}{2}(V_{\text{exp}} + V_{\text{cfd}})}$$
2. Classifies the discrepancy severity (`ACCEPTABLE_AGREEMENT` $<5\%$, `MINOR_DISCREPANCY` $5-10\%$, `SIGNIFICANT_DISCREPANCY` $>10\%$).
3. Explains the physical aerodynamic source of the discrepancy:
   - **Boundary Layer Tripping**: Fixed transition vs natural transition in wind tunnel.
   - **Wind Tunnel Wall Interference**: Solid blockage and streamline curvature corrections.
   - **Eddy-Viscosity Damping**: Under/over-prediction of separation bubbles in linear eddy-viscosity RANS models ($k-\omega$ SST vs Spalart-Allmaras).
4. Displays both values side-by-side with full provenance.

---

## 5. Condition Matching Modes

The `ConditionMatchingEngine` categorizes matches into four distinct certainty grades:
- `EXACT_MATCH`: Flow conditions match database grid within tight tolerances ($|\Delta M| \le 0.02, |\Delta Re|/Re \le 0.05, |\Delta \alpha| \le 0.25^\circ$).
- `NEAR_MATCH`: Conditions fall within interpolation proximity ($|\Delta \alpha| \le 1.0^\circ$).
- `INTERPOLATION_CANDIDATE`: Multiple surrounding data points can be used for verified polynomial or spline interpolation.
- `OUTSIDE_VALIDATION_DOMAIN`: Flow conditions exceed the database or surrogate validity envelope.
