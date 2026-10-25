"""
AASI 2.0 Aerospace Software Adapters.
Thin, safe, decoupled adapters for external scientific computing packages:
- RocketPy: Rocket flight dynamics and trajectory simulation
- OpenMDAO: Multidisciplinary design, analysis, and optimization
- SU2: Stanford University Unstructured compressible CFD solver
"""

from .rocketpy_adapter import RocketPyAdapter, RocketTrajectoryResult
from .openmdao_adapter import OpenMDAOAeroComponent, OpenMDAOAdapter
from .su2_adapter import SU2CaseAdapter, SU2RunConfig, SU2ConvergenceReport

__all__ = [
    "RocketPyAdapter",
    "RocketTrajectoryResult",
    "OpenMDAOAeroComponent",
    "OpenMDAOAdapter",
    "SU2CaseAdapter",
    "SU2RunConfig",
    "SU2ConvergenceReport",
]
