"""Scientific result-resolution architecture prioritizing validated datasets, analytical tools, and literature."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from .dataset_registry import DatasetRegistry
from .retriever import HybridRetriever


class ResultResolutionDispatcher:
    """Dispatches aerospace scientific queries through the resolution hierarchy.

    Hierarchy:
    1. Normalized conditions search against verified experimental/CFD dataset registry.
    2. If exact validated match exists -> return reference result + provenance + citation.
    3. If no dataset match, check applicability of Phase 2 engineering tools (orbit, rocket, math).
    4. If no analytical tool exists, retrieve scientific literature for qualitative grounding.
    5. Never invent or hallucinate numerical results.
    """

    def __init__(
        self,
        dataset_registry: DatasetRegistry,
        retriever: Optional[HybridRetriever] = None,
    ):
        self.dataset_registry = dataset_registry
        self.retriever = retriever

    def extract_conditions(self, query: str) -> Dict[str, Any]:
        """Extract and normalize physical flow conditions and geometry from natural language."""
        conditions: Dict[str, Any] = {}

        # 1. Airfoil / Geometry detection (e.g. NACA 0012, NACA 4412, NACA 2412)
        naca_match = re.search(r"\b(NACA\s*\d{4,5})\b", query, re.IGNORECASE)
        if naca_match:
            # normalize spacing e.g. "NACA 0012"
            raw_geo = naca_match.group(1).upper()
            conditions["geometry"] = re.sub(r"NACA\s*", "NACA ", raw_geo)

        # 2. Mach number (e.g. Mach 0.3, M=0.3, Mach=0.85)
        mach_match = re.search(r"\b(?:Mach|M)\s*(?:=|\s|at)\s*([0-9]*\.?[0-9]+)\b", query, re.IGNORECASE)
        if mach_match:
            try:
                conditions["mach"] = float(mach_match.group(1))
            except ValueError:
                pass

        # 3. Reynolds number (e.g. Re=500000, Reynolds 500,000, Re = 5e5, 500k)
        re_match = re.search(
            r"\b(?:Reynolds|Re)\s*(?:number)?\s*(?:=|\s|of)\s*([0-9]+(?:\.[0-9]+)?(?:e[0-9]+)?|[0-9]{1,3}(?:,[0-9]{3})+)\b",
            query,
            re.IGNORECASE,
        )
        if re_match:
            raw_re = re_match.group(1).replace(",", "")
            try:
                conditions["reynolds"] = float(raw_re)
            except ValueError:
                pass

        # 4. Angle of Attack (e.g. AoA=8°, alpha=8 deg, AoA 8 deg, 8 degrees angle of attack)
        aoa_match = re.search(
            r"\b(?:AoA|alpha|angle of attack)\s*(?:=|\s|at|of)?\s*(-?[0-9]+(?:\.[0-9]+)?)\s*(?:°|deg|degrees)?\b",
            query,
            re.IGNORECASE,
        )
        if not aoa_match:
            aoa_alt = re.search(r"(-?[0-9]+(?:\.[0-9]+)?)\s*(?:°|deg|degrees)\s*(?:AoA|alpha|angle of attack)", query, re.IGNORECASE)
            if aoa_alt:
                aoa_match = aoa_alt

        if aoa_match:
            try:
                conditions["aoa_deg"] = float(aoa_match.group(1))
            except ValueError:
                pass

        # 5. Physical target variable (drag, lift, pitching moment, pressure)
        q_lower = query.lower()
        if any(term in q_lower for term in ["drag coefficient", "cd", "drag polar"]):
            conditions["target_variable"] = "CD"
        elif any(term in q_lower for term in ["lift coefficient", "cl", "lift slope"]):
            conditions["target_variable"] = "CL"
        elif any(term in q_lower for term in ["pitching moment", "cm"]):
            conditions["target_variable"] = "CM"

        return conditions

    def resolve(self, query: str) -> Dict[str, Any]:
        """Execute the resolution decision workflow."""
        extracted = self.extract_conditions(query)

        # Stage 1: If physical conditions (geometry + conditions) are present, check dataset registry
        has_conditions = any(k in extracted for k in ["mach", "reynolds", "aoa_deg"]) or "target_variable" in extracted
        if "geometry" in extracted and has_conditions:
            geo = extracted["geometry"]
            mach = extracted.get("mach")
            reynolds = extracted.get("reynolds")
            aoa = extracted.get("aoa_deg")

            dataset_matches = self.dataset_registry.query_conditions(
                geometry=geo,
                mach=mach,
                reynolds=reynolds,
                aoa_deg=aoa,
                domain="aerodynamics",
            )

            if dataset_matches:
                match = dataset_matches[0]
                target_var = extracted.get("target_variable", "CD")
                matched_pts = match.get("matched_points", [])

                return {
                    "resolution_type": "EXACT_VALIDATED_DATASET",
                    "status": "SUCCESS",
                    "query_conditions": extracted,
                    "dataset_id": match["dataset_id"],
                    "dataset_name": match["dataset_name"],
                    "source": match["source"],
                    "citation": match["citation"],
                    "is_experimental": match["is_experimental"],
                    "validation_status": match["validation_status"],
                    "matched_points": matched_pts,
                    "target_variable": target_var,
                    "uncertainty": match.get("uncertainty"),
                    "explanation": (
                        f"Found verified {('experimental' if match['is_experimental'] else 'benchmark CFD')} "
                        f"dataset for {geo} matching query conditions."
                    ),
                }
            else:
                # Geometry was identified, but no exact conditions exist in registry
                return {
                    "resolution_type": "NO_MATCHING_DATASET",
                    "status": "NOT_FOUND_IN_REGISTRY",
                    "query_conditions": extracted,
                    "explanation": (
                        f"Geometry '{geo}' recognized, but no exact validated dataset matching "
                        f"Mach={mach}, Re={reynolds}, AoA={aoa}° is currently registered in AASI."
                    ),
                    "action_required": "FALLBACK_TO_LITERATURE_OR_TOOL",
                }

        # Stage 2: Return pass-through for general question or tool routing
        return {
            "resolution_type": "GENERAL_OR_LITERATURE",
            "status": "PROCEED",
            "query_conditions": extracted,
        }
