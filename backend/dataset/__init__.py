"""
AASI CFD Dataset Knowledge Fabric Package.
"""

from backend.dataset.schema import (
    CFDRecord,
    GeometrySpec,
    FlowConditions,
    MeshMetrics,
    SolverConfig,
    SimulationResults,
    ValidationMetrics,
    ProvenanceMetadata,
)
from backend.dataset.storage import (
    ObjectStorageBackend,
    MetadataStore,
    ScientificFeatureStore,
)
from backend.dataset.catalog import CFDCatalog
from backend.dataset.similarity import AerodynamicSimilarity
from backend.dataset.retrieval import CFDRetrievalEngine
from backend.dataset.provenance import DatasetProvenanceGuard

__all__ = [
    "CFDRecord",
    "GeometrySpec",
    "FlowConditions",
    "MeshMetrics",
    "SolverConfig",
    "SimulationResults",
    "ValidationMetrics",
    "ProvenanceMetadata",
    "ObjectStorageBackend",
    "MetadataStore",
    "ScientificFeatureStore",
    "CFDCatalog",
    "AerodynamicSimilarity",
    "CFDRetrievalEngine",
    "DatasetProvenanceGuard",
]
