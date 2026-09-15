"""
AASI Scientific AI Planner.
Parses natural-language scientific objectives into deterministic experiment specifications.
"""

import re
import hashlib
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ExperimentSpecification(BaseModel):
    """Deterministic scientific experiment specification."""
    experiment_id: str
    objective: str
    geometry: str
    alpha_deg: float
    reynolds: float
    mach: float = 0.15
    required_outputs: List[str] = Field(default_factory=lambda: ["CL", "CD", "CM", "Cp"])
    fidelity_requirement: str = "adaptive"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    spec_hash: str


class ScientificPlanner:
    """
    Parses natural-language objectives and produces cryptographic experiment specifications.
    """

    AIRFOIL_PATTERN = re.compile(r"\b(NACA\s*\d{4,5}|RAE\s*2822|CLARK\s*Y|S\s*1223|EPPLER\s*\d+)\b", re.IGNORECASE)
    ALPHA_PATTERN = re.compile(r"(?:alpha|aoa|angle\s*of\s*attack)\s*(?:=|is|at)?\s*([+-]?\d+(?:\.\d+)?)\s*(?:deg|degrees|°)?", re.IGNORECASE)
    RE_PATTERN = re.compile(r"(?:re|reynolds)(?:\s*number)?\s*(?:=|is|at)?\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\b", re.IGNORECASE)
    MACH_PATTERN = re.compile(r"(?:mach|m)\s*(?:=|is|at)?\s*([+-]?\d+(?:\.\d+)?)\b", re.IGNORECASE)

    @classmethod
    def parse_objective(cls, objective_text: str, default_mach: float = 0.15) -> ExperimentSpecification:
        """
        Extracts scientific parameters from natural language.
        Enforces strict fallback bounds.
        """
        text = objective_text.strip()

        # 1. Geometry
        geom_match = cls.AIRFOIL_PATTERN.search(text)
        geometry = "NACA 0012"
        if geom_match:
            raw_geom = geom_match.group(1).upper()
            geometry = " ".join(raw_geom.split())  # normalize spacing
        elif "NACA" in text.upper():
            # Check for concatenated NACA numbers like NACA4412
            naca_search = re.search(r"NACA(\d{4,5})", text, re.IGNORECASE)
            if naca_search:
                geometry = f"NACA {naca_search.group(1)}"

        # 2. Angle of Attack
        alpha = 4.0
        alpha_match = cls.ALPHA_PATTERN.search(text)
        if alpha_match:
            try:
                alpha = float(alpha_match.group(1))
            except ValueError:
                alpha = 4.0
        else:
            # Fallback simple degree regex: e.g. "8 degrees" or "8°"
            deg_search = re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:degrees|deg|°)", text, re.IGNORECASE)
            if deg_search:
                try:
                    alpha = float(deg_search.group(1))
                except ValueError:
                    alpha = 4.0

        # 3. Reynolds Number
        reynolds = 3000000.0
        re_match = cls.RE_PATTERN.search(text)
        if re_match:
            try:
                val_str = re_match.group(1).lower()
                reynolds = float(val_str)
            except ValueError:
                reynolds = 3000000.0

        # 4. Mach Number
        mach = default_mach
        mach_match = cls.MACH_PATTERN.search(text)
        if mach_match:
            try:
                mach = float(mach_match.group(1))
            except ValueError:
                mach = default_mach

        # 5. Required outputs
        required_outputs = ["CL", "CD", "CM", "Cp"]
        fidelity_req = "adaptive"
        if "surrogate" in text.lower() and "trustworthy" in text.lower():
            fidelity_req = "adaptive_validation"
        elif "cfd only" in text.lower() or "run openfoam" in text.lower():
            fidelity_req = "live_cfd"
        elif "surrogate only" in text.lower():
            fidelity_req = "surrogate"

        # 6. Cryptographic specification hash
        spec_dict = {
            "objective": text,
            "geometry": geometry,
            "alpha_deg": round(alpha, 4),
            "reynolds": round(reynolds, 2),
            "mach": round(mach, 4),
            "required_outputs": sorted(required_outputs),
            "fidelity_requirement": fidelity_req,
        }
        canonical_str = json.dumps(spec_dict, sort_keys=True)
        spec_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        experiment_id = f"EXP-AASI-{spec_hash[:10].upper()}"

        return ExperimentSpecification(
            experiment_id=experiment_id,
            objective=text,
            geometry=geometry,
            alpha_deg=round(alpha, 4),
            reynolds=round(reynolds, 2),
            mach=round(mach, 4),
            required_outputs=required_outputs,
            fidelity_requirement=fidelity_req,
            spec_hash=spec_hash,
        )
