"""
AASI Agent Package.
Provides the autonomous experiment planner, graph engine, fidelity decision engine,
execution controller, diagnostics, repair engine, and report generator.
Preserves backwards compatibility with legacy AASIAgent.
"""

# New Phase 25 Autonomous Architecture
from backend.agent.scientific_state import (
    ProvenanceState,
    CFDResultState,
    ColabExecutionState,
    ScientificStateMachine,
    StateTransitionRecord,
)
from backend.agent.planner import (
    ScientificPlanner,
    ExperimentSpecification,
)
from backend.agent.experiment_graph import (
    ExperimentGraph,
    TaskNode,
    TaskEdge,
    TaskStatus,
)
from backend.agent.decision_engine import (
    FidelityDecisionEngine,
    FidelityLevel,
    FidelityDecision,
)
from backend.agent.diagnostics import (
    CFDDiagnosticsEngine,
    DiagnosticReport,
    CFDErrorClass,
)
from backend.agent.repair_engine import (
    CFDRepairEngine,
    RepairCandidate,
    RepairOutcome,
)
from backend.agent.report_generator import (
    ScientificReportGenerator,
    ScientificReport,
    MultiFidelityComparison,
    QuantityWithProvenance,
)
from backend.agent.execution_controller import (
    AutonomousExecutionController,
)

# Legacy AASIAgent backwards compatibility
try:
    from backend.agent.agent_legacy import (
        AASIAgent,
        AASIAgentError,
        OllamaUnavailableError,
        OllamaRuntimeError,
        default_agent,
    )
except ImportError:
    pass

__all__ = [
    # State & Provenance
    "ProvenanceState",
    "CFDResultState",
    "ColabExecutionState",
    "ScientificStateMachine",
    "StateTransitionRecord",
    # Planner & Graph
    "ScientificPlanner",
    "ExperimentSpecification",
    "ExperimentGraph",
    "TaskNode",
    "TaskEdge",
    "TaskStatus",
    # Decision & Execution
    "FidelityDecisionEngine",
    "FidelityLevel",
    "FidelityDecision",
    "AutonomousExecutionController",
    # Diagnostics & Repair
    "CFDDiagnosticsEngine",
    "DiagnosticReport",
    "CFDErrorClass",
    "CFDRepairEngine",
    "RepairCandidate",
    "RepairOutcome",
    # Report Generator
    "ScientificReportGenerator",
    "ScientificReport",
    "MultiFidelityComparison",
    "QuantityWithProvenance",
    # Legacy
    "AASIAgent",
    "AASIAgentError",
    "OllamaUnavailableError",
    "OllamaRuntimeError",
    "default_agent",
]
