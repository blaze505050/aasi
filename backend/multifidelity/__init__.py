"""
AASI Multi-Fidelity Scientific Fabric.

Exposes fidelity hierarchies, result models, cross-fidelity discrepancy engines,
uncertainty calibration audits, and cascade resolver.
"""

from backend.multifidelity.models import (
    FidelityLevel,
    CFDQualityClassification,
    FlowConditions,
    MultiFidelityResult,
    DiscrepancyResult,
    UncertaintyCalibrationMetrics,
)
from backend.multifidelity.discrepancy import MultiFidelityDiscrepancyEngine
from backend.multifidelity.calibration import UncertaintyCalibrationEngine
from backend.multifidelity.resolver import MultiFidelityResolver
from backend.multifidelity.consistency import CrossFidelityConsistencyValidator
from backend.multifidelity.fusion import MultiFidelityFusionEngine
from backend.multifidelity.registry import MultiFidelityRegistry
from backend.multifidelity.service import MultiFidelityService, multi_fidelity_service

__all__ = [
    "FidelityLevel",
    "CFDQualityClassification",
    "FlowConditions",
    "MultiFidelityResult",
    "DiscrepancyResult",
    "UncertaintyCalibrationMetrics",
    "MultiFidelityDiscrepancyEngine",
    "UncertaintyCalibrationEngine",
    "MultiFidelityResolver",
    "CrossFidelityConsistencyValidator",
    "MultiFidelityFusionEngine",
    "MultiFidelityRegistry",
    "MultiFidelityService",
    "multi_fidelity_service",
]

