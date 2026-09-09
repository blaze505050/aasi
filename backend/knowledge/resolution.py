"""Scientific result-resolution architecture prioritizing validated datasets, analytical tools, and literature."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from .dataset_registry import DatasetRegistry
from .retriever import HybridRetriever
from backend.science.service import get_science_service


class ResultResolutionDispatcher:
    """Dispatches aerospace scientific queries through the resolution hierarchy.

    Delegates to the first-class ScientificResolutionEngine while maintaining
    full backward compatibility with Phase 3 calling conventions and schemas.
    """

    def __init__(
        self,
        dataset_registry: Optional[DatasetRegistry] = None,
        retriever: Optional[HybridRetriever] = None,
    ):
        self.dataset_registry = dataset_registry
        self.retriever = retriever
        self.science_service = get_science_service()

    def extract_conditions(self, query: str) -> Dict[str, Any]:
        """Extract and normalize physical flow conditions and geometry from natural language."""
        cond = self.science_service.normalizer.normalize(query)
        res: Dict[str, Any] = {}
        if cond.geometry:
            res["geometry"] = cond.geometry
        if cond.mach is not None:
            res["mach"] = cond.mach
        if cond.reynolds is not None:
            res["reynolds"] = cond.reynolds
        if cond.aoa_deg is not None:
            res["aoa_deg"] = cond.aoa_deg
        if cond.requested_outputs:
            res["target_variable"] = cond.requested_outputs[0]
        return res

    def resolve(self, query: str) -> Dict[str, Any]:
        """Execute the resolution decision workflow."""
        extracted = self.extract_conditions(query)

        # First check the underlying first-class ScientificResolutionEngine
        engine_res = self.science_service.engine.resolve(query)
        level = engine_res.get("resolution_level", "")

        # Map to Phase 3 return schema if exact dataset matched
        if "LEVEL 2 - EXPERIMENTAL" in level or "LEVEL 3 - VALIDATED CFD" in level:
            primary = engine_res.get("primary_result", {})
            conds = primary.get("conditions", {})
            target_var = extracted.get("target_variable", "CD")
            is_exp = "EXPERIMENT" in primary.get("epistemic_status", "")

            matched_point = {
                "aoa": conds.get("aoa_deg"),
                "mach": conds.get("mach"),
                "reynolds": conds.get("reynolds"),
                target_var.lower(): primary.get("value"),
            }

            return {
                "resolution_type": "EXACT_VALIDATED_DATASET",
                "status": "SUCCESS",
                "query_conditions": extracted,
                "dataset_id": primary.get("result_id"),
                "dataset_name": primary.get("source"),
                "source": primary.get("source"),
                "citation": primary.get("provenance", {}).get("citation", ""),
                "is_experimental": is_exp,
                "validation_status": primary.get("validation_status", "VALIDATED"),
                "matched_points": [matched_point],
                "target_variable": target_var,
                "uncertainty": primary.get("uncertainty", {}),
                "epistemic_status": primary.get("epistemic_status"),
                "trace": engine_res.get("trace", []),
                "explanation": (
                    f"Found verified {('experimental' if is_exp else 'benchmark CFD')} "
                    f"dataset for {extracted.get('geometry')} matching query conditions."
                ),
            }

        # If conditions were identified but out of domain / no match
        if "geometry" in extracted and any(k in extracted for k in ["mach", "reynolds", "aoa_deg"]):
            return {
                "resolution_type": "NO_MATCHING_DATASET",
                "status": "NOT_FOUND_IN_REGISTRY",
                "query_conditions": extracted,
                "trace": engine_res.get("trace", []),
                "explanation": (
                    f"Geometry '{extracted.get('geometry')}' recognized, but no exact validated dataset matching "
                    f"Mach={extracted.get('mach')}, Re={extracted.get('reynolds')}, AoA={extracted.get('aoa_deg')}° "
                    f"is currently registered in AASI."
                ),
                "action_required": "FALLBACK_TO_LITERATURE_OR_TOOL",
            }

        # Stage 2: Return pass-through for general question or tool routing
        return {
            "resolution_type": "GENERAL_OR_LITERATURE",
            "status": "PROCEED",
            "query_conditions": extracted,
            "trace": engine_res.get("trace", []),
        }
