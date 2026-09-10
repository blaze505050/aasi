"""
AASI Physics-AI Subsystem.

Production-grade aerodynamic neural surrogates, leakage-free data partitioning,
physics-aware validation gates, epistemic uncertainty modeling, and reproducible training.
"""

from backend.physics_ai.schemas import (
    AirfoilSample,
    AerodynamicPrediction,
    UncertaintyMetrics,
    DomainStatusEnum,
)
from backend.physics_ai.active_learning import (
    ActiveLearning2Engine,
    ActiveLearningCandidateRecord,
    AcquisitionStrategy,
    CandidateStatus,
    active_learning_registry,
)

__all__ = [
    "AirfoilSample",
    "AerodynamicPrediction",
    "UncertaintyMetrics",
    "DomainStatusEnum",
    "ActiveLearning2Engine",
    "ActiveLearningCandidateRecord",
    "AcquisitionStrategy",
    "CandidateStatus",
    "active_learning_registry",
]

