# AASI 2.0 — 02. Existing Capabilities Inventory

| Capability | Module / Component | Epistemic Classification | Verification Status |
| :--- | :--- | :--- | :--- |
| **2D Airfoil Aerodynamics** | `backend/physics/panel_solver.py` | `ANALYTICAL` | Verified against Abbott NACA 0012 |
| **3D Wing Aerodynamics** | `backend/physics/surface_pressure_3d.py` | `ANALYTICAL` | Verified against ONERA M6 benchmark |
| **Multi-Condition Polar Sweeps**| `backend/physics/aerodb_engine.py` | `ANALYTICAL` / `DERIVED` | Verified across $\alpha \in [-6^\circ, 18^\circ]$ |
| **Stability Derivatives Extraction**| `backend/physics/aerodb_engine.py` | `DERIVED` | Formally extracted ($C_{L\alpha}$, $X_{ac}$, $C_{D0}$) |
| **USAF DATCOM Card Exporter** | `backend/export/aerodb_export.py` | `DERIVED` | Formally aligned with DATCOM format |
| **NASA S/HABP Polar Exporter** | `backend/export/aerodb_export.py` | `DERIVED` | Formally aligned with S/HABP format |
| **6-DOF Autopilot Exporter** | `backend/export/autopilot_exporter.py` | `DERIVED` | Formally formatted for Simulink/JSBSim |
| **GUM Uncertainty Quantification** | `backend/physics/uncertainty_model.py`| `DERIVED` | Bounded $u_{95}$ ($k=2$, ASME V&V 20) |
| **Hardware Resource Auditing** | `backend/governor/resource_monitor.py` | `MEASURED` | Verified on Windows & Linux hosts |
| **Fail-Closed Safety Governor** | `backend/governor/safety_governor.py` | `GOVERNANCE` | Verified fail-closed path with audit log |
| **Global Emergency Kill Switch** | `backend/governor/kill_switch.py` | `GOVERNANCE` | Atomic cooperative halt & debounce |
| **General Agent Task Harness** | `backend/harness/task_harness.py` | `ORCHESTRATION` | Full 8-state cognitive lifecycle |
| **AASI Mission Language (AML)** | `backend/scientific_language/` | `LANGUAGE` | AST lexer, parser, physics validator |
| **Scientific DAG Compiler** | `backend/scientific_compiler/` | `COMPILER` | Dependency DAG resolution & scheduling |
| **Merkle Lineage Graph** | `backend/science/merkle_lineage.py` | `PROVENANCE` | Cryptographic SHA-256 integrity DAG |
| **Physics AI Surrogate Models** | `backend/physics_ai/` | `SURROGATE` | Trained on 17,595 CFD samples ($R^2 > 0.99$) |
| **OpenFOAM Meshing Staging** | `backend/cfd/` | `STAGED_ONLY` | C-grid generation staged for execution |
