# AASI Repository Inventory — Phase 0 Forensic Audit

> **Audit Date:** 2026-09-25
> **Auditor:** Commercial Readiness Audit Engine
> **Repository:** AASI — Autonomous Aerospace Scientific Intelligence
> **Commit Baseline:** Pre-commercial audit

---

## Executive Summary

AASI is a substantial aerospace scientific intelligence platform with **~200+ Python source files**, **84 automated tests**, **16 React/TypeScript frontend components**, and **99 documentation files** spanning 29 development phases. The codebase contains genuine scientific infrastructure — not a prototype or wrapper.

**Key Finding:** The repository contains a real, working scientific investigation engine with differentiated capabilities (hypothesis generation, multi-fidelity evidence reconciliation, verification, provenance, cognitive state machine, compute routing, tool ecosystem). However, it is organized as an evolving research project, not a commercial product. The `main.py` monolith is 3,022 lines. The architecture is ready for product extraction but requires packaging, isolation, and hardening.

---

## Architecture Overview

```
AASI/
├── backend/                    # Python FastAPI application (core)
│   ├── main.py                 # 3,022-line monolith — API + logic combined
│   ├── agent/                  # Investigation orchestration, planning, diagnostics, repair
│   ├── api/                    # Modular API routers (19 route files)
│   ├── auth/                   # Authentication, authorization, governance
│   ├── cfd/                    # OpenFOAM case generation, mesh, XFOIL adapter
│   ├── cognitive/              # Cognitive engine: world model, hypotheses, tools, critic
│   ├── compliance/             # NASA-STD-7009B dossier generator
│   ├── compute/                # Compute router, Colab, HPC, queue, providers
│   ├── dataset/                # Dataset ingestion, versioning, validation
│   ├── datasets/               # Dataset acquisition, audit, parsers
│   ├── deployment/             # Deployment config, Dockerfile
│   ├── export/                 # AeroDB export (DATCOM, SHABP, CSV)
│   ├── graph/                  # Knowledge graph service
│   ├── knowledge/              # RAG, embeddings, vector store, seed corpus
│   ├── llm/                    # LLM provider abstraction
│   ├── multifidelity/          # Multi-fidelity resolution, discrepancy, fusion
│   ├── observability/          # Metrics, events, logging
│   ├── physics/                # Physics models: airfoil parser, panel solver, orbit, rocket
│   ├── physics_ai/             # ML surrogates, active learning, training campaigns
│   ├── research/               # Research service, evidence ledger, experiment registry
│   ├── science/                # Core science engine: evidence, memory, verification, hypotheses
│   ├── simulation/             # Simulation executor, sandbox, quality control
│   ├── sources/                # External data connectors (NASA, ESA, ISRO, arXiv, SpaceX)
│   ├── storage/                # Content-addressed object store
│   ├── tools/                  # Tool registry (orbital, rocket, math)
│   ├── training/               # LLM training dataset generation
│   └── validation/             # Grid convergence, ASME V&V 20
├── frontend/                   # Next.js 14 TypeScript application
│   ├── app/                    # App router (page.tsx, layout.tsx, globals.css)
│   └── components/             # 16 React components
├── runner/                     # Local CFD runner agent with sandboxing
├── tests/                      # 84 test files + benchmarks
├── data/                       # Persistent data: airfoils, auth, memory, experiments
├── docs/                       # 99 technical documents + phase reports
├── scripts/                    # Browser acceptance test
├── training/                   # PhysicsNemo integration stubs
└── AASI_MVP_Master_Plan/       # Original architecture plans
```

---

## Subsystem Inventory

### 1. Cognitive Engine (`backend/cognitive/`)

