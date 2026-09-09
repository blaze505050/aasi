"""Simulation solver adapters package."""

from .base import BaseSolverAdapter
from .openfoam import OpenFOAMAdapter
from .su2 import SU2Adapter
from .xfoil import XFOILAdapter
from .xflr5 import XFLR5Adapter

__all__ = [
    "BaseSolverAdapter",
    "OpenFOAMAdapter",
    "SU2Adapter",
    "XFOILAdapter",
    "XFLR5Adapter",
]
