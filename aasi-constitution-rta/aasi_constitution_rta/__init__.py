"""
AASI Constitution RTA Package.
Implements the ASTM F3269-21 Run-Time Assurance architecture,
5-stage isolated cognitive loop, Ed25519 cryptographic kernel,
2-of-3 voting Safety Monitor, and all 19 coded failsafes (F-1 to F-19).
"""

from .kernel import (
    SealedConstitutionalKernel,
    CognitiveLoopStage,
    CognitiveState,
    CognitiveActionProposal,
    AuthorizationVerdict,
    ExecutionResult,
    Ed25519Verifier,
    SignedCommandToken,
)
from .failsafes import (
    FailsafeRegistry,
    FailsafeCode,
    FailsafeViolation,
    FailsafeContext,
    evaluate_all_failsafes,
)
from .safety_monitor import (
    SafetyMonitor2of3,
    RTASwitch,
    RTASwitchState,
    RecoveryFunction,
    EvaluatorVerdict,
)
from .telemetry_parser import (
    CCSDSTelemetryParser,
    CCSDSPacketHeader,
    CCSDSSpacePacket,
)

__all__ = [
    "SealedConstitutionalKernel",
    "CognitiveLoopStage",
    "CognitiveState",
    "CognitiveActionProposal",
    "AuthorizationVerdict",
    "ExecutionResult",
    "Ed25519Verifier",
    "SignedCommandToken",
    "FailsafeRegistry",
    "FailsafeCode",
    "FailsafeViolation",
    "FailsafeContext",
    "evaluate_all_failsafes",
    "SafetyMonitor2of3",
    "RTASwitch",
    "RTASwitchState",
    "RecoveryFunction",
    "EvaluatorVerdict",
    "CCSDSTelemetryParser",
    "CCSDSPacketHeader",
    "CCSDSSpacePacket",
]