| Component | File | Size | Purpose | Maturity | Customer Value | Action |
|---|---|---|---|---|---|---|
| Orchestrator | `orchestrator.py` | 20.7 KB | 16-step investigation loop with autonomy levels | **HIGH** | **CRITICAL** | **KEEP** |
| State Machine | `states.py` | 6.2 KB | 17-state FSM with valid transition matrix | **HIGH** | **HIGH** | **KEEP** |
| World Model | `world_model.py` | 9.4 KB | Structured aerospace world state with provenance | **HIGH** | **HIGH** | **KEEP** |
| Hypothesis Engine | `hypothesis_engine.py` | 12.4 KB | Competing falsifiable hypothesis generation | **HIGH** | **CRITICAL** | **KEEP** |
| Scientific Critic | `critic.py` | 6.8 KB | Multi-perspective hypothesis critique | **MEDIUM** | **HIGH** | **IMPROVE** |
| Experiment Planner | `planner.py` | 9.3 KB | Candidate experiment generation with cost/risk | **HIGH** | **CRITICAL** | **KEEP** |
| Scientific Tools | `tools.py` | 18.7 KB | MCP-compatible tool registry with execution modes | **HIGH** | **HIGH** | **KEEP** |
| Memory | `memory.py` | 10.8 KB | Cognitive investigation memory | **MEDIUM** | **HIGH** | **IMPROVE** |
| Contradiction | `contradiction.py` | 8.0 KB | Multi-source contradiction detection | **HIGH** | **CRITICAL** | **KEEP** |
| Model Zoo | `model_zoo.py` | 83.7 KB | ML model lifecycle management | **MEDIUM** | **MEDIUM** | **DEFER** |

**Classification:** KEEP — this is the crown jewel of the product.

### 2. Science Engine (`backend/science/`)

| Component | File | Size | Purpose | Maturity | Customer Value | Action |
|---|---|---|---|---|---|---|
| Evidence Engine | `evidence.py` | 22.6 KB | 9-tier epistemic evidence with provenance | **HIGH** | **CRITICAL** | **KEEP** |
| Scientific Memory | `memory.py` | 20.2 KB | Persistent verified results, failure corpus | **HIGH** | **CRITICAL** | **KEEP** |
| Verification | `verification.py` | 14.4 KB | 10-point CFD audit, anti-fabrication | **HIGH** | **CRITICAL** | **KEEP** |
| Hypotheses | `hypotheses.py` | 20.3 KB | Science-level hypothesis management | **HIGH** | **HIGH** | **KEEP** |
| Experiment Planner | `planner.py` | 20.4 KB | Multi-fidelity experiment planning | **HIGH** | **HIGH** | **KEEP** |
| Empirical Ledger | `empirical_ledger.py` | 7.2 KB | Immutable evidence ledger | **HIGH** | **CRITICAL** | **KEEP** |
| Closed Loop | `closed_loop.py` | 22.3 KB | Autonomous investigation loop | **HIGH** | **HIGH** | **KEEP** |

**Classification:** KEEP — second most important subsystem.

### 3. Agent / Orchestration (`backend/agent/`)

| Component | File | Size | Purpose | Maturity | Customer Value | Action |
|---|---|---|---|---|---|---|
| Production Orchestrator | `orchestrator.py` | 9.2 KB | Session management, state transitions | **HIGH** | **HIGH** | **KEEP** |
| Scientific Answer Engine | `scientific_answer.py` | 17.5 KB | Structured epistemic explanations | **HIGH** | **CRITICAL** | **KEEP** |
| Investigation Graph | `investigation_graph.py` | 16.7 KB | Inquiry DAG, discovery engine | **HIGH** | **HIGH** | **KEEP** |
| Diagnostics | `diagnostics.py` | 15.5 KB | CFD failure classification | **HIGH** | **HIGH** | **KEEP** |
| Repair Engine | `repair_engine.py` | 7.9 KB | Automated CFD repair staging | **HIGH** | **HIGH** | **KEEP** |
| Report Generator | `report_generator.py` | 7.7 KB | Scientific report compilation | **MEDIUM** | **HIGH** | **IMPROVE** |
| Legacy Agent | `agent_legacy.py` | 40.8 KB | Original Ollama-based chat agent | **LOW** | **LOW** | **REFACTOR** |

