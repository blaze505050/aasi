"""
AASI Cognitive Engine: Cognitive Memory & Scientific Skill Architecture.
Stores verified facts, failed investigations, repair strategies, physics relationships,
and reusable aerospace procedures (ScientificSkills) with explicit trigger conditions.
"""

from __future__ import annotations

import difflib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aasi.cognitive.memory")


class CognitiveMemoryCategory(str, Enum):
    """Rigorous memory categories defined in Section 12."""
    FACT = "FACT"
    EXPERIMENT = "EXPERIMENT"
    HYPOTHESIS = "HYPOTHESIS"
    FAILURE = "FAILURE"
    REPAIR = "REPAIR"
    TOOL = "TOOL"
    PHYSICS_RELATIONSHIP = "PHYSICS_RELATIONSHIP"
    MODEL_LIMITATION = "MODEL_LIMITATION"
    DESIGN_PATTERN = "DESIGN_PATTERN"
    INVESTIGATION = "INVESTIGATION"
    SKILL = "SKILL"


class CognitiveMemoryRecord(BaseModel):
    """Atomic memory unit retained across scientific investigations."""
    record_id: str = Field(default_factory=lambda: f"MEM-{uuid.uuid4().hex[:8].upper()}")
    category: CognitiveMemoryCategory
    title: str
    content: str
    geometry: str = "GENERIC_AIRFOIL"
    operating_conditions: Dict[str, Any] = Field(default_factory=dict)
    physics_domain: str = "aerodynamics"
    epistemic_tier: str = "VERIFIED"
    provenance_hash: str = ""
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ScientificSkill(BaseModel):
    """
    Reusable engineering procedure built from verified investigations.
    Not an LLM prompt; defines explicit triggers, inputs, workflow, verification, and repair.
    """
    skill_id: str = Field(default_factory=lambda: f"SKL-{uuid.uuid4().hex[:8].upper()}")
    name: str = Field(..., description="E.g. NACA Airfoil RANS CFD Investigation")
    domain: str = "aerodynamics"
    trigger_conditions: List[str] = Field(..., description="Conditions activating this skill (e.g. ['geometry_is_airfoil', 'needs_drag_breakdown'])")
    required_inputs: Dict[str, str] = Field(..., description="Inputs schema (geometry, alpha_deg, reynolds, mach)")
    workflow_steps: List[str] = Field(..., description="Deterministic sequence of actions")
    tools_required: List[str] = Field(..., description="IDs of tools invoked")
    verification_checks: List[str] = Field(..., description="Verification gates that must be satisfied")
    known_failure_modes: List[str] = Field(default_factory=list, description="Common solver or mesh breakdown mechanisms")
    repair_strategies: List[str] = Field(default_factory=list, description="Prescribed actions when failure occurs")
    evidence_history: List[str] = Field(default_factory=list, description="Historical investigation IDs successfully executing this skill")
    success_rate: float = 1.0
    version: int = 1


