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
from .transonic_transolver import (
    TransonicTransolverEngine,
    TransonicSolverResult,
    TransonicShockMetrics,
    TransonicFlowfieldGrid,
    rankine_hugoniot_normal_shock,
    calculate_cp_critical,
    AGARD_BENCHMARKS,
)
from .turbulence_tbnn import (
    HighReTurbulenceEngine,
    TensorBasisNeuralNetwork,
    BoundaryLayerProfileResult,
    SSTTurbulenceState,
    check_realizability,
    project_to_lumley_triangle,
    compute_turbulent_tensors_and_invariants,
    TURBULENCE_BENCHMARKS,
)
from .equivariant_gnn import (
    SE3EquivariantAirframeGNN,
    EGNNPredictionResult,
    AirframeMesh,
    generate_canonical_airframe_mesh,
    euler_to_rotation_matrix,
    verify_so3_orthonormality,
    AEROSPACE_3D_BENCHMARKS,
)
from .conformal_uncertainty import (
    ConformalAerospaceSafetyEngine,
    ConformalEvaluationResult,
    ConformalCalibrationDeck,
    generate_aerospace_calibration_deck,
    compute_conformal_quantile,
    LatentAerospaceOODDetector,
)
from .hypersonic_aerothermo import (
    HypersonicAerothermoEngine,
    HypersonicAerothermoResult,
    ChemicalCompositionState,
    compute_hypersonic_chemical_equilibrium,
    get_freestream_atmospheric_properties,
    HYPERSONIC_BENCHMARKS,
)
from .fsi_flutter import (
    PKFlutterSolver,
    AeroelasticModeState,
    FlutterVelocityStation,
    FlutterBoundaryResult,
    AEROELASTIC_BENCHMARKS,
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
    "TransonicTransolverEngine",
    "TransonicSolverResult",
    "TransonicShockMetrics",
    "TransonicFlowfieldGrid",
    "rankine_hugoniot_normal_shock",
    "calculate_cp_critical",
    "AGARD_BENCHMARKS",
    "HighReTurbulenceEngine",
    "TensorBasisNeuralNetwork",
    "BoundaryLayerProfileResult",
    "SSTTurbulenceState",
    "check_realizability",
    "project_to_lumley_triangle",
    "compute_turbulent_tensors_and_invariants",
    "TURBULENCE_BENCHMARKS",
    "SE3EquivariantAirframeGNN",
    "EGNNPredictionResult",
    "AirframeMesh",
    "generate_canonical_airframe_mesh",
    "euler_to_rotation_matrix",
    "verify_so3_orthonormality",
    "AEROSPACE_3D_BENCHMARKS",
    "ConformalAerospaceSafetyEngine",
    "ConformalEvaluationResult",
    "ConformalCalibrationDeck",
    "generate_aerospace_calibration_deck",
    "compute_conformal_quantile",
    "LatentAerospaceOODDetector",
    "HypersonicAerothermoEngine",
    "HypersonicAerothermoResult",
    "ChemicalCompositionState",
    "compute_hypersonic_chemical_equilibrium",
    "get_freestream_atmospheric_properties",
    "HYPERSONIC_BENCHMARKS",
    "PKFlutterSolver",
    "AeroelasticModeState",
    "FlutterVelocityStation",
    "FlutterBoundaryResult",
    "AEROELASTIC_BENCHMARKS",
    "UnifiedAerodynamicSurrogatePipeline",
]

