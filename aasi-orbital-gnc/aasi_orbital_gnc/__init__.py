"""
AASI Orbital GNC & Fault-Tolerant Flight Control Package.
Implements:
- 6-DOF Reinforcement Meta-Learning orbital docking simulator (SpaDeX, Chandrayaan-4, BAS-01)
- NavIC RODP + ISL sensor fusion filter eliminating the 225m post-eclipse drift anomaly
- 5-tier proximity sensor handoff (LRF, ISL, Rendezvous, Optical, BDS entry)
- Nonlinear fault-tolerant aircraft control (F-16, B747) under surface locks and icing
"""

from .orbital_dynamics import (
    OrbitalVehicleConfig,
    OrbitalState6DOF,
    RelativeOrbitalDynamics6DOF,
    SPADEX_CONFIG,
    CHANDRAYAAN4_CONFIG,
    BAS01_CONFIG,
)
from .meta_rl_docking import (
    MetaRLDockingPolicy,
    DockingStepResult,
    AutonomousDockingSimulator,
)
from .navic_rodp_filter import (
    NavICRODPSensorFusionFilter,
    SensorMeasurements5Tier,
    SensorTier,
)
from .aircraft_fault_control import (
    Aircraft6DOFDynamics,
    ActuatorFailureMode,
    AdaptiveIncrementalDynamicInversionController,
    AircraftSimulationStep,
)

__all__ = [
    "OrbitalVehicleConfig",
    "OrbitalState6DOF",
    "RelativeOrbitalDynamics6DOF",
    "SPADEX_CONFIG",
    "CHANDRAYAAN4_CONFIG",
    "BAS01_CONFIG",
    "MetaRLDockingPolicy",
    "DockingStepResult",
    "AutonomousDockingSimulator",
    "NavICRODPSensorFusionFilter",
    "SensorMeasurements5Tier",
    "SensorTier",
    "Aircraft6DOFDynamics",
    "ActuatorFailureMode",
    "AdaptiveIncrementalDynamicInversionController",
    "AircraftSimulationStep",
]
