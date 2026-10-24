"""
AASI 30-Problem Aerospace Platform: Modular Architecture & Verification Kernel.
"""

from backend.modules.base import (
    BenchmarkCase,
    BenchmarkEvaluation,
    EpistemicClassification,
    EvidenceRecord,
    FidelityLevel,
    ModuleResult,
    ProblemModule,
    compute_sha256_provenance,
)
from backend.modules.airfoil_2d import Airfoil2DModule
from backend.modules.vlm_3d import VLM3DModule
from backend.modules.benchmark_registry import (
    BenchmarkRegistry,
    ModuleBenchmarkReport,
    PlatformValidationSuiteReport,
    benchmark_registry,
)

__all__ = [
    "ProblemModule",
    "FidelityLevel",
    "EpistemicClassification",
    "BenchmarkCase",
    "BenchmarkEvaluation",
    "EvidenceRecord",
    "ModuleResult",
    "compute_sha256_provenance",
    "Airfoil2DModule",
    "VLM3DModule",
    "BenchmarkRegistry",
    "ModuleBenchmarkReport",
    "PlatformValidationSuiteReport",
    "benchmark_registry",
]
