"""
AASI Aero-FNO Package.
Implements the high-speed PyTorch aerodynamic surrogate pipeline:
- FourNetFlows with Conv1d boundary lifting
- Geo-FNO with learned mesh deformation
- IUFNO with implicit Fourier layers and U-Net skip connections
- DLR Theodorsen unsteady aeroelastic modal force recovery
"""

from .fournetflows import FourNetFlowsModel, SpectralConv2d
from .geo_fno import GeoFNOAirfoilModel, MeshDeformationNetwork
from .iufno import IUFNOModel, ImplicitFourierLayer, UNetSkipBlock
from .theodorsen_aeroelasticity import (
    TheodorsenAeroelasticSolver,
    AeroelasticState,
    AeroelasticModalResult,
)
from .pipeline import UnifiedAerodynamicSurrogatePipeline

__all__ = [
    "FourNetFlowsModel",
    "SpectralConv2d",
    "GeoFNOAirfoilModel",
    "MeshDeformationNetwork",
    "IUFNOModel",
    "ImplicitFourierLayer",
    "UNetSkipBlock",
    "TheodorsenAeroelasticSolver",
    "AeroelasticState",
    "AeroelasticModalResult",
    "UnifiedAerodynamicSurrogatePipeline",
]
