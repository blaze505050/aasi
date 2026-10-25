# AASI 2.0 — 06. License & Attribution Matrix

## 1. Software Bill of Materials (SBOM) & License Compatibility

| Component / Library | Stated License | Compatibility with AASI Commercial Distribution | Obligations / Attribution Requirements |
| :--- | :--- | :--- | :--- |
| **FastAPI** | MIT | Compatible | Retain copyright notice in distributions |
| **Pydantic / Pydantic-Settings** | MIT | Compatible | Retain copyright notice |
| **NumPy** | BSD-3-Clause | Compatible | Retain 3-clause BSD copyright notice |
| **Uvicorn** | BSD-3-Clause | Compatible | Retain BSD notice |
| **Pytest** | MIT | Compatible | Development dependency only |
| **OpenFOAM** | GPL-3.0 | Compatible via Subprocess Boundary | Binary isolated via WSL/Subprocess boundary; no GPL code linked into proprietary kernel |
| **SU2** | LGPL-2.1 | Compatible via External CLI Adapter | Invoked via CLI; no dynamic/static linking into AASI core |
| **RocketPy** | MIT | Compatible | Retain copyright notice in adapter documentation |
| **OpenMDAO** | Apache-2.0 | Compatible | Retain Apache 2.0 notices and state modifications |
| **Anthropic Skills Pattern** | Apache-2.0 | Compatible | Retain attribution to Anthropic pattern in docs |
| **ASD-STE100 Principles** | Restricted Copyright (ASD) | Conditional (Principles Only) | Do NOT copy proprietary vocabulary or claim certification |
| **Open-Interpreter** | AGPL-3.0 | **INCOMPATIBLE** | **REJECTED** — Never link or bundle in commercial core |

---

## 2. Intellectual Property & Anti-Contamination Doctrine

1. **GPL / LGPL Boundary**: All external CFD solvers (OpenFOAM, SU2) communicate strictly via file-based contracts (mesh files, controlDict, force coefficients, residual tables) or separate subprocess invocations. They are never imported or linked as shared objects.
2. **Third-Party Attribution**: All adopted open-source patterns are credited in `THIRD_PARTY_NOTICES.md` with original license texts preserved.
3. **ASD-STE100 Non-Certification**: AASI's Controlled Aerospace Language uses general simplified technical English concepts (active voice, short sentences, explicit units) and makes no claim of endorsement or certification by the ASD-STE100 Maintenance Group.
