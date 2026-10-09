"""
AASI XFOIL Solver Adapter.

Executes native XFOIL binary when present on the system host/container,
or seamlessly falls back to the native pure-Python AerodynamicPanelSolver.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from backend.physics.panel_solver import AerodynamicPanelSolver, generate_naca4_coordinates

logger = logging.getLogger("aasi.cfd.xfoil")


class XFoilAdapter:
    """
    Subsonic viscous-inviscid solver interface.
    """

    def __init__(self, xfoil_binary: Optional[str] = None):
        self.xfoil_binary = xfoil_binary or shutil.which("xfoil")
        self.panel_fallback = AerodynamicPanelSolver()

    def is_available(self) -> bool:
        """Checks if native XFOIL binary is executable on host."""
        return self.xfoil_binary is not None and os.access(self.xfoil_binary, os.X_OK)

    def solve(
        self,
        geometry_name: str,
        alpha_deg: float,
        reynolds: float = 3e6,
        mach: float = 0.15,
        coordinates: Optional[np.ndarray] = None,
        timeout_seconds: int = 15,
    ) -> Dict[str, Any]:
        """
        Runs XFOIL if installed, otherwise uses native panel solver.
        """
        if not self.is_available() or coordinates is None:
            # Clean fallback to native panel solver
            if "NACA" in geometry_name.upper():
                self.panel_fallback.set_naca(geometry_name)
            elif coordinates is not None:
                self.panel_fallback.set_coordinates(coordinates)
            else:
                self.panel_fallback.set_naca("0012")

            res = self.panel_fallback.solve(alpha_deg, reynolds, mach)
            res["execution_mode"] = "NATIVE_PANEL_SOLVER"
            return res

        # Run real XFOIL in temporary workspace
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            coord_file = tmp_path / "airfoil.dat"
            polar_file = tmp_path / "polar.txt"

            # Write coordinate file
            with open(coord_file, "w", encoding="utf-8") as f:
                f.write(f"{geometry_name}\n")
                for pt in coordinates:
                    f.write(f" {pt[0]:.6f} {pt[1]:.6f}\n")

            # XFOIL command batch script
            commands = [
                f"LOAD {coord_file.name}",
                "PANE",
                "OPER",
                f"VISC {reynolds:.0f}",
                f"MACH {mach:.3f}",
                "PACC",
                f"{polar_file.name}",
                "",
                f"ALFA {alpha_deg:.2f}",
                "QUIT",
            ]
            input_script = "\n".join(commands) + "\n"

            try:
                proc = subprocess.run(
                    [self.xfoil_binary],
                    input=input_script,
                    text=True,
                    capture_output=True,
                    cwd=tmp_path,
                    timeout=timeout_seconds,
                )

                if polar_file.exists():
                    lines = polar_file.read_text(encoding="utf-8").strip().splitlines()
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 5 and parts[0].replace(".", "", 1).replace("-", "", 1).isdigit():
                            cl = float(parts[1])
                            cd = float(parts[2])
                            cm = float(parts[4])
                            return {
                                "CL": round(cl, 4),
                                "CD": round(cd, 5),
                                "CM": round(cm, 4),
                                "solver": "XFOIL (Direct Viscous-Inviscid Coupling)",
                                "execution_mode": "REAL_BINARY_EXECUTION",
                                "alpha_deg": alpha_deg,
                                "reynolds": reynolds,
                                "mach": mach,
                            }
            except Exception as e:
                logger.warning(f"XFOIL execution error: {e}. Falling back to native panel solver.")

        # Fallback if polar not generated
        self.panel_fallback.set_coordinates(coordinates)
        res = self.panel_fallback.solve(alpha_deg, reynolds, mach)
        res["execution_mode"] = "NATIVE_PANEL_SOLVER"
        return res