### 4. Compute Infrastructure (`backend/compute/`)

| Component | File | Size | Purpose | Maturity | Customer Value | Action |
|---|---|---|---|---|---|---|
| Compute Router | `router.py` | 11.7 KB | Deterministic routing: LOCAL/COLAB/HPC | **HIGH** | **CRITICAL** | **KEEP** |
| Colab Provider | `colab.py` | 43.0 KB | Google Colab notebook generation | **HIGH** | **HIGH** | **KEEP** |
| Job Queue | `queue.py` | 13.9 KB | Persistent job lifecycle management | **HIGH** | **HIGH** | **KEEP** |
| User Provided | `user_provided.py` | 21.7 KB | BYOC (bring your own compute) | **HIGH** | **CRITICAL** | **KEEP** |

**Classification:** KEEP — essential for BYOC compute economics.

### 5. Authentication & Authorization (`backend/auth/`)

| Component | File | Purpose | Maturity | Action |
|---|---|---|---|---|
| Security Manager | `security.py` | PBKDF2 hashing, HMAC session tokens | **HIGH** | **IMPROVE** |
| Governance Engine | `governance.py` | Quotas, rate limiting, job ownership | **HIGH** | **KEEP** |
| Auth Models | `models.py` | User, Role, Session models | **HIGH** | **IMPROVE** |

**Security Finding:** Default password `aerospace-secure-password-2026` created for dev. Default secret key hardcoded. Both need production hardening.

---

## Critical Findings

### Security Issues

| Severity | Finding | Location | Action |
|---|---|---|---|
| **HIGH** | Default password hardcoded | `auth/security.py:64` | FIX: Only create in dev mode |
| **HIGH** | Default secret key in code | `deployment/config.py:21` | FIX: Require env var in prod |
| **MEDIUM** | CORS wildcard `*` default | `deployment/config.py:46` | FIX: Restrict in production |
| **LOW** | No subprocess calls found | N/A | Good — no shell injection risk |

### Architectural Issues

| Severity | Finding | Location | Action |
|---|---|---|---|
| **HIGH** | `main.py` is 3,022-line monolith | `backend/main.py` | REFACTOR: Extract remaining endpoints |
| **MEDIUM** | No Organization/Team model | `auth/models.py` | ADD: Organization, Project |
| **MEDIUM** | No billing/subscription abstraction | N/A | ADD: Plan, Entitlement, UsageEvent |

### Demo/Mock Code — Properly Quarantined

| Finding | Location | Risk |
|---|---|---|
| `DEMO_DATA` epistemic tier explicitly labeled | `science/models.py` | LOW |
| `DEMONSTRATION` evidence tier explicitly marked | `research/evidence_ledger.py` | LOW |
| `sha256-weights-placeholder` in surrogates | `science/surrogates.py` | MEDIUM |

**Key positive finding:** The codebase aggressively guards against fabrication. Stage 10 governance, anti-fabrication rules, and explicit epistemic tier separation are deeply embedded.

---

## Subsystem Classification Summary

| Classification | Subsystems |
|---|---|
| **KEEP** | Cognitive Engine, Science Engine, Agent Orchestration, Compute Router, CFD Infrastructure, Evidence System, Verification, Memory, Knowledge/RAG, Multi-fidelity, Physics Tools, Tests |
| **IMPROVE** | Auth (add Org/Team), Frontend UX, Observability, Report Generator, main.py extraction, Security hardening |
| **REFACTOR** | Legacy Agent, `main.py` monolith, duplicate dataset directories |
| **REPLACE** | None |
| **REMOVE** | None |
| **DEFER** | Model Zoo (83KB), PhysicsNemo training stubs, full enterprise SSO |
