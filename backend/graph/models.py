"""
AASI Scientific Knowledge Graph Models.

Defines the 16 Entity types and 10 Relation types forming the foundation
of the scientific knowledge graph.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EntityType(str, Enum):
    AIRCRAFT = "Aircraft"
    AIRFOIL = "Airfoil"
    ROCKET = "Rocket"
    ENGINE = "Engine"
    SPACECRAFT = "Spacecraft"
    MISSION = "Mission"
    PLANET = "Planet"
    MOON = "Moon"
    MATERIAL = "Material"
    EXPERIMENT = "Experiment"
    DATASET = "Dataset"
    PAPER = "Paper"
    SIMULATION = "Simulation"
    SOLVER = "Solver"
    MODEL = "Model"
    ORGANIZATION = "Organization"


class RelationType(str, Enum):
    USES = "USES"
    MEASURED_BY = "MEASURED_BY"
    SIMULATED_BY = "SIMULATED_BY"
    VALIDATED_BY = "VALIDATED_BY"
    DESCRIBED_IN = "DESCRIBED_IN"
    PART_OF = "PART_OF"
    OPERATES_AT = "OPERATES_AT"
    DERIVED_FROM = "DERIVED_FROM"
    CITES = "CITES"
    TRAINED_ON = "TRAINED_ON"


class GraphEntity(BaseModel):
    entity_id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())



class GraphRelation(BaseModel):
    source_id: str
    relation_type: RelationType
    target_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0
