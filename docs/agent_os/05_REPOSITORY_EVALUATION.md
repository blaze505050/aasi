# AASI 2.0 — 05. Open-Source Repository Evaluation

**Evaluation Framework**: Rigorous review of architecture, license compatibility, security posture, and resource footprint.

---

## 1. General Agent Harnesses

### 1.1 `openclaw/openclaw`
- **License**: MIT
- **Architecture**: Claw-based modular agent harness with typed actions.
- **Assessment**: Provides lightweight action-contract abstractions. However, full dependency introduces external telemetry.
- **Classification**: `STUDY_PATTERN_ONLY` — We adopt the typed tool dispatch patterns directly in `backend/harness/` with zero dependency bloat.

### 1.2 `OpenHands/OpenHands` (formerly OpenDevin)
- **License**: MIT
- **Architecture**: Microservice-heavy multi-agent container runtime with Docker sandbox.
- **Assessment**: Overkill for AASI's modular monolith architecture; requires Docker daemon and multi-GB images.
- **Classification**: `REJECT` — Too heavy for local workstations; introduces unnecessary operational fragility.

### 1.3 `OpenInterpreter/open-interpreter`
- **License**: AGPL-3.0 / MIT (varying by component)
- **Architecture**: Conversational terminal code execution.
- **Assessment**: AGPL-3.0 license is legally dangerous for AASI's proprietary commercial enterprise distribution. Also executes unrestricted shell commands.
- **Classification**: `REJECT` — Incompatible with commercial terms and violates the fail-closed least-privilege security doctrine.

### 1.4 `browser-use/browser-use`
- **License**: MIT
- **Architecture**: Playwright-based browser automation driven by LLM vision.
- **Assessment**: Extremely useful for web research, but full autonomous browser automation can execute dangerous side effects (form submission, payment, logins).
- **Classification**: `ADAPT_SELECTED_COMPONENT` — Adapt a read-only, bounded research adapter with domain allowlists and prompt-injection sanitization.

### 1.5 `pydantic/pydantic-ai`
- **License**: MIT
- **Architecture**: Strongly-typed model and agent framework natively built on Pydantic v2.
- **Assessment**: Fully aligned with AASI's Pydantic 2.x codebase. Elegant, robust, zero extra bloat.
- **Classification**: `IMPLEMENT_COMPATIBLE_INTERFACE` — AASI's ToolSpec and ToolBus use compatible Pydantic v2 schemas.

### 1.6 `SWE-agent/SWE-agent`
- **License**: MIT
- **Architecture**: Software engineering agent with dedicated file viewer and linter tools.
- **Assessment**: Excellent file navigation design (line slicing, regex search, structured replace).
- **Classification**: `STUDY_PATTERN_ONLY` — Implemented in AASI's controlled workspace file operations.

---

## 2. Skills and Tool Interoperability

### 2.1 `anthropics/skills`
- **License**: Apache-2.0
- **Architecture**: Directory-based declarative skills (`SKILL.md` with YAML frontmatter and shell/python helpers).
- **Assessment**: Clean, auditable, and human-readable pattern.
- **Classification**: `ADOPT_AS_DEPENDENCY` / `IMPLEMENT_COMPATIBLE_INTERFACE` — Adopted as AASI's native skill specification in `skills/`.

### 2.2 `modelcontextprotocol/servers` (MCP)
- **License**: MIT
- **Architecture**: Standardized JSON-RPC protocol for agent-tool communication.
- **Assessment**: Industry standard for tool interoperability. Must remain behind the Safety Governor barrier.
- **Classification**: `IMPLEMENT_COMPATIBLE_INTERFACE` — AASI tools expose MCP-compatible schemas while preserving internal fail-closed authorization.

### 2.3 `danyuchn/asd-ste100-skill`
- **License**: Unspecified / Content restricted by ASD
- **Assessment**: ASD-STE100 is copyrighted by the AeroSpace and Defence Industries Association of Europe. Cannot claim formal certification or copy dictionary tables.
- **Classification**: `STUDY_PATTERN_ONLY` — Use technical clarity and passive-voice reduction principles in AML without infringing copyright.

---

## 3. Aerospace and Scientific Computing

### 3.1 `su2code/SU2`
- **License**: LGPL-2.1
- **Architecture**: C++ open-source CFD and aerodynamic shape optimization solver.
- **Assessment**: Powerful for compressible and transonic flows. Large binary footprint (requires C++ build / MPI).
- **Classification**: `IMPLEMENT_COMPATIBLE_INTERFACE` — Provide a staged SU2 config generator and output ingestion adapter without bundling binaries.

### 3.2 `OpenMDAO/OpenMDAO`
- **License**: Apache-2.0
- **Architecture**: NASA framework for Multidisciplinary Design Optimization (MDO).
- **Assessment**: Clean, Python-native gradient-based optimization engine.
- **Classification**: `ADAPT_SELECTED_COMPONENT` — Create an adapter wrapping AASI aerodynamic polars into OpenMDAO Component models.

### 3.3 `RocketPy-Team/RocketPy`
- **License**: MIT
- **Architecture**: 6-DOF flight trajectory simulation for sounding rockets and atmospheric vehicles.
- **Assessment**: High-quality Python trajectory engine with atmospheric integration.
- **Classification**: `ADAPT_SELECTED_COMPONENT` — Implement a trajectory adapter converting AASI aerodynamic tables into RocketPy vehicle aerodynamics.
