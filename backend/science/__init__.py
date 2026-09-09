"""AASI Scientific Result Resolution & Condition Normalization Subsystem."""

from .models import EpistemicStatus, ConditionMatchStatus, NormalizedConditions, ScientificResult, SourceDiscrepancy
from .normalizer import EngineeringQueryNormalizer
from .matcher import ConditionMatchingEngine
from .experimental import ExperimentalDatabase, ExperimentalDataset
from .cfd import CFDDatabase, CFDRecord
from .surrogates import SurrogateRegistry, SurrogateMetadata
from .validators import ScientificValidationEngine
from .conflict import ConflictResolutionEngine
from .engine import ScientificResolutionEngine
from .service import ScienceService, get_science_service

__all__ = [
    "EpistemicStatus",
    "ConditionMatchStatus",
    "NormalizedConditions",
    "ScientificResult",
    "SourceDiscrepancy",
    "EngineeringQueryNormalizer",
    "ConditionMatchingEngine",
    "ExperimentalDatabase",
    "ExperimentalDataset",
    "CFDDatabase",
    "CFDRecord",
    "SurrogateRegistry",
    "SurrogateMetadata",
    "ScientificValidationEngine",
    "ConflictResolutionEngine",
    "ScientificResolutionEngine",
    "ScienceService",
    "get_science_service",
]
