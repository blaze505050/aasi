"""AASI Physics AI & Neural Surrogate Modeling Subsystem (Phase 4 Foundation).

Defines standard interfaces for Physics-Informed Neural Networks (PINNs),
Fourier Neural Operators (FNO), Graph Neural Networks (GNNs), and PhysicsNeMo surrogates.
"""

from .models import (
    PhysicsModelType,
    PhysicsModelMetadata,
    BasePhysicsSurrogateModel,
    PINNModel,
    PINOModel,
    FNOModel,
    GNNModel,
    DoMINOModel,
    MeshGraphNetModel,
    AeroGraphNetModel,
    PhysicsNeMoModel,
)
from .dimensional import AerodynamicDimensionalizer, DimensionlessFlowState
from .constraints import AerodynamicConstraintEngine, PhysicalConstraintReport

__all__ = [
    "PhysicsModelType",
    "PhysicsModelMetadata",
    "BasePhysicsSurrogateModel",
    "PINNModel",
    "PINOModel",
    "FNOModel",
    "GNNModel",
    "DoMINOModel",
    "MeshGraphNetModel",
    "AeroGraphNetModel",
    "PhysicsNeMoModel",
    "AerodynamicDimensionalizer",
    "DimensionlessFlowState",
    "AerodynamicConstraintEngine",
    "PhysicalConstraintReport",
]

