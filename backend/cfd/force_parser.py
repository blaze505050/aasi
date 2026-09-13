"""
AASI Phase 21: OpenFOAM Force and Aerodynamic Coefficient Parser.
Governing Rule: Absolute Anti-Fabrication Rule.
Parses postProcessing forceCoeffs.dat and forces.dat files for CL, CD, and CM histories.
"""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np


class CFDForceParser:
    """Parses OpenFOAM aerodynamic force and coefficient outputs."""

    @classmethod
    def parse_force_coeffs_dat(cls, file_path: Path) -> Dict[str, Any]:
        """
        Parse OpenFOAM postProcessing/forceCoeffs/0/coefficient.dat or forceCoeffs.dat.
        Standard header: # Time  Cm  Cd  Cl  Cl(f)  Cl(r)
        """
        path = Path(file_path)
        if not path.exists():
            return {"parsed": False, "error": f"Force file not found: {path}"}

        iterations: List[int] = []
        cl_history: List[float] = []
        cd_history: List[float] = []
        cm_history: List[float] = []

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    tokens = line.split()
                    if len(tokens) >= 4:
                        try:
                            # Standard OpenFOAM forceCoeffs: Time, Cm, Cd, Cl
                            iter_val = int(float(tokens[0]))
                            cm_val = float(tokens[1])
                            cd_val = float(tokens[2])
                            cl_val = float(tokens[3])

                            iterations.append(iter_val)
                            cm_history.append(cm_val)
                            cd_history.append(cd_val)
                            cl_history.append(cl_val)
                        except ValueError:
                            continue
        except Exception as e:
            return {"parsed": False, "error": str(e)}

        if not iterations:
            return {"parsed": False, "error": "No valid data rows found in force file"}

        # Compute stabilization statistics on last 20% of iterations (min 5, max 100)
        window = max(5, min(100, int(len(iterations) * 0.2)))
        cl_tail = cl_history[-window:]
        cd_tail = cd_history[-window:]
        cm_tail = cm_history[-window:]

        cl_mean = float(np.mean(cl_tail))
        cl_std = float(np.std(cl_tail))
        cd_mean = float(np.mean(cd_tail))
        cd_std = float(np.std(cd_tail))
        cm_mean = float(np.mean(cm_tail))
        cm_std = float(np.std(cm_tail))

        # Relative variation in CD over stabilization window
        cd_relative_variation = abs(cd_std / (abs(cd_mean) + 1e-6))
        cl_relative_variation = abs(cl_std / (abs(cl_mean) + 1e-6))

        return {
            "parsed": True,
            "total_records": len(iterations),
            "final_iteration": iterations[-1],
            "stabilization_window": window,
            "CL": {
                "final": cl_history[-1],
                "mean": round(cl_mean, 5),
                "std": round(cl_std, 6),
                "relative_variation": round(cl_relative_variation, 5),
                "history": cl_history,
            },
            "CD": {
                "final": cd_history[-1],
                "mean": round(cd_mean, 5),
                "std": round(cd_std, 6),
                "relative_variation": round(cd_relative_variation, 5),
                "history": cd_history,
            },
            "CM": {
                "final": cm_history[-1],
                "mean": round(cm_mean, 5),
                "std": round(cm_std, 6),
                "history": cm_history,
            },
            "iterations": iterations,
        }

    @classmethod
    def find_and_parse_forces(cls, case_dir: Path) -> Dict[str, Any]:
        """Scan case directory for standard OpenFOAM force coefficient files."""
        case_path = Path(case_dir)
        candidates = [
            case_path / "postProcessing/forceCoeffs/0/coefficient.dat",
            case_path / "postProcessing/forceCoeffs/0/forceCoeffs.dat",
            case_path / "postProcessing/forces/0/force.dat",
            case_path / "forceCoeffs.dat",
        ]
        for cand in candidates:
            if cand.exists() and cand.stat().st_size > 0:
                return cls.parse_force_coeffs_dat(cand)

        # Fallback: search recursively in postProcessing
        post_dir = case_path / "postProcessing"
        if post_dir.exists():
            for dat_file in post_dir.glob("**/*.dat"):
                res = cls.parse_force_coeffs_dat(dat_file)
                if res.get("parsed", False):
                    return res

        return {
            "parsed": False,
            "error": "No force coefficient files found in postProcessing directory.",
        }
