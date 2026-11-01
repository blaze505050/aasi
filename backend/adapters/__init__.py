"""
AASI 2.0 Aerospace Software & Scientific AI Adapters.
Thin, safe, decoupled adapters for external scientific computing packages:
- AeroSandbox: 2D panel methods, 3D VLM, and US Standard Atmosphere
- OpenAeroStruct: Coupled aerostructural analysis & MDO
- RocketPy: Rocket flight dynamics and 3-DOF trajectory simulation
- OpenMDAO: Multidisciplinary design, analysis, and optimization
- SU2: Compressible CFD case synthesis and residual history parsing
- NeuralOperator: Fourier Neural Operator (FNO) continuous surface Cp prediction
- PhysicsNeMo: Navier-Stokes PDE conservation residual verification
- AS-Bench: Autonomous scientific discovery benchmarking
- 1D-AGI: Symbolic physics scaling laws & Buckingham Pi dimensional analysis
"""

from .aerosandbox_adapter import AeroSandboxAdapter, AeroSandboxAirfoilResult, AtmosphereState
from .openaerostruct_adapter import OpenAeroStructAdapter, AeroStructuralInput, AeroStructuralResult
from .rocketpy_adapter import RocketPyAdapter, RocketTrajectoryResult
from .openmdao_adapter import OpenMDAOAeroComponent, OpenMDAOAdapter
from .su2_adapter import SU2CaseAdapter, SU2RunConfig, SU2ConvergenceReport
from .neuraloperator_adapter import NeuralOperatorAdapter, FNOPredictionResult
from .physics_nemo_adapter import PhysicsNeMoAdapter, PinnedFlowfieldResidual
from .as_bench_adapter import ASBenchAdapter, ASBenchScenario, ASBenchScorecard
from .one_d_agi_adapter import OneDAGIAdapter, DimensionlessGroup, SymbolicScalingLaw

__all__ = [
    "AeroSandboxAdapter",
    "AeroSandboxAirfoilResult",
    "AtmosphereState",
    "OpenAeroStructAdapter",
    "AeroStructuralInput",
    "AeroStructuralResult",
    "RocketPyAdapter",
    "RocketTrajectoryResult",
    "OpenMDAOAeroComponent",
    "OpenMDAOAdapter",
    "SU2CaseAdapter",
    "SU2RunConfig",
    "SU2ConvergenceReport",
    "NeuralOperatorAdapter",
    "FNOPredictionResult",
    "PhysicsNeMoAdapter",
    "PinnedFlowfieldResidual",
    "ASBenchAdapter",
    "ASBenchScenario",
    "ASBenchScorecard",
    "OneDAGIAdapter",
    "DimensionlessGroup",
    "SymbolicScalingLaw",
]
