"""
AASI Phase 21: OpenFOAM Residual Parser.
Governing Rule: Absolute Anti-Fabrication Rule.
Parses equation residuals and continuity errors from actual solver logs.
"""

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class CFDResidualParser:
    """Parses solver log outputs for equation residuals and continuity behavior."""

    RESIDUAL_PATTERN = re.compile(
        r"Solving for (?P<field>[A-Za-z0-9_]+),\s+Initial residual = (?P<init>[-+0-9.eE]+),\s+Final residual = (?P<final>[-+0-9.eE]+)"
    )
    CONTINUITY_PATTERN = re.compile(
        r"time step continuity errors : sum local = (?P<local>[-+0-9.eE]+),\s+Global = (?P<global>[-+0-9.eE]+),\s+cumulative = (?P<cum>[-+0-9.eE]+)"
    )

    @classmethod
    def parse_log_text(cls, log_text: str) -> Dict[str, Any]:
        """Parse raw log text and extract residual histories."""
        residuals: Dict[str, List[float]] = {}
        continuity_local: List[float] = []
        continuity_global: List[float] = []
        has_nan_or_inf = False

        for line in log_text.splitlines():
            # Check for NaN / Inf
            if "nan" in line.lower() or "inf" in line.lower():
                # Verify if it's in a numerical context
                if "fatal" in line.lower() or "residual" in line.lower() or "error" in line.lower():
                    has_nan_or_inf = True

            match = cls.RESIDUAL_PATTERN.search(line)
            if match:
                field = match.group("field")
                try:
                    init_val = float(match.group("init"))
                    if math.isnan(init_val) or math.isinf(init_val):
                        has_nan_or_inf = True
                    if field not in residuals:
                        residuals[field] = []
                    residuals[field].append(init_val)
                except ValueError:
                    has_nan_or_inf = True

            cont_match = cls.CONTINUITY_PATTERN.search(line)
            if cont_match:
                try:
                    loc_val = float(cont_match.group("local"))
                    glob_val = float(cont_match.group("global"))
                    continuity_local.append(loc_val)
                    continuity_global.append(glob_val)
                except ValueError:
                    pass

        # Compute summary metrics per field
        summary: Dict[str, Any] = {}
        for field, values in residuals.items():
            if len(values) > 0:
                init = values[0]
                final = values[-1]
                min_val = min(values)
                max_val = max(values)
                drop_orders = (
                    math.log10(init / final) if (init > 0 and final > 0 and init >= final) else 0.0
                )
                summary[field] = {
                    "initial": init,
                    "final": final,
                    "min": min_val,
                    "max": max_val,
                    "order_of_magnitude_drop": round(drop_orders, 3),
                    "iterations": len(values),
                }

        return {
            "residuals": residuals,
            "continuity_local": continuity_local,
            "continuity_global": continuity_global,
            "has_nan_or_inf": has_nan_or_inf,
            "summary": summary,
            "total_iterations": max([len(v) for v in residuals.values()]) if residuals else 0,
        }

    @classmethod
    def parse_log_file(cls, log_path: Path) -> Dict[str, Any]:
        """Parse log file from disk."""
        path = Path(log_path)
        if not path.exists():
            return {
                "residuals": {},
                "has_nan_or_inf": False,
                "summary": {},
                "total_iterations": 0,
                "error": f"Log file not found: {path}",
            }
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            return cls.parse_log_text(content)
        except Exception as e:
            return {
                "residuals": {},
                "has_nan_or_inf": True,
                "summary": {},
                "total_iterations": 0,
                "error": str(e),
            }
