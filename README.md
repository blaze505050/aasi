# AASI — Autonomous Aerospace Scientific Intelligence

> **Deterministic Aerodynamic Database Generation, Automated ASME V&V 20 Verification Artifacts, Multi-Fidelity Investigation, & 30-Problem Aerospace Engineering Platform Roadmap**

[![Live Production](https://img.shields.io/badge/Live_Production-frontend--blush--eta--19.vercel.app-0070f3?style=for-the-badge&logo=vercel&logoColor=white)](https://frontend-blush-eta-19.vercel.app)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![ASME V&V 20-2009](https://img.shields.io/badge/Verification_Artifacts-ASME%20V%26V%2020--2009-brightgreen.svg)](https://www.asme.org/codes-standards/find-codes-standards/v-v-20-standard-verification-validation-computational-fluid-dynamics-heat-transfer)
[![NASA-STD-7009B Aligned](https://img.shields.io/badge/Evidence_Artifacts-NASA--STD-7009B%20Aligned-blue.svg)](https://standards.nasa.gov/standard/NASA/NASA-STD-7009B)
[![USAF DATCOM](https://img.shields.io/badge/Export-USAF%20DATCOM-red.svg)](#multi-standard-aerospace-exporters)
[![Tests](https://img.shields.io/badge/Tests-1015%20Passing-success.svg)](#automated-verification-test-suite)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🚀 **Live Production Platform & Digital Twin Studio:**  
> **[https://frontend-blush-eta-19.vercel.app](https://frontend-blush-eta-19.vercel.app)**

---

## Executive Summary

**AASI (Autonomous Aerospace Scientific Intelligence)** is an aerodynamic engineering, verification, and scientific evidence platform designed for UAV developers, aerodynamicists, eVTOL teams, and aerospace researchers. Optimized for **conceptual and preliminary design trade studies**, AASI transforms the traditionally fragmented, labor-intensive aerodynamic database workflow into an automated, verifiable pipeline.

The core thesis of AASI:
$$\text{AASI} = \text{Physics Kernel} + \text{Verification Layer} + \text{Autonomous Orchestrator}$$

**Every number comes with its proof.** Rather than producing unverified numbers, AASI outputs deterministic first-principles physics (discrete vortex panel methods, 3D vortex lattice methods, Karman-Tsien compressibility, Schlichting/Squire-Young boundary layer drag estimates) accompanied by formal 5-tier Guide to the Expression of Uncertainty in Measurement (GUM) uncertainty intervals and verification evidence artifacts aligned with the methodologies of **ASME V&V 20-2009** and **NASA-STD-7009B** CAS credibility guidelines.

```
                                  ┌─────────────────────────────────────────┐
                                  │      AASI MISSION CONTROL COCKPIT       │
                                  │     (Next.js 14 + Interactive Polars)   │
                                  └────────────────────┬────────────────────┘
                                                       │
                     ┌─────────────────────────────────┼─────────────────────────────────┐
                     ▼                                 ▼                                 ▼
       ┌───────────────────────────┐     ┌───────────────────────────┐     ┌───────────────────────────┐
       │   AERO DATABASE ENGINE    │     │   ASME V&V 20 VERIFIER    │     │  CFD & GEOMETRY INGESTION │
       │ ───────────────────────── │     │ ───────────────────────── │     │ ───────────────────────── │
       │ • Multi-Sweep (α, Re, M)  │     │ • Grid Convergence Index  │     │ • Selig, Lednicer, CSV    │
       │ • CL_alpha, CD0, L/D_max  │     │ • Observed Order (p)      │     │ • Auto-Normalizer & LE (0)│
       │ • CM_alpha, x_ac, Korn Mdd│     │ • Richardson Extrap (phi) │     │ • Conformal 6-Block C-Grid│
       │ • USAF DATCOM Export (.dat│     │ • NASA-STD-7009B Dossier  │     │ • Boundary Layer Grading  │
       │ • NASA S/HABP Export (.sh)│     │ • CAS Credibility Scoring │     │ • OpenFOAM blockMeshDict  │
       │ • 6-DOF Flight Sim (.csv) │     │ • SHA-256 Provenance Hash │     │ • <3ms Panel Solver       │
       └───────────────────────────┘     └───────────────────────────┘     └───────────────────────────┘
```

---

## 🌟 Flagship Feature: Aerospace Digital Twin Suite

AASI 2.0 features an industry-grade, deterministic **Aerospace Digital Twin Suite** with real-time interactive 3D WebGL (Three.js) airframe visualization, high-frequency telemetry cockpits, and non-nominal fault-injection stress testing across 4 vehicle classes:

1. 🚀 **Orbital Heavy-Lift Launch Vehicle (Rocket Digital Twin)**
   - Multi-stage ascent trajectory, Tsiolkovsky mass depletion, US Standard Atmosphere 1976 barometric profile.
   - Compressible transonic wave drag rise $C_D(M)$, dynamic pressure $q(t)$ tracking Max-Q, and Fay-Riddell aero-thermal heating.
   - Gravity turn pitch-over dynamics and Keplerian orbital insertion state ($a, e, v_{circ}$, perigee, apogee).
   - Fault injection: Premature engine cutoff, gimbal actuator freeze.

2. 🚁 **Hexacopter & Hybrid eVTOL (Drone Digital Twin)**
   - Blade Element Momentum Theory (BEMT) rotor inflow and power dissipation.
   - Cheeseman-Bennett In-Ground-Effect (IGE) correction for takeoff/landing.
   - Lithium-Ion Battery Equivalent Circuit Model (ECM) with nonlinear $V_{oc}(SoC)$ curve and internal resistance voltage sag under motor draw.
   - Brushless DC motor electro-thermal rise and Dryden atmospheric wind gust response.
   - Fault injection: Rotor motor failure (loss of 1 of 6 rotors), battery cell drop, gust surge.

3. ✈️ **Twin-Turbofan Commercial Air Transport (Aeroplane Digital Twin)**
   - 3D compressible drag polar with Korn drag divergence and induced drag factor.
   - High-bypass turbofan thrust lapse and Thrust Specific Fuel Consumption (TSFC).
   - Complete Breguet mission profile: Takeoff roll $\to$ rotation $\to$ 250 kt 10k climb $\to$ sustained Mach 0.78 cruise at FL360 $\to$ descent and landing.
   - $V\text{-}n$ structural maneuver envelope monitoring (+2.5g / -1.0g FAR Part 25) and One-Engine Inoperative (OEI) drift-down trim.
   - Fault injection: Engine flameout (OEI), pitot tube icing, stabilizer trim runaway.

4. 🛰️ **Sun-Synchronous LEO Observation Satellite (Satellite Digital Twin)**
   - Keplerian orbital propagation with Earth oblateness $J_2$ perturbations (calculating RAAN nodal precession $\dot{\Omega}$ and perigee rotation $\dot{\omega}$).
   - Harris-Priester / Jacchia thermospheric scale-height density model predicting semi-major axis drag decay $\frac{da}{dt}$ and orbital lifetime in years.
   - Cylindrical Earth shadow eclipse geometry (umbra entry/exit timestamps).
   - GaAs triple-junction solar array electrical generation and battery Depth-of-Discharge (DoD).
   - Stefan-Boltzmann 4th-power radiation equilibrium between solar, Earth albedo, Earth infrared, and internal dissipation.
   - Fault injection: Solar array string failure (-60%), reaction wheel saturation, geomagnetic drag surge.

### Flight Dynamics & Autopilot Bridges
- **JSBSim 6-DoF FDM Exporter (`<fdm_config>`)**: Ready-to-simulate flight dynamics deck with mass properties and stability derivatives ($C_{L\alpha}, C_{m\alpha}, C_{Y\beta}, C_{l\beta}, C_{n\beta}, C_{lp}, C_{mq}, C_{nr}$).
- **PX4 Autopilot Parameter & Mixer Exporter**: Direct `.params` and actuator `.mix` files for Pixhawk / QGroundControl integration.

---

## 30-Problem Aerospace Platform Architecture

AASI is designed as a modular 30-problem aerospace engineering platform across three progressive tiers:

### 1. The Plug-in Module Contract
Every physical problem module implements a strict four-part interface:
1. `solve(inputs, fidelity)` $\to$ deterministic calculation
2. `uncertainty(inputs)` $\to$ formal 95% confidence intervals (GUM / ASME V&V 20)
3. `benchmarks()` $\to$ published reference cases with literature data (NASA TM, AGARD, AIAA)
4. `evidence(results)` $\to$ immutable cryptographic SHA-256 provenance record

### 2. The Three-Level Fidelity Ladder
- **L0 (Analytic / Empirical):** Closed-form equations for millisecond trade space exploration (e.g. Thin Airfoil Theory, Diederich 3D Swept Wing).
- **L1 (Reduced-Order Physics):** Discrete vortex panel methods and 3D Vortex Lattice Methods (VLM) for seconds-scale preliminary design.
- **L2 (High-Fidelity CFD/FEA):** Automated mesh dispatch for OpenFOAM (`simpleFoam`) and SU2 Navier-Stokes solvers with wall-normal grading ($y^+ \sim 1$).

### 3. Tiered Roadmap & Priority Wedges
- **Tier 1 (Aerodynamics Core, Months 0-6):** 3D Wing VLM, Transonic Shock, Boundary Layer Transition ($e^N$), Stall Correction, Airfoil Inverse Design, Propeller/Rotor BEMT, Aeroelastic Flutter, 6-DOF Handling Qualities (MIL-STD-1797), Polynomial Chaos UQ, Autonomous CFD Agent.
- **Tier 2 (Vehicle Systems & Propulsion, Months 6-12):** Rocket Trajectory & Dispersion (RocketPy), Atmospheric Reentry Heating (Sutton-Graves / Fay-Riddell), Thermal Protection System Sizing, Cantera Rocket Engine Maps, Structural FEA (CalculiX/FEniCS), Fatigue Life (Paris Law), Composites (Tsai-Wu), Avionics Thermal, eVTOL Powertrain & Battery Sizing, Predictive Maintenance (NASA C-MAPSS).
- **Tier 3 (Astrodynamics & Space Operations, Months 12-18):** High-Fidelity Orbit Propagation (SGP4 + J2-J6), Conjunction Assessment, Interplanetary Trajectory Optimization (Lambert / GTOP), RPO Dynamics, ADCS (Quaternion EKF), Constellation Walker Patterns, Space Weather Drag, Deorbit Risk, Cislunar CR3BP / NRHO, Telemetry Anomaly Detection.

**Priority Go-to-Market Wedge (Wedge A):** eVTOL and UAV developers (Items 1, 3, 6, 8, 9, 19). Fast sales cycles, critical weight/power trade-offs, and immediate need for verifiable aerodynamic databases without large dedicated in-house CFD teams.

---

## Core Capabilities

### 1. Aerodynamic Database (Aero DB) Generation Engine with Formal UQ
- **Flight Envelope Sweeps:** Generates full tabular matrices of $C_L$, $C_D$, $C_M$, and $L/D$ across user-specified angle of attack ranges ($-6^\circ$ to $+16^\circ$), Reynolds numbers ($5 \times 10^4$ to $10^7$), and Mach numbers ($0.0$ to $0.85$).
- **Automated Stability & Control Derivatives:**
  - Lift-curve slope ($C_{L_\alpha}$ per degree and per radian)
  - Zero-lift angle of attack ($\alpha_{0L}$)
  - Zero-lift parasite drag coefficient ($C_{D0}$) and induced drag factor ($K$)
  - Maximum aerodynamic efficiency ($(L/D)_{max}$) and cruise angle ($\alpha_{cruise}$)
  - Pitching moment slope ($C_{M_\alpha}$) and Aerodynamic Center location ($x_{ac}/c$)
  - Static margin against arbitrary center of gravity ($x_{cg}/c$)
  - Transonic drag-divergence Mach number ($M_{dd}$) via Korn's equation
- **Formal 5-Tier Uncertainty Quantification:** Propagates input tolerances, discretization GCI, model discrepancy, and experimental balance limits into 95% expanded uncertainty intervals ($U_{95}$) for every polar point.

### 2. 3D Wing Aerodynamics via Vortex Lattice Method (VLM)
- Discretizes arbitrary trapezoidal and swept wings with span, taper, sweep, dihedral, and twist.
- Evaluates 3D circulation distribution $\Gamma(y)$, spanwise lift, Trefftz-plane induced drag $C_{Di}$, Oswald efficiency factor $e$, and 3D Prandtl-Glauert compressibility scaling.
- Validated against the classic AGARD AR-138 ONERA M6 reference wing benchmark.

### 3. Multi-Standard Aerospace Exporters
Export aerodynamic databases directly into industry-standard flight mechanics toolchains with embedded uncertainty:
- **USAF DATCOM (`.dat`):** Formatted fixed-column namelist cards (`$FLTCON`, `$OPTINS`, `$SYNTHS`, `$WGPLNF`) with condition-by-condition GUM uncertainty comments.
- **NASA S/HABP (`.shabp`):** Space-Vehicle High-Speed Aerodynamic Boundary Program input deck with standard `$TABLE` definitions and expanded $U_{95}$ columns.
- **6-DOF Flight Dynamics CSV (`.csv`):** Includes explicit `cl_uncertainty_u95`, `cd_uncertainty_u95`, and `cm_uncertainty_u95` columns ready for robust control design in MATLAB/Simulink Aerospace Blockset, JSBSim, PX4, or ArduPilot.
- **JSON Schema:** Full machine-readable flight envelope data with cryptographic SHA-256 provenance hash.

### 4. Continuous Benchmark Validation Registry
- Automated CI validation gate running reference test suites against published literature:
  - **NACA 0012:** Thin airfoil theory and NASA LTPT experimental data (Abbott & von Doenhoff, 1959).
  - **RAE 2822:** Supercritical transonic section baseline (AGARD AR-138 Case 6).
  - **Eppler E387:** High-efficiency low-Reynolds UAV section (NASA TM-4102).
  - **ONERA M6:** Finite swept wing subsonic/compressible aerodynamics (AGARD AR-138).
- Fails the build if any calculation regresses beyond published physical error bounds.

### 5. Evidence Artifacts Aligned with ASME V&V 20 & NASA-STD-7009B
- Generates structured, publication-ready verification dossiers in both **HTML/PDF** and **JSON**:
  - Formal discretization error estimation per **ASME V&V 20-2009** ($GCI_{fine}$, observed order $p$, Richardson extrapolation).
  - Credibility scoring aligned with **NASA-STD-7009B Credibility Assessment Scale (CAS)** across Verification, Validation, Input Pedigree, and Results Uncertainty.
  - Complete digital chain of custody with **SHA-256 cryptographic provenance hashing** of geometry, solver configurations, and results.

### 6. Universal Airfoil Geometry Ingestion & Pre-Processing
- **Supported Formats:** Selig (`.dat`, `.txt`), Lednicer (`.dat`), tabular CSV/TSV (`.csv`), or analytical 4-digit NACA profiles.
- **Automated Geometry Normalization:**
  - Auto-strips coordinate headers and detects delimiter layout.
  - Automatically translates leading edge to $(0.0, 0.0)$ and aligns chord with positive x-axis.
  - Scales to unit chord ($c = 1.0$).
  - Cosine-clustered resampling (120 panels) to accurately capture high-gradient suction peaks and stagnation zones.

### 7. Conformal 6-Block C-Grid OpenFOAM Mesher
- Generates structured, conformal 6-block C-grid `blockMeshDict` with:
  - Exact C-topology curved arcs surrounding leading edge and downstream wake domain.
  - Physical airfoil wall patches correctly mapped to block vertices: `(8 20 19 7)`, `(7 19 18 6)`, `(8 9 21 20)`, `(9 10 22 21)`.
  - Boundary layer wall normal grading ($R_{grad} = 15$) ensuring $y^+ \sim 1$ resolution for OpenFOAM `simpleFoam` / `rhoSimpleFoam` and SU2 solvers.

### 8. Multi-Fidelity Investigation & Epistemic Classification
- Every computation result carries an epistemic classification: `CALCULATED`, `PREDICTED`, `ESTIMATED`, `ASSUMED`, or `UNVERIFIED`.
- Surrogate model predictions carry out-of-domain (OOD) status: `IN_DOMAIN`, `EXTRAPOLATION`, or `OUT_OF_DOMAIN`.
- Panel solver results are correctly labeled `VERIFIED_PANEL_VISCOUS` — never fabricated as "CFD" or "experimental".
- Cryptographic SHA-256 audit trail with append-only Merkle DAG provenance chain.

### 9. Enterprise Commercial Tiers
- **Community** (free): 50 polar sweeps/month, core panel solver, basic exports
- **Professional** ($290/mo): Unlimited polars, full DATCOM/S-HABP export, surrogate inference
- **Team** ($1,200/mo): Multi-seat, shared investigations, priority compute
- **Enterprise Defense** (custom): Air-gapped deployment, ITAR compliance, dedicated SLA

---

## Quickstart

### One-Command Turnkey Launcher

Clone the repository and run the unified launcher:

```powershell
# Windows (PowerShell or Command Prompt)
python run_aasi.py

# Or simply double-click:
run_aasi.bat
```

```bash
# Linux / macOS
python3 run_aasi.py
```

The launcher will:
1. Detect and activate the Python virtual environment.
2. Spin up the FastAPI Physics Backend on port `8000`.
3. Launch the Next.js Engineering Cockpit on port `3000`.
4. Run automated health checks and open `http://localhost:3000` in your default browser.
5. Provide clean, graceful shutdown on `Ctrl+C`.

---

### Manual Setup (Optional)

#### Backend Setup
```powershell
# Create & activate environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to access the Mission Control interface.

### Docker Deployment
```bash
# Set required environment variables
export AASI_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Build and start all services
docker-compose up --build -d

# Verify health
curl http://localhost:8000/api/health
```

---

## API Reference

AASI provides an enterprise-ready REST API with interactive Swagger documentation at `http://localhost:8000/docs`:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/aerodb/generate` | Generate full flight envelope Aero DB and stability derivatives |
| `GET` | `/api/aerodb/{id}` | Retrieve generated aerodynamic database |
| `GET` | `/api/aerodb/{id}/export?format={datcom\|shabp\|csv\|json}` | Download Aero DB formatted for DATCOM, S/HABP, or 6-DOF simulation |
| `POST` | `/api/geometry/upload` | Ingest and normalize Selig, Lednicer, or CSV airfoil files |
| `POST` | `/api/geometry/direct` | Generate normalized geometry from analytical NACA 4-digit code |
| `POST` | `/api/investigate/study/asme-vv20` | Execute ASME V&V 20-2009 Grid Convergence Index study |
| `GET` | `/api/investigate/{job_id}/dossier` | Export publication-ready HTML/PDF NASA-STD-7009B Certification Dossier |
| `GET` | `/api/investigate/{job_id}/dossier/json` | Export machine-readable JSON certification dossier |
| `GET` | `/api/health` | System health check and active module status |
| `GET` | `/docs` | Interactive OpenAPI Swagger documentation |
| `GET` | `/redoc` | ReDoc API documentation |

---

## Curated Benchmark Profiles

A library of validated test airfoils is included in [`data/airfoils/`](data/airfoils/):

- **`clark_y.dat`**: General aviation baseline profile ($t/c = 11.7\%$) in Selig format.
- **`rae2822.dat`**: Supercritical transonic validation benchmark (AGARD AR 138).
- **`eppler_e387.dat`**: High-efficiency low-Reynolds sailplane/UAV section.
- **`naca0012.dat`**: Standard symmetric section for rotorcraft and code validation.
- **`custom_uav_wing.csv`**: Tactical high-lift cambered UAV profile in CSV format.

---

## Automated Verification Test Suite

AASI maintains a comprehensive test suite of **948+ passing tests** covering physics validation, epistemic integrity, API contracts, export formats, security, and end-to-end workflows:

```powershell
# Run the complete test suite
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

```text
============================== 948 passed in ~90s ==============================
```

Key test categories:
- **Physics Validation:** Panel solver against NACA 0012 thin-airfoil theory and Abbott & von Doenhoff experimental data
- **ASME V&V 20:** Grid Convergence Index, Richardson extrapolation, observed order verification
- **Epistemic Integrity:** Anti-fabrication guards, classification enforcement, Merkle DAG immutability
- **Export Verification:** DATCOM format compliance, S/HABP namelist validation, 6-DOF CSV structure
- **Security & Auth:** RBAC, session management, secret key validation, CORS enforcement
- **End-to-End Workflows:** Geometry ingestion → panel solver → polar sweep → export pipeline

Frontend TypeScript type integrity:
```bash
cd frontend && npx tsc --noEmit
# 0 errors
```

---

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/aasi_aerodynamic_certification.yml`) runs:
1. **Backend Regression Suite** — Full 948-test pytest execution
2. **Frontend Build & Typecheck** — Next.js production build with zero errors
3. **ASME V&V 20 Certification Gate** — Benchmark verification against NASA LTPT NACA 0012 and AGARD 138 RAE 2822

---

## Limitations & Operational Envelope

AASI's fast aerodynamic database engine is optimized for **rapid conceptual trade studies and early-stage preliminary aircraft/UAV design**. Users should observe the following physics envelopes:

| Parameter / Regime | Recommended Range | Limitations & High-Fidelity Recommendation |
| :--- | :--- | :--- |
| **Mach Number ($M$)** | $0.0 \le M \le 0.70$ | Subsonic attached flow. Transonic shock formation above $M_{crit}$ requires viscous compressible CFD (e.g., OpenFOAM / SU2). |
| **Angle of Attack ($\alpha$)** | $-4^\circ \le \alpha \le 12^\circ$ | High-alpha non-linear stall and post-stall separation require Reynolds-Averaged Navier-Stokes (RANS) or empirical post-stall models. |
| **Reynolds Number ($Re$)** | $10^5 \le Re \le 10^7$ | Low-$Re$ laminar separation bubbles ($Re < 10^5$) require transition modeling or wind tunnel calibration. |
| **Geometry** | 2D Airfoils + 3D Planform Approximations | Complex 3D fuselage-wing-nacelle interference requires full 3D CFD or Vortex Lattice Methods (VLM). |

---

## Engineering Disclaimer

> **IMPORTANT NOTICE:** All aerodynamic calculations, stability derivatives, and verification metrics produced by AASI are intended for preliminary engineering design, conceptual trade studies, educational research, and optimization workflows. They do not constitute certified flight test data. All aerodynamic characteristics must be independently validated through higher-fidelity computational methods, wind-tunnel experimentation, or flight testing prior to flight-critical hardware manufacturing or flight operations.

---

## Technology Stack

- **Physics & Verification Engine:** Python 3.12, NumPy, SciPy, SymPy, Astropy, RocketPy
- **API & Service Layer:** FastAPI, Pydantic v2, Uvicorn, HTTPX
- **Frontend Cockpit:** Next.js 14 (App Router), TypeScript, Vanilla CSS, SVG Vector Polars, Three.js
- **CFD & Mesh Dispatcher:** OpenFOAM `blockMeshDict` (6-block C-grid), SU2, XFOIL
- **Verification Methodologies:** ASME V&V 20-2009, NASA-STD-7009B, USAF DATCOM, NASA S/HABP
- **Infrastructure:** Docker, docker-compose, Redis, GitHub Actions CI/CD
- **Security:** JWT auth, RBAC, SHA-256 cryptographic provenance, rate limiting

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
