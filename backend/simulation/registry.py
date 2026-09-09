"""Solver registry managing computational solver discovery and adapters."""

from __future__ import annotations

from typing import Dict, List, Optional
from .adapters.base import BaseSolverAdapter
from .adapters.openfoam import OpenFOAMAdapter
from .adapters.su2 import SU2Adapter
from .adapters.xflr5 import XFLR5Adapter
from .adapters.xfoil import XFOILAdapter
from .detector import solver_detector
from .models import SolverInfo


class SolverRegistry:
    """Central registry tracking available computational solvers and their execution adapters."""

    def __init__(self):
        self._adapters: Dict[str, BaseSolverAdapter] = {
            "OpenFOAM": OpenFOAMAdapter(),
            "SU2": SU2Adapter(),
            "XFOIL": XFOILAdapter(),
            "XFLR5": XFLR5Adapter(),
        }

    def get_adapter(self, solver_name: str) -> Optional[BaseSolverAdapter]:
        """Retrieve execution adapter for solver."""
        for name, adapter in self._adapters.items():
            if name.lower() == solver_name.lower():
                return adapter
        return None

    def list_solvers(self) -> List[SolverInfo]:
        """Probe host environment and list all detected solvers with status."""
        detected = solver_detector.detect_all()
        return list(detected.values())

    def get_solver_info(self, solver_name: str) -> Optional[SolverInfo]:
        """Get detection info for specific solver."""
        detected = solver_detector.detect_all()
        for name, info in detected.items():
            if name.lower() == solver_name.lower():
                return info
        return None


# Default solver registry singleton
solver_registry = SolverRegistry()
