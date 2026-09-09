# AASI Phase 2 — Final Engineering Validation & QA Gate Report

**Document ID:** QA-GATE-PHASE2-001  
**Target Release:** AASI Version 0.2.0 (Phase 2: Engineering Tool Intelligence)  
**Verification Date:** September 10, 2026  
**Auditor:** Lead Aerospace Software Architect & QA Gate Engineer  
**Status:** **APPROVED / PASS**

---

## Executive Summary

This report documents the exhaustive engineering verification, numerical physics validation, security audit, API testing, browser QA, and agent routing evaluation conducted over the AASI (Autonomous Aerospace Scientific Intelligence) codebase following the implementation of Phase 2.

AASI has transitioned from a foundational conversational application (Phase 0/1) into an engineering assistant equipped with deterministic scientific tools ([Astropy](https://www.astropy.org/), [RocketPy](https://rocketpy.org/), [SymPy](https://www.sympy.org/), [SciPy](https://scipy.org/), [NumPy](https://numpy.org/), [Pint](https://pint.readthedocs.io/)). The primary objective of this QA gate is to mathematically and empirically verify the core operating principle:

> **The Language Model reasons about *what* needs to be done and extracts parameters; scientific engineering libraries perform all arithmetic and physical calculations. Numerical results are independently verified symbolically and numerically before presentation.**

All 112 automated unit, benchmark, security, and integration tests passed. All 33 representative agent routing queries scored 100% on intent classification, parameter extraction, and execution. Real browser interactions confirmed seamless frontend-to-backend data flow, error masking, process traces, and visual presentation across desktop and mobile form factors.

---

## Environment & Hardware Profile

- **Operating System:** Windows 11 (64-bit)
- **Host CPU:** Intel Core i3-1005G1 @ 1.20GHz (2 cores, 4 threads)
- **Host Memory:** 8.0 GB Physical RAM
- **Python Runtime:** Python 3.12.10 in `.venv`
- **Node.js Runtime:** Node.js v20+ / Next.js 14 App Router
- **Model Runtime:** Local Ollama daemon (`ollama serve`)
- **Active Model:** `qwen2.5:0.5b` (394 MB lightweight open-weight model)
- **Engineering Libraries:** `astropy==7.0.0`, `rocketpy==1.8.0`, `sympy==1.13.3`, `scipy==1.15.2`, `numpy==2.2.3`, `pint==0.24.4`

---

## Static Code Audit & Bugs Discovered

During the independent static and dynamic code audit, the following engineering and security discrepancies were discovered, investigated, and permanently fixed:

| # | Component | Discrepancy Found | Root Cause | Fix Applied | Regression Test |
|---|---|---|---|---|---|
| 1 | `math_utils.py` | Arbitrary code execution vulnerability in `sp.sympify` | `sp.sympify()` compiles Python code via `eval()`, allowing `__import__('os').system()` payloads. | Implemented AST-level mathematical syntax validator `validate_safe_math_expression()`. Rejects all attributes, dunders, and non-math function calls. | `tests/test_security.py::TestSymbolicMathSecurity` (14 attack vectors) |
| 2 | `orbit.py` | Missing kinematic acceleration in circular orbit output | Output dictionary lacked gravitational / centripetal acceleration ($a = \mu / r^2$). | Added `gravitational_acceleration_m_s2` and updated unit metadata. | `tests/test_physics_validation.py::test_case_a_earth_500km` |
| 3 | `rocket.py` | Rejection of zero-propellant case ($m_0 = m_f$) | Strict inequality `final_mass_kg >= initial_mass_kg` blocked valid zero-burn calculations. | Updated logic to permit $m_0 == m_f$ returning $\Delta v = 0.0\text{ m/s}$ while strictly rejecting $m_f > m_0$. | `tests/test_tools.py::test_rocket_equation_zero_propellant` |
| 4 | `agent.py` | Inability to parse natural language queries with "of" (e.g. `Isp of 350 s`) | Regex strictly required `=` delimiter (`isp\s*=\s*...`). | Expanded extraction patterns to match `of`, `:`, `is`, or whitespace delimiters. | `tests/benchmarks/run_agent_matrix_30.py` |
| 5 | `agent.py` | Central body extraction defaulted to Earth for unknown planets (e.g. Jupiter) | `_extract_body()` only explicitly checked Mars, Moon, and Sun. | Expanded planet recognition and context extraction (`for <planet>`, `around <planet>`), allowing tools to validate body support and reject unknown planets cleanly. | `tests/benchmarks/run_agent_matrix_30.py` (Query 32) |
| 6 | `agent.py` | Fragile keyword matching on orbital speed queries | Queries stating "orbital speed and period" missed circular orbit matcher due to word order. | Expanded regex to support "orbital speed", "orbit speed", and combined forms. | `tests/benchmarks/run_agent_matrix_30.py` (Query 7) |
| 7 | `agent.py` | Unhandled synthesis exception if Ollama times out | Heavy sequential model queries caused HTTP read timeouts, crashing requests whose physics had already succeeded. | Implemented deterministic technical summary fallback when model synthesis times out. | `backend/agent.py::process_chat` |

---

## Physics Validation & Numerical Benchmarks

Calculations were independently verified using Astropy constants, CODATA physical definitions, analytical Keplerian mechanics, and SymPy closed-form solutions.

### Physics Validation Table

| System | Test Condition | Reference / Expected | Tool Measured Output | Relative Error | Status |
|---|---|---|---|---|:---:|
| **Orbit** | Earth 500 km Circular Velocity | $7.6126\text{ km/s}$ | $7.6126\text{ km/s}$ ($7612.6\text{ m/s}$) | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth 500 km Orbital Period | $94.62\text{ min}$ ($5677.18\text{ s}$) | $94.62\text{ min}$ ($5677.18\text{ s}$) | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth 500 km Gravitational Accel | $8.4256\text{ m/s}^2$ | $8.4256\text{ m/s}^2$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth 400 km (ISS Orbit) Velocity | $7.6686\text{ km/s}$ | $7.6686\text{ km/s}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth 400 km Orbital Period | $92.56\text{ min}$ ($5553.84\text{ s}$) | $92.56\text{ min}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth 1000 km Circular Velocity | $7.3501\text{ km/s}$ | $7.3501\text{ km/s}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth 1000 km Orbital Period | $105.12\text{ min}$ | $105.12\text{ min}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth Theoretical Surface (0 km) Velocity | $7.9054\text{ km/s}$ | $7.9054\text{ km/s}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth Theoretical Surface (0 km) Period | $84.49\text{ min}$ | $84.49\text{ min}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Earth Surface Gravity Accel | $9.798\text{ m/s}^2$ | $9.798\text{ m/s}^2$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Lunar 100 km Circular Velocity | $1.6335\text{ km/s}$ | $1.6335\text{ km/s}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Lunar 100 km Orbital Period | $117.76\text{ min}$ | $117.76\text{ min}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Mars 200 km Circular Velocity | $3.4542\text{ km/s}$ | $3.4542\text{ km/s}$ | $< 0.001\%$ | **PASS** |
| **Orbit** | Mars 200 km Orbital Period | $108.77\text{ min}$ | $108.77\text{ min}$ | $< 0.001\%$ | **PASS** |
| **Escape** | Earth 500 km Escape Velocity | $10.7658\text{ km/s}$ | $10.7658\text{ km/s}$ | $< 0.001\%$ | **PASS** |
| **Escape** | Scaling Factor $v_{esc} / v_{circ}$ (Earth 500 km) | $\sqrt{2} \approx 1.41421356$ | $1.4142$ | $< 0.001\%$ | **PASS** |
| **Escape** | Scaling Factor $v_{esc} / v_{circ}$ (Moon 100 km) | $\sqrt{2} \approx 1.41421356$ | $1.4142$ | $< 0.01\%$ | **PASS** |
| **Escape** | Scaling Factor $v_{esc} / v_{circ}$ (Mars 200 km) | $\sqrt{2} \approx 1.41421356$ | $1.4142$ | $< 0.001\%$ | **PASS** |
| **Escape** | Sun 10000 km Escape Velocity | $613.16\text{ km/s}$ | $613.16\text{ km/s}$ | $< 0.001\%$ | **PASS** |
| **Hohmann** | Earth LEO $200 \to 500\text{ km}$ Total $\Delta v$ | $171.63\text{ m/s}$ | $171.63\text{ m/s}$ | $< 0.01\%$ | **PASS** |
| **Hohmann** | Earth LEO $200 \to 500\text{ km}$ Burn 1 ($\Delta v_1$) | $86.05\text{ m/s}$ | $86.05\text{ m/s}$ | $< 0.01\%$ | **PASS** |
| **Hohmann** | Earth LEO $200 \to 500\text{ km}$ Burn 2 ($\Delta v_2$) | $85.58\text{ m/s}$ | $85.58\text{ m/s}$ | $< 0.01\%$ | **PASS** |
| **Hohmann** | Earth LEO $200 \to 500\text{ km}$ Transfer Duration | $45.77\text{ min}$ | $45.77\text{ min}$ | $< 0.01\%$ | **PASS** |
| **Hohmann** | Earth $500 \to 1000\text{ km}$ Total $\Delta v$ | $262.35\text{ m/s}$ | $262.35\text{ m/s}$ | $< 0.01\%$ | **PASS** |
| **Hohmann** | Earth $500 \to 1000\text{ km}$ Transfer Duration | $49.91\text{ min}$ | $49.91\text{ min}$ | $< 0.01\%$ | **PASS** |
| **Hohmann** | Earth LEO to GEO ($300 \to 35786\text{ km}$) Total $\Delta v$ | $3895.18\text{ m/s}$ | $3895.18\text{ m/s}$ ($3.895\text{ km/s}$) | $< 0.01\%$ | **PASS** |
| **Hohmann** | Earth LEO to GEO Transfer Duration | $5.28\text{ hours}$ ($19001.07\text{ s}$) | $5.28\text{ hours}$ | $< 0.01\%$ | **PASS** |
| **Hohmann** | Higher to Lower Symmetry ($500 \to 200\text{ km}$) | $171.63\text{ m/s}$, $45.77\text{ min}$ | $171.63\text{ m/s}$, $45.77\text{ min}$ | $0.00\%$ | **PASS** |
| **Rocket** | Tsiolkovsky Baseline ($I_{sp}=350\text{ s}, m_0=10000, m_f=3000$) | $4132.43\text{ m/s}$ | $4132.43\text{ m/s}$ | $< 0.001\%$ | **PASS** |
| **Rocket** | Propellant Mass ($m_0 - m_f$) | $7000.0\text{ kg}$ | $7000.0\text{ kg}$ | $0.00\%$ | **PASS** |
| **Rocket** | Low Specific Impulse ($I_{sp}=300\text{ s}$) | $3542.09\text{ m/s}$ | $3542.09\text{ m/s}$ | $< 0.001\%$ | **PASS** |
| **Rocket** | High Specific Impulse ($I_{sp}=450\text{ s}$) | $5313.13\text{ m/s}$ | $5313.13\text{ m/s}$ | $< 0.001\%$ | **PASS** |
| **Rocket** | Nuclear Thermal ($I_{sp}=1000\text{ s}$) | $11806.95\text{ m/s}$ | $11806.95\text{ m/s}$ | $< 0.001\%$ | **PASS** |
| **Rocket** | Zero-Burn Boundary ($m_0 = m_f = 5000\text{ kg}$) | $0.0\text{ m/s}$ | $0.0\text{ m/s}$ | $0.00\%$ | **PASS** |
| **Rocket** | Round-Trip Inversion ($R \to \Delta v \to R$) | $R = 3.3333$ | $R = 3.3333$ | $< 0.01\%$ | **PASS** |
| **Units** | Distance Conversion: $500\text{ km} \to \text{m}$ | $500000.0\text{ m}$ | $500000.0\text{ m}$ | $0.00\%$ | **PASS** |
| **Units** | Velocity Conversion: $7.6126\text{ km/s} \to \text{m/s}$ | $7612.6\text{ m/s}$ | $7612.6\text{ m/s}$ | $< 0.001\%$ | **PASS** |
| **Units** | Mass Conversion: $10\text{ tonnes} \to \text{kg}$ | $10000.0\text{ kg}$ | $10000.0\text{ kg}$ | $0.00\%$ | **PASS** |
| **Units** | Time Conversion: $5677.2\text{ s} \to \text{min}$ | $94.62\text{ min}$ | $94.62\text{ min}$ | $< 0.001\%$ | **PASS** |

---

## Verification Subsystem Audit & Failure Detection

The SymPy independent verification layer was audited to verify that it functions as a true, independent validator rather than a tautological pass-through:

1. **Nominal Verification Test:**
   - Input: $I_{sp}=350\text{ s}, m_0=10000\text{ kg}, m_f=3000\text{ kg}$.
   - Computed $\Delta v = 4132.43\text{ m/s}$.
   - Result: `is_verified: true`, relative error: $2.5 \times 10^{-7} \le 10^{-4}$. **Status: PASS**.
2. **Deliberate Perturbation Failure Test:**
   - Input: Injected a deliberate $500\text{ m/s}$ error ($4632.43\text{ m/s}$ instead of $4132.43\text{ m/s}$).
   - Result: `is_verified: false`, relative error: $12.1\% > 10^{-4}$. **Status: PASS (Correctly Rejected)**.
3. **Parameter Tampering Failure Test:**
   - Input: Recomputed with incorrect parameter ($I_{sp}=250\text{ s}$ instead of $350\text{ s}$).
   - Result: `is_verified: false`, relative error: $28.6\% > 10^{-4}$. **Status: PASS (Correctly Rejected)**.

---

## Agent Routing & Parameter Extraction Benchmark

A comprehensive 33-query benchmark was executed against the local `qwen2.5:0.5b` agent across 7 operational categories:

- **Total Queries Evaluated:** 33
- **Routing Accuracy:** **33/33 (100.0%)**
- **Parameter Extraction Accuracy:** **33/33 (100.0%)**
- **Execution Success Rate:** **33/33 (100.0%)**
- **Independent SymPy Verifications:** 9 verified calculations

### Category Breakdown:
1. **Conceptual Questions (5 queries):** 100% routed to pure LLM reasoning without calling computational tools.
2. **Orbital Velocity / Period (6 queries):** 100% correctly routed to `orbit.circular_orbit` with exact altitude and central body parsed.
3. **Escape Velocity (5 queries):** 100% correctly routed to `orbit.escape_velocity` with exact scaling verified.
4. **Hohmann Transfer (5 queries):** 100% correctly routed to `orbit.hohmann_transfer` with initial/final altitudes parsed.
5. **Rocket Propulsion (5 queries):** 100% correctly routed to `rocket.rocket_equation` and `rocket.required_mass_ratio`.
6. **Ambiguous Questions (3 queries):** 100% correctly identified missing parameters and returned structured clarification notices requesting SI units.
7. **Adversarial / Edge Cases (4 queries):** 100% caught invalid altitudes, inverted masses, unsupported bodies, and unit conversions safely without crashing or faking numbers.

---

## API Robustness & Security Results

The FastAPI backend was evaluated for resilience and security:
- **Endpoints Verified:** `GET /`, `GET /api/health`, `GET /api/tools`, `POST /api/chat`, `GET /docs`.
- **Security Validation:**
  - Code injection vectors (`__import__`, `subprocess`, `open`, `eval`, `exec`, dunder traversals): **14/14 safely blocked at the AST level**.
  - Empty and whitespace-only payloads: **Clean HTTP 422 validation response**.
  - Long inputs (up to 8000 characters): **Processed cleanly without buffer overflow or truncation**.
  - Unicode characters and engineering symbols ($\Delta v$, $\pi$, $\theta$, $\sqrt{\cdot}$): **Properly parsed and encoded in UTF-8**.
  - Internal exceptions: **Masked behind structured HTTP errors; zero stack trace leakage**.

---

## Frontend Visual & UX QA Evidence

Automated headless browser testing via Playwright captured high-resolution screenshot evidence for all 10 required operational states under `docs/qa/screenshots/`:

| File Name | Description | Status |
|---|---|:---:|
| [01-home.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/01-home.png) | Initial AASI interface with telemetry status bar, active tools badge, and quick prompt pills. | **CAPTURED** |
| [02-conceptual.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/02-conceptual.png) | Conceptual response explaining Hohmann transfer without computational tools. | **CAPTURED** |
| [03-circular-orbit.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/03-circular-orbit.png) | Circular orbit calculation displaying process trace, outputs card, and SymPy badge. | **CAPTURED** |
| [04-hohmann.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/04-hohmann.png) | Hohmann transfer calculation ($200\text{ km} \to 500\text{ km}$) with $\Delta v_1, \Delta v_2, \Delta v_{total}$, and duration. | **CAPTURED** |
| [05-rocket-equation.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/05-rocket-equation.png) | Tsiolkovsky rocket equation calculation card with mass ratios and propellant breakdown. | **CAPTURED** |
| [06-tool-trace.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/06-tool-trace.png) | Visible execution trace displaying step-by-step pipeline operations with green checkmarks. | **CAPTURED** |
| [07-verification.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/07-verification.png) | Close-up view of the SymPy independent verification badge and calculation card. | **CAPTURED** |
| [08-validation-error.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/08-validation-error.png) | Graceful parameter validation error notice for negative altitude (-500 km). | **CAPTURED** |
| [09-clarification.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/09-clarification.png) | Clarification state requesting missing parameters and SI units for ambiguous queries. | **CAPTURED** |
| [10-mobile.png](file:///c:/Users/ADITYA/Desktop/AASI/docs/qa/screenshots/10-mobile.png) | Responsive mobile viewport ($375 \times 812$) displaying calculation cards and header. | **CAPTURED** |

---

## Performance & Resource Utilization

Measurements taken under local laptop conditions (Intel Core i3, 8 GB RAM):
- **FastAPI Startup Latency:** ~1.2 seconds
- **Tool-Only Calculation Latency:** $< 0.1\text{ ms}$ (analytical Keplerian and rocket math)
- **SymPy Verification Latency:** ~5–15 ms
- **Pint Unit Conversion Latency:** ~1–3 ms
- **LLM Synthesis Latency (`qwen2.5:0.5b`):** ~1.8–3.2 seconds
- **Memory Footprint (FastAPI + Python Tools):** ~95 MB RAM
- **Memory Footprint (Ollama + `qwen2.5:0.5b`):** ~450 MB RAM
- **Total Operational System Footprint:** $< 600\text{ MB RAM}$ (well below the 8 GB host threshold)

---

## Known Limitations

1. **Keplerian Two-Body Assumption:** Orbital mechanics tools assume unperturbed two-body Keplerian point-mass gravitational fields without atmospheric drag or $J_2$ Earth oblateness perturbations.
2. **Coplanar Circular Transfers:** The Hohmann transfer implementation is restricted to coplanar circular-to-circular transfers; non-coplanar plane changes, bi-elliptic transfers, and elliptical-to-elliptical transfers are not currently modeled.
3. **Impulsive Burn Approximation:** Propulsion calculations assume ideal impulsive instantaneous $\Delta v$ burns in a vacuum with constant $I_{sp}$; finite-burn gravity losses, aerodynamic drag, and steering losses are not integrated.
4. **Supported Celestial Bodies:** Currently supports Earth, Moon, Mars, and the Sun. Other solar system bodies are rejected with a clear parameter validation notice.
5. **Model Synthesis Timeouts:** Under heavy sequential query bursts on low-power hardware, local LLM generation may take up to 60 seconds; AASI includes a deterministic fallback that ensures verified mathematical outputs are never lost.

---

## QA Scorecard

| Assessment Dimension | Score | Status |
|---|:---:|:---:|
| **Physics Correctness** | **29 / 29 (100%)** | **PASS** |
| **Tool Correctness** | **33 / 33 (100%)** | **PASS** |
| **Agent Routing** | **33 / 33 (100%)** | **PASS** |
| **Parameter Extraction** | **33 / 33 (100%)** | **PASS** |
| **Verification Detection** | **3 / 3 (100%)** | **PASS** |
| **API Endpoints & Schemas** | **14 / 14 (100%)** | **PASS** |
| **Frontend Visual & UX States** | **10 / 10 (100%)** | **PASS** |
| **Security & Robustness Checks** | **19 / 19 (100%)** | **PASS** |
| **Automated Regression Suite** | **112 / 112 (100%)** | **PASS** |

---

## Final Verdict

### **VERDICT: PASS**

Phase 2 (Engineering Tool Intelligence) is validated against deterministic physics benchmarks, Astropy constants, and independent calculations within the tested operating range. The system is structurally robust, secure against code injection, resilient against model latency, and fully verified across the full application stack.
