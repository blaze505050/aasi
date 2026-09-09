"""Dynamic discovery and environment inspection for host and WSL2 scientific solvers."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import Dict, Optional
from .models import SolverAvailability, SolverInfo

logger = logging.getLogger(__name__)


class SolverDetector:
    """Probes host operating system (Windows) and WSL2 Linux environments for CFD and scientific solvers."""

    def __init__(self, wsl_distro: str = "Ubuntu-22.04"):
        self.wsl_distro = wsl_distro

    def detect_all(self) -> Dict[str, SolverInfo]:
        """Probe all supported scientific solvers and return their availability."""
        return {
            "OpenFOAM": self.detect_openfoam(),
            "SU2": self.detect_su2(),
            "XFOIL": self.detect_xfoil(),
            "XFLR5": self.detect_xflr5(),
        }

    def detect_openfoam(self) -> SolverInfo:
        """Probe host Windows PATH and WSL2 Linux distributions for OpenFOAM binaries."""
        # 1. Check native Windows binary (e.g. OpenFOAM for Windows)
        win_path = shutil.which("simpleFoam.exe") or shutil.which("simpleFoam")
        if win_path:
            return SolverInfo(
                solver_name="OpenFOAM",
                version="Windows Native",
                executable_path=win_path,
                is_available=True,
                status=SolverAvailability.AVAILABLE,
                supported_domains=["aerodynamics", "hydrodynamics", "combustion"],
                supported_physics=["RANS", "LES", "Incompressible", "Compressible"],
                supported_dimensions=["2D", "3D"],
                execution_environment="host",
                detection_diagnostic="OpenFOAM detected in Windows PATH",
            )

        # 2. Check WSL2 Linux environment
        wsl_binary = shutil.which("wsl.exe") or shutil.which("wsl")
        if wsl_binary:
            try:
                # Probe WSL2 with a strict 3-second timeout
                res = subprocess.run(
                    ["wsl.exe", "-d", self.wsl_distro, "bash", "-c", "which simpleFoam 2>/dev/null || which foamRun 2>/dev/null"],
                    capture_output=True,
                    text=True,
                    timeout=3.0,
                )
                if res.returncode == 0 and res.stdout.strip():
                    linux_path = res.stdout.strip()
                    return SolverInfo(
                        solver_name="OpenFOAM",
                        version="v2312 (WSL2)",
                        executable_path=f"wsl:{linux_path}",
                        is_available=True,
                        status=SolverAvailability.AVAILABLE,
                        supported_domains=["aerodynamics", "hydrodynamics", "thermal"],
                        supported_physics=["RANS (SA, k-omega SST)", "LES", "Incompressible"],
                        supported_dimensions=["2D", "3D"],
                        execution_environment="wsl2",
                        detection_diagnostic=f"OpenFOAM found in WSL2 distro '{self.wsl_distro}' at {linux_path}",
                    )
                else:
                    return SolverInfo(
                        solver_name="OpenFOAM",
                        is_available=False,
                        status=SolverAvailability.NOT_AVAILABLE,
                        execution_environment="wsl2",
                        detection_diagnostic=f"WSL2 available, but simpleFoam was not found in PATH for distro '{self.wsl_distro}'",
                    )
            except subprocess.TimeoutExpired:
                return SolverInfo(
                    solver_name="OpenFOAM",
                    is_available=False,
                    status=SolverAvailability.DETECTION_ERROR,
                    detection_diagnostic="WSL2 probe timed out (WSL disk or service unresponsive)",
                )
            except Exception as exc:
                return SolverInfo(
                    solver_name="OpenFOAM",
                    is_available=False,
                    status=SolverAvailability.DETECTION_ERROR,
                    detection_diagnostic=f"WSL2 detection error: {str(exc)}",
                )

        return SolverInfo(
            solver_name="OpenFOAM",
            is_available=False,
            status=SolverAvailability.NOT_AVAILABLE,
            detection_diagnostic="Neither Windows OpenFOAM nor WSL2 subsystem is configured in system PATH",
        )

    def detect_su2(self) -> SolverInfo:
        """Probe for SU2 CFD solver binaries."""
        path = shutil.which("SU2_CFD.exe") or shutil.which("SU2_CFD")
        if path:
            return SolverInfo(
                solver_name="SU2",
                version="v7.5",
                executable_path=path,
                is_available=True,
                status=SolverAvailability.AVAILABLE,
                supported_domains=["aerodynamics", "compressible_flow"],
                supported_physics=["Euler", "Navier-Stokes", "RANS"],
                supported_dimensions=["2D", "3D"],
                execution_environment="host",
                detection_diagnostic=f"SU2 found at {path}",
            )
        return SolverInfo(
            solver_name="SU2",
            is_available=False,
            status=SolverAvailability.NOT_AVAILABLE,
            supported_domains=["aerodynamics", "compressible_flow"],
            supported_physics=["Euler", "Navier-Stokes", "RANS"],
            detection_diagnostic="SU2_CFD executable not found in PATH",
        )

    def detect_xfoil(self) -> SolverInfo:
        """Probe for XFOIL subsonic airfoil solver."""
        path = shutil.which("xfoil.exe") or shutil.which("xfoil")
        if path:
            return SolverInfo(
                solver_name="XFOIL",
                version="v6.99",
                executable_path=path,
                is_available=True,
                status=SolverAvailability.AVAILABLE,
                supported_domains=["aerodynamics"],
                supported_physics=["Panel Method", "Viscous Boundary Layer Coupling"],
                supported_dimensions=["2D"],
                execution_environment="host",
                detection_diagnostic=f"XFOIL found at {path}",
            )
        return SolverInfo(
            solver_name="XFOIL",
            is_available=False,
            status=SolverAvailability.NOT_AVAILABLE,
            supported_domains=["aerodynamics"],
            supported_physics=["Panel Method", "Viscous Coupling"],
            detection_diagnostic="xfoil executable not found in PATH",
        )

    def detect_xflr5(self) -> SolverInfo:
        """Probe for XFLR5 analysis tool."""
        path = shutil.which("xflr5.exe") or shutil.which("xflr5")
        if path:
            return SolverInfo(
                solver_name="XFLR5",
                version="v6.58",
                executable_path=path,
                is_available=True,
                status=SolverAvailability.AVAILABLE,
                supported_domains=["aerodynamics", "stability"],
                supported_physics=["VLM", "3D Panel Method"],
                supported_dimensions=["3D"],
                execution_environment="host",
                detection_diagnostic=f"XFLR5 found at {path}",
            )
        return SolverInfo(
            solver_name="XFLR5",
            is_available=False,
            status=SolverAvailability.NOT_AVAILABLE,
            supported_domains=["aerodynamics", "stability"],
            supported_physics=["VLM", "3D Panel Method"],
            detection_diagnostic="xflr5 executable not found in PATH",
        )


# Default detector instance
solver_detector = SolverDetector()
