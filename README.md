# AASI — Autonomous Aerospace Scientific Intelligence

> **Preliminary Aerodynamic Database Generation, Automated Verification, & Multi-Fidelity Investigation Platform**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![ASME V&V 20-2009](https://img.shields.io/badge/Methodology-ASME%20V%26V%2020--2009-brightgreen.svg)](https://www.asme.org/codes-standards/find-codes-standards/v-v-20-standard-verification-validation-computational-fluid-dynamics-heat-transfer)
[![NASA-STD-7009B](https://img.shields.io/badge/Methodology-NASA--STD-7009B%20CAS-blue.svg)](https://standards.nasa.gov/standard/NASA/NASA-STD-7009)
[![USAF DATCOM](https://img.shields.io/badge/Export-USAF%20DATCOM-red.svg)](#multi-standard-aerospace-exporters)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Executive Summary

**AASI** is an aerodynamic engineering and scientific investigation platform designed for UAV developers, aerodynamicists, eVTOL teams, and aerospace researchers. It transforms the traditionally fragmented, labor-intensive aerodynamic database workflow into an automated, verifiable pipeline for conceptual and preliminary design.

AASI computes aerodynamic coefficients, stability derivatives, and grid convergence metrics deterministically using verified first-principles physics (discrete vortex panel methods, Helmbold-Keune finite-span corrections, Karman-Tsien compressibility, Schlichting/Squire-Young boundary layer drag estimates) alongside structured verification frameworks following the methodologies of **ASME V&V 20-2009** and **NASA-STD-7009B**.

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

## Core Capabilities

### 1. Aerodynamic Database (Aero DB) Generation Engine
- **Flight Envelope Sweeps:** Generates full tabular matrices of $C_L$, $C_D$, $C_M$, and $L/D$ across user-specified angle of attack ranges ($-6^\circ$ to $+16^\circ$), Reynolds numbers ($5 \times 10^4$ to $10^7$), and Mach numbers ($0.0$ to $0.85$).
- **Automated Stability & Control Derivatives:**
  - Lift-curve slope ($C_{L_\alpha}$ per degree and per radian)
  - Zero-lift angle of attack ($\alpha_{0L}$)
  - Zero-lift parasite drag coefficient ($C_{D0}$) and induced drag factor ($K$)
  - Maximum aerodynamic efficiency ($(L/D)_{max}$) and cruise angle ($\alpha_{cruise}$)
  - Pitching moment slope ($C_{M_\alpha}$) and Aerodynamic Center location ($x_{ac}/c$)
  - Static margin against arbitrary center of gravity ($x_{cg}/c$)
  - Transonic drag-divergence Mach number ($M_{dd}$) via Korn's equation

### 2. Multi-Standard Aerospace Exporters
Export aerodynamic databases directly into industry-standard flight mechanics toolchains in 1 click:
- **USAF DATCOM (`.dat`):** Formatted fixed-column namelist cards (`$FLTCON`, `$OPTINS`, `$SYNTHS`, `$WGPLNF`) for direct ingestion into classical aircraft stability and control workflows.
- **NASA S/HABP (`.shabp`):** Space-Vehicle High-Speed Aerodynamic Boundary Program input deck with standard `$TABLE` definitions.
- **6-DOF Flight Dynamics CSV (`.csv`):** Ready for direct import into MATLAB/Simulink Aerospace Blockset, JSBSim, or FlightGear.
- **JSON Schema:** Full machine-readable flight envelope data for custom MDO (Multidisciplinary Design Optimization) pipelines.

### 3. ASME V&V 20-2009 Verification & GCI Engine
- Implements formal discretization error estimation per **ASME V&V 20-2009** (*Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer*):
  - Systematic grid refinement factor ($r_{21}, r_{32}$)
  - Observed order of accuracy ($p$) solved via fixed-point transcendental iteration
  - Richardson extrapolation estimate ($\phi_{ext}^{21}$)
  - Relative errors ($e_a^{21}, e_{ext}^{21}$)
  - Fine-grid Grid Convergence Index ($GCI_{fine}$ with safety factor $F_s = 1.25$)
  - Asymptotic range of convergence verification ($R_{asymptotic} \approx 1.0$)

### 4. NASA-STD-7009B Credibility Assessment & Verification Dossier Generator
- Generates structured, publication-ready verification dossiers in both **HTML/PDF** and **JSON**:
  - Full **Credibility Assessment Scale (CAS)** rubric scoring across Verification, Validation, Input Pedigree, and Results Uncertainty.
  - Complete digital chain of custody with **SHA-256 and Merkle DAG cryptographic provenance hashing** of geometry, solver outputs, and verification metrics.
  - Formatted for engineering design reviews, technical audits, and data traceability.

### 5. Universal Airfoil Geometry Ingestion & Pre-Processing
- **Supported Formats:** Selig (`.dat`, `.txt`), Lednicer (`.dat`), tabular CSV/TSV (`.csv`), or analytical 4-digit NACA profiles.
- **Automated Geometry Normalization:**
  - Auto-strips coordinate headers and detects delimiter layout.
  - Automatically translates leading edge to $(0.0, 0.0)$ and aligns chord with positive x-axis.
  - Scales to unit chord ($c = 1.0$).
  - Cosine-clustered resampling (120 panels) to accurately capture high-gradient suction peaks and stagnation zones.

### 6. Conformal 6-Block C-Grid OpenFOAM Mesher
- Generates structured, conformal 6-block C-grid `blockMeshDict` with:
  - Exact C-topology curved arcs surrounding leading edge and downstream wake domain.
  - Physical airfoil wall patches correctly mapped to block vertices: `(8 20 19 7)`, `(7 19 18 6)`, `(8 9 21 20)`, `(9 10 22 21)`.
  - Boundary layer wall normal grading ($R_{grad} = 15$) ensuring $y^+ \sim 1$ resolution for OpenFOAM `simpleFoam` / `rhoSimpleFoam` and SU2 solvers.

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

AASI maintains a 100% passing test suite across all physical modules, API contracts, meshing integrity, and export formats:

```powershell
# Run the complete test suite
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

```text
============================== 92 passed in 10.45s ==============================
tests/test_aerodb_engine.py::test_full_envelope_sweep PASSED
tests/test_aerodb_engine.py::test_stability_derivatives PASSED
tests/test_aerodb_export.py::test_datcom_export PASSED
tests/test_aerodb_export.py::test_shabp_export PASSED
tests/test_aerodb_export.py::test_six_dof_csv_export PASSED
tests/test_airfoil_parser.py::test_selig_and_lednicer_parsing PASSED
tests/test_asme_vv20.py::test_grid_convergence_index PASSED
tests/test_dossier_generator.py::test_nasa_7009b_dossier PASSED
tests/test_cfd_mesh_integrity.py::test_conformal_6block_mesh PASSED
tests/test_panel_solver.py::test_real_physics_aerodynamics PASSED
...
```

Frontend TypeScript type integrity:
```bash
cd frontend && npx tsc --noEmit
# 0 errors
```

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
- **Frontend Cockpit:** Next.js 14 (App Router), TypeScript, Vanilla CSS, SVG Vector Polars
- **CFD & Mesh Dispatcher:** OpenFOAM `blockMeshDict` (6-block C-grid), SU2, XFOIL
- **Verification Methodologies:** ASME V&V 20-2009, NASA-STD-7009B, USAF DATCOM, NASA S/HABP

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

