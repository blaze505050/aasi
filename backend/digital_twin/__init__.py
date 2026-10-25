"""
AASI 2.0 Aerospace Digital Twin Engine.
High-fidelity deterministic digital twins for Rocket, Drone, Aeroplane, and Satellite.
"""

from backend.digital_twin.models import (
    VehicleType,
    SimulationMode,
    FaultType,
    FaultInjectionConfig,
    TelemetryFrame,
    MissionEvent,
    DigitalTwinSimulationResult,
)
from backend.digital_twin.rocket_twin import RocketDigitalTwin, RocketDigitalTwinConfig
from backend.digital_twin.drone_twin import DroneDigitalTwin, DroneDigitalTwinConfig
from backend.digital_twin.aeroplane_twin import AeroplaneDigitalTwin, AeroplaneDigitalTwinConfig
from backend.digital_twin.satellite_twin import SatelliteDigitalTwin, SatelliteDigitalTwinConfig
from backend.digital_twin.twin_orchestrator import DigitalTwinOrchestrator, DigitalTwinCatalogItem

__all__ = [
    "VehicleType",
    "SimulationMode",
    "FaultType",
    "FaultInjectionConfig",
    "TelemetryFrame",
    "MissionEvent",
    "DigitalTwinSimulationResult",
    "RocketDigitalTwin",
    "RocketDigitalTwinConfig",
    "DroneDigitalTwin",
    "DroneDigitalTwinConfig",
    "AeroplaneDigitalTwin",
    "AeroplaneDigitalTwinConfig",
    "SatelliteDigitalTwin",
    "SatelliteDigitalTwinConfig",
    "DigitalTwinOrchestrator",
    "DigitalTwinCatalogItem",
]
