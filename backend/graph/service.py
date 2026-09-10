"""
AASI In-Memory Scientific Knowledge Graph Service.

Stores aerospace entities and directed relations, providing traversal,
subgraph extraction, and relationship querying without heavyweight external databases.
"""

from typing import Dict, Any, List, Optional
from backend.graph.models import EntityType, RelationType, GraphEntity, GraphRelation


class KnowledgeGraphService:
    """In-memory directed multigraph for scientific entities and relations."""

    def __init__(self):
        self.entities: Dict[str, GraphEntity] = {}
        self.relations: List[GraphRelation] = []
        self._seed_aerospace_graph()

    def _seed_aerospace_graph(self):
        # 1. Organizations
        self.add_entity(GraphEntity(entity_id="ORG-NASA", name="NASA", entity_type=EntityType.ORGANIZATION))
        self.add_entity(GraphEntity(entity_id="ORG-ISRO", name="ISRO", entity_type=EntityType.ORGANIZATION))
        self.add_entity(GraphEntity(entity_id="ORG-ESA", name="ESA", entity_type=EntityType.ORGANIZATION))

        # 2. Airfoils & Papers
        self.add_entity(GraphEntity(entity_id="AF-NACA0012", name="NACA 0012", entity_type=EntityType.AIRFOIL, properties={"max_thickness": 0.12, "camber": 0.0}))
        self.add_entity(GraphEntity(entity_id="PUB-NASA-TND628", name="NASA TN-D-628", entity_type=EntityType.PAPER, properties={"year": 1961}))
        self.add_entity(GraphEntity(entity_id="PUB-NACA-TR824", name="NACA-TR-824", entity_type=EntityType.PAPER, properties={"year": 1945}))

        # 3. Solvers, Datasets, Simulations, Models
        self.add_entity(GraphEntity(entity_id="SOLV-OPENFOAM", name="OpenFOAM", entity_type=EntityType.SOLVER, properties={"family": "FVM"}))
        self.add_entity(GraphEntity(entity_id="DS-AIRFRANS", name="AirfRANS", entity_type=EntityType.DATASET, properties={"cases": 1000}))
        self.add_entity(GraphEntity(entity_id="MOD-AEROGRAPHNET", name="AeroGraphNet", entity_type=EntityType.MODEL, properties={"type": "GNN"}))

        # 4. Rockets, Missions, Celestial Bodies
        self.add_entity(GraphEntity(entity_id="MSN-CHANDRAYAAN3", name="Chandrayaan-3", entity_type=EntityType.MISSION))
        self.add_entity(GraphEntity(entity_id="RCK-LVM3", name="LVM3", entity_type=EntityType.ROCKET))
        self.add_entity(GraphEntity(entity_id="RCK-FALCON9", name="Falcon 9", entity_type=EntityType.ROCKET))
        self.add_entity(GraphEntity(entity_id="BOD-MOON", name="Moon", entity_type=EntityType.MOON))
        self.add_entity(GraphEntity(entity_id="BOD-MARS", name="Mars", entity_type=EntityType.PLANET))

        # 5. Add Relationships
        self.add_relation(GraphRelation(source_id="AF-NACA0012", relation_type=RelationType.DESCRIBED_IN, target_id="PUB-NASA-TND628"))
        self.add_relation(GraphRelation(source_id="AF-NACA0012", relation_type=RelationType.DESCRIBED_IN, target_id="PUB-NACA-TR824"))
        self.add_relation(GraphRelation(source_id="PUB-NASA-TND628", relation_type=RelationType.PART_OF, target_id="ORG-NASA"))
        self.add_relation(GraphRelation(source_id="MOD-AEROGRAPHNET", relation_type=RelationType.TRAINED_ON, target_id="DS-AIRFRANS"))
        self.add_relation(GraphRelation(source_id="DS-AIRFRANS", relation_type=RelationType.SIMULATED_BY, target_id="SOLV-OPENFOAM"))
        self.add_relation(GraphRelation(source_id="MSN-CHANDRAYAAN3", relation_type=RelationType.USES, target_id="RCK-LVM3"))
        self.add_relation(GraphRelation(source_id="MSN-CHANDRAYAAN3", relation_type=RelationType.OPERATES_AT, target_id="BOD-MOON"))
        self.add_relation(GraphRelation(source_id="RCK-LVM3", relation_type=RelationType.PART_OF, target_id="ORG-ISRO"))

    def add_entity(self, entity: GraphEntity) -> bool:
        """Adds or updates an entity."""
        self.entities[entity.entity_id] = entity
        return True

    def add_relation(self, relation: GraphRelation) -> bool:
        """Adds a relation between existing entities."""
        if relation.source_id not in self.entities or relation.target_id not in self.entities:
            return False
        self.relations.append(relation)
        return True

    def get_entity(self, entity_id: str) -> Optional[GraphEntity]:
        return self.entities.get(entity_id)

    def get_neighbors(self, entity_id: str) -> List[Dict[str, Any]]:
        """Returns all outbound and inbound connected entities with relation tags."""
        neighbors = []
        for r in self.relations:
            if r.source_id == entity_id:
                target = self.entities.get(r.target_id)
                if target:
                    neighbors.append({
                        "direction": "OUTBOUND",
                        "relation": r.relation_type.value,
                        "entity": target.model_dump()
                    })
            elif r.target_id == entity_id:
                source = self.entities.get(r.source_id)
                if source:
                    neighbors.append({
                        "direction": "INBOUND",
                        "relation": r.relation_type.value,
                        "entity": source.model_dump()
                    })
        return neighbors

    def search_entities(self, query: str, entity_type: Optional[EntityType] = None) -> List[GraphEntity]:
        """Searches graph entities by name or properties."""
        q = query.lower()
        results = []
        for ent in self.entities.values():
            if entity_type and ent.entity_type != entity_type:
                continue
            if q in ent.name.lower() or q in ent.entity_id.lower():
                results.append(ent)
        return results
