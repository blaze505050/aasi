# AASI 2.0 — 04. Integration Gaps & Implementation Roadmap

## 1. Identified Architecture Gaps

| Area | Current Baseline | Target State (AASI 2.0) | Gap Resolution |
| :--- | :--- | :--- | :--- |
| **Tool Protocol** | Dict-based parameters | Strongly-typed `ToolSpec` and `ToolResult` | Implemented in `backend/harness/tool_bus.py` |
| **Safety Governance** | Ad-hoc checks | Fail-closed `SafetyGovernor` with Merkle audit chain | Implemented in `backend/governor/` |
| **Resource Awareness** | Static probes in runner | Live `ResourceMonitor` with EMA smoothing & budgets | Implemented in `backend/governor/` |
| **Agent Harness** | Legacy prompt scripts | Deterministic 8-state cognitive task harness | Implemented in `backend/harness/task_harness.py` |
| **External Adapters** | OpenFOAM only | Unified adapters for RocketPy, OpenMDAO, SU2 | Build modular adapters in `backend/adapters/` |
| **Browser Research** | None | Bounded, citation-preserving, read-only researcher | Build bounded research agent with injection shields |
| **Skills Registry** | Skills in `.agents/skills` | AASI-native declarative skill format in `skills/` | Create 14 executable skills in `skills/` |
| **UI Integration** | Static display | Live Governor HUD, KillSwitch, and Task Harness | Wire REST endpoints into Next.js control plane |
| **Commercialization** | Single-tier access | Researcher, Engineering, Enterprise RBAC tiers | Define tier models in `backend/compliance/` |