class CognitiveMemoryEngine:
    """Manages persistent cognitive records, failure-repair diagnosis, and scientific skills."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or os.getenv("AASI_COGNITIVE_MEMORY_PATH", "data/cognitive_memory.json"))
        self._records: Dict[str, CognitiveMemoryRecord] = {}
        self._skills: Dict[str, ScientificSkill] = {}
        self._load_memory()
        self._initialize_default_skills()

    def _load_memory(self) -> None:
        """Loads memory entries from disk if present."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for rec_data in data.get("records", []):
                        rec = CognitiveMemoryRecord(**rec_data)
                        self._records[rec.record_id] = rec
                    for skl_data in data.get("skills", []):
                        skl = ScientificSkill(**skl_data)
                        self._skills[skl.skill_id] = skl
                logger.info("Loaded %d cognitive records and %d skills from %s", len(self._records), len(self._skills), self.storage_path)
            except Exception as e:
                logger.warning("Failed loading cognitive memory from %s: %s", self.storage_path, e)
        else:
            self._seed_foundational_memory()

    def _seed_foundational_memory(self) -> None:
        """Seeds critical failure-repair knowledge and physics relationships."""
        # Seed 1: High Alpha RANS Divergence & Repair
        self.add_record(
            CognitiveMemoryRecord(
                category=CognitiveMemoryCategory.FAILURE,
                title="Steady RANS Non-Convergence at Post-Stall Alpha > 18 deg",
                content="Steady RANS (simpleFoam) exhibits oscillating residuals (> 1e-2) and Courant blow-up due to massive shed vortices.",
                geometry="NACA 0012",
                operating_conditions={"alpha_deg": 20.0, "reynolds": 3.0e6, "mach": 0.15},
                physics_domain="aerodynamics",
                epistemic_tier="FAILED_INVESTIGATION",
                tags=["stall", "divergence", "rans_limitation", "high_alpha"],
            )
        )
        self.add_record(
            CognitiveMemoryRecord(
                category=CognitiveMemoryCategory.REPAIR,
                title="Repair Strategy for High-Alpha Stall Divergence",
                content="Switch solver from steady simpleFoam to transient pimpleFoam with bounded relaxation and deltaT satisfying CFL < 0.8, or fall back to empirical Abbott wind-tunnel polar.",
                geometry="NACA 0012",
                operating_conditions={"alpha_deg": 20.0, "reynolds": 3.0e6},
                physics_domain="aerodynamics",
                epistemic_tier="VERIFIED",
                tags=["repair", "relaxation", "unsteady", "pimpleFoam"],
            )
        )
        # Seed 2: D'Alembert Paradox Relationship
        self.add_record(
            CognitiveMemoryRecord(
                category=CognitiveMemoryCategory.PHYSICS_RELATIONSHIP,
                title="Inviscid D'Alembert Paradox Invariant",
                content="In ideal steady potential flow around closed 2D airfoils, integrated pressure drag is identically zero (CD = 0) regardless of camber or angle of attack. Non-zero drag requires viscous shear stress or wake displacement.",
                geometry="GENERIC_AIRFOIL",
                physics_domain="aerodynamics",
                epistemic_tier="ANALYTICAL",
                tags=["potential_flow", "dalembert", "zero_drag", "theory"],
            )
        )

    def _initialize_default_skills(self) -> None:
        """Initializes canonical aerospace skills."""
        if not self._skills:
            self.register_skill(
                ScientificSkill(
                    name="NACA Airfoil Multi-Fidelity Investigation",
                    domain="aerodynamics",
                    trigger_conditions=["geometry_is_airfoil", "needs_flight_polar"],
                    required_inputs={"geometry": "str", "alpha_deg": "float", "reynolds": "float", "mach": "float"},
                    workflow_steps=[
                        "Step 1: Check Abbott & von Doenhoff empirical wind-tunnel catalog",
                        "Step 2: Run discrete vortex panel solver with Squire-Young viscous correction",
                        "Step 3: Execute conformal 6-block C-grid OpenFOAM simpleFoam simulation",
                        "Step 4: Audit residuals and verify via ASME V&V 20 GCI",
                        "Step 5: Reconcile multi-fidelity discrepancies and consolidate memory",
                    ],
                    tools_required=["scientific_knowledge_catalog", "discrete_vortex_panel", "openfoam_simplefoam", "asme_vv20_verifier"],
                    verification_checks=["RESIDUALS_BELOW_1E4", "CONSERVATION_CHECK", "ASME_VV20_GCI"],
                    known_failure_modes=["High-alpha separation divergence", "Near-wall mesh grading y+ > 5"],
                    repair_strategies=["Refine boundary layer grading to 15", "Use transient pimpleFoam"],
                )
            )

    def add_record(self, record: CognitiveMemoryRecord) -> None:
        self._records[record.record_id] = record
        self._persist()

        # Synchronize with consolidated EpistemicMemoryKernel
        try:
            from backend.science.epistemic_kernel import epistemic_kernel, EpistemicRecord, EpistemicRecordType, EpistemicTrustTier
            rec_type_map = {
                CognitiveMemoryCategory.FAILURE: EpistemicRecordType.FAILED_INVESTIGATION,
                CognitiveMemoryCategory.REPAIR: EpistemicRecordType.REPAIR_STRATEGY,
                CognitiveMemoryCategory.PHYSICS_RELATIONSHIP: EpistemicRecordType.PHYSICS_RELATIONSHIP,
            }
            rec_type = rec_type_map.get(record.category, EpistemicRecordType.SCIENTIFIC_ASSUMPTION)
            ep_rec = EpistemicRecord(
                record_id=record.record_id,
                record_type=rec_type,
                trust_tier=EpistemicTrustTier.ANALYTICAL if record.category == CognitiveMemoryCategory.PHYSICS_RELATIONSHIP else EpistemicTrustTier.VERIFIED_CFD,
                title=record.title,
                geometry=record.geometry,
                operating_conditions=record.operating_conditions,
                assumptions=[record.content],
                failures=[{"description": record.content}] if record.category == CognitiveMemoryCategory.FAILURE else [],
                repair_strategies=[record.content] if record.category == CognitiveMemoryCategory.REPAIR else [],
            )
            epistemic_kernel.store_record(ep_rec)
        except Exception:
            pass

    def register_skill(self, skill: ScientificSkill) -> None:
        self._skills[skill.skill_id] = skill
        self._persist()

    def search_memory(
        self,
        query: str,
        category: Optional[CognitiveMemoryCategory] = None,
        geometry: Optional[str] = None,
        k: int = 3,
    ) -> List[CognitiveMemoryRecord]:
        """Multi-criteria similarity retrieval across cognitive records."""
        matches: List[CognitiveMemoryRecord] = []
        for rec in self._records.values():
            if category and rec.category != category:
                continue
            if geometry and rec.geometry != "GENERIC_AIRFOIL" and geometry.lower() not in rec.geometry.lower():
                continue
            matches.append(rec)

        # Simple text similarity ranking
        def score(rec: CognitiveMemoryRecord) -> float:
            ratio = difflib.SequenceMatcher(None, query.lower(), (rec.title + " " + rec.content).lower()).ratio()
            return ratio

        matches.sort(key=score, reverse=True)
        return matches[:k]

    def find_repairs_for_failure(self, failure_description: str) -> List[CognitiveMemoryRecord]:
        """Finds matching repair strategies when an investigation diverges or fails."""
        return self.search_memory(failure_description, category=CognitiveMemoryCategory.REPAIR, k=2)

    def get_skill_for_investigation(self, geometry: str, task: str) -> Optional[ScientificSkill]:
        """Retrieves best-matching scientific skill for a proposed investigation."""
        for skill in self._skills.values():
            if "airfoil" in geometry.lower() and "polar" in task.lower():
                return skill
        return list(self._skills.values())[0] if self._skills else None

    def _persist(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "records": [r.model_dump() for r in self._records.values()],
                "skills": [s.model_dump() for s in self._skills.values()],
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning("Could not persist cognitive memory: %s", e)


# Global cognitive memory engine instance
cognitive_memory_engine = CognitiveMemoryEngine()
