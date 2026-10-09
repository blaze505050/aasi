# AASI Product Definition — Phase 1

> **Audit Date:** 2026-09-25

---

## 1. What problem does AASI solve?

Aerospace engineering investigations today are **fragmented, manual, unreproducible, and locked inside individual engineers' heads.**

A typical aerodynamic investigation requires an engineer to:
1. Formulate the question and operating conditions
2. Select an appropriate analysis method (analytical, panel method, RANS CFD, experiment)
3. Set up the tool (mesh, boundary conditions, solver settings)
4. Run the computation (minutes to days)
5. Parse and verify results (convergence, residuals, physical sanity)
6. Compare against reference data or competing methods
7. Diagnose failures when simulations diverge
8. Iterate with modified parameters
9. Reconcile conflicting evidence from different fidelity levels
10. Document assumptions, limitations, and provenance

This process typically takes **hours to weeks** per investigation. Results are often undocumented, unreproducible, and lost when engineers leave.

**AASI automates the scientific investigation workflow**, not just individual steps.

---

## 2. Who benefits?

| Role | Benefit |
|---|---|
| **Aerodynamics engineer** | Faster time-to-answer, automated verification, reproducible investigations |
| **R&D team lead** | Searchable scientific memory, knowledge preservation, team-wide evidence reuse |
| **UAV/eVTOL startup** | Rapid design-space exploration without dedicated CFD staff |
| **University researcher** | Structured experiment planning, provenance for publications |
| **Engineering consultant** | Professional investigation reports, multi-tool orchestration |
| **Simulation engineer** | Automated failure diagnosis, repair staging, compute routing |

---

## 3. Who pays?

**Primary buyers (first 12 months):**
- Engineering team leads at UAV/drone/eVTOL startups (5-50 engineers)
- University PI / research group leads with computational budgets
- Aerospace consultancies needing reproducible investigation reports
- Space startups doing preliminary aerodynamic/propulsion analysis

**Secondary buyers (12-36 months):**
- Mid-size aerospace R&D organizations
- Defense engineering contractors (with private deployment)

---

## 4. What is the painful problem?

> **Engineering investigations are not reproducible, searchable, or verifiable — and setting up CFD simulations correctly requires deep specialist knowledge that most teams cannot hire enough of.**

Specific pains:
- CFD setup is error-prone; 30-50% of initial runs diverge or produce unphysical results
- No institutional memory of past investigations
- Conflicting results from different tools with no systematic reconciliation
- Junior engineers waste senior engineer time asking for method guidance
- No audit trail connecting decisions to evidence
- Design reviews rely on PowerPoint screenshots, not traceable evidence chains

---

## 5. What currently takes engineers hours/days/weeks that AASI can reduce?

| Task | Current Time | AASI Approach | Estimated Reduction |
|---|---|---|---|
| Formulating CFD case setup | 2-4 hours | Automated from natural language + world model | TO BE VALIDATED |
| Running parametric sweeps | 1-5 days | Staged experiment planning with active selection | TO BE VALIDATED |
| Diagnosing diverged simulation | 2-8 hours | Automated 10-point diagnostic + repair staging | TO BE VALIDATED |
| Finding relevant prior work | 1-3 hours | Scientific memory retrieval by conditions | TO BE VALIDATED |
| Multi-fidelity evidence reconciliation | 4-16 hours | Automated discrepancy analysis with epistemic tiers | TO BE VALIDATED |
| Writing investigation report | 2-8 hours | Automated structured report with provenance | TO BE VALIDATED |

---

## 6. What can AASI do that generic LLMs cannot reliably do?

| Capability | Generic LLM | AASI |
|---|---|---|
| Generate valid CFD case files | Unreliable | Deterministic mesh + boundary condition generation |
| Verify simulation convergence | Cannot | 10-point audit with residual parsing |
| Distinguish hypothesis from evidence | Conflates | 9 epistemic tiers, strict separation |
| Track provenance of every claim | No | SHA-256 hashed evidence chain |
| Diagnose specific CFD failure modes | Guesses | Structured diagnostic engine with repair staging |
| Remember previous investigations | No persistence | Scientific memory with multi-dimensional retrieval |
| Plan next experiment | Random suggestions | Information-gain maximizing experiment selection |
| Reconcile conflicting evidence | Averages/ignores | Physics-aware discrepancy engine with root cause |

---

## 7. What can AASI do that conventional simulation software cannot?

| Capability | Conventional CAE | AASI |
|---|---|---|
| Scientific reasoning about *why* | No | Hypothesis-driven investigation |
| Autonomous method selection | No | Multi-fidelity decision engine |
| Cross-tool evidence reconciliation | No | Multi-source evidence framework |
| Natural-language problem intake | No | NL query normalization |
| Institutional scientific memory | No | Persistent verified result corpus |
| Automated failure diagnosis | Limited | Comprehensive diagnostic engine |
| Investigation-level orchestration | No | 16-step cognitive loop |

---

## 8. What can AASI do that engineering copilots cannot?

| Capability | Engineering Copilot | AASI |
|---|---|---|
| Full investigation lifecycle | Code completion only | Question → Verified Evidence |
| Scientific state machine | No | 17-state FSM with valid transitions |
| Competing hypotheses | No | Falsifiable hypothesis generation |
| Multi-cycle reasoning | Single-turn | Autonomous multi-cycle investigation |
| Tool execution + verification | Suggests code | Executes, verifies, reconciles |
| Scientific provenance | No | Content-addressed evidence chain |

---

## 9. What is the strongest current product wedge?

**CFD Investigation Automation for aerodynamic analysis.**

Rationale:
- OpenFOAM case generation, execution, and verification are already implemented
- The cognitive loop has been validated on real aerodynamic investigations
- NACA 0012 and other benchmark profiles are included
- Failure diagnosis and repair staging are working
- The BYOC compute model (Colab, user HPC) protects margins
- Aerodynamics has the deepest implementation in the current codebase

---

## 10. What should NOT be marketed yet?

| Capability | Reason |
|---|---|
| "Fully autonomous aerospace engineer" | Over-promise; current autonomy is Level 3-4 |
| "Certification-ready" | No regulatory body has reviewed AASI |
| "Real-time flight simulation" | AASI does investigation, not real-time sim |
| "Enterprise-scale deployment" | Single-node architecture today |
| "Defense-grade security" | Needs formal security audit |
| "Multi-physics" | Currently focused on aerodynamics |
| "3D complex geometry" | Primary strength is 2D airfoil analysis |

---

## Concrete Product Definition

> **AASI is an autonomous scientific investigation platform for aerospace engineering. It takes an engineering question, constructs a structured investigation with competing hypotheses, selects and executes appropriate computational tools (panel methods, RANS CFD, analytical models), verifies results against physical constraints, reconciles conflicting evidence across fidelity levels, and produces traceable, reproducible engineering reports — while maintaining a persistent scientific memory that learns from every investigation.**
>
> **AASI does not replace engineering tools. AASI gives the engineering toolchain a scientific brain.**
