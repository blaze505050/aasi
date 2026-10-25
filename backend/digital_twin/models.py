"""
AASI 2.0 Aerospace Digital Twin Data Contracts & Telemetry Schema.

Defines verifiable state vectors, high-rate telemetry frames, fault-injection
specifications, safety envelopes, and provenance hashing for:
- Multi-Stage Orbital Rocket
- Autonomous Drone & Hybrid eVTOL
- Commercial / Tactical Aeroplane
- Low Earth Orbit (LEO) Satellite
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VehicleType(str, Enum):
    ROCKET = "ROCKET"
    DRONE = "DRONE"
    AEROPLANE = "AEROPLANE"
    SATELLITE = "SATELLITE"


class SimulationMode(str, Enum):
    NOMINAL = "NOMINAL"
    FAULT_INJECTION = "FAULT_INJECTION"
    ENVELOPE_STRESS = "ENVELOPE_STRESS"


class FaultType(str, Enum):
    # Rocket Faults
    ENGINE_SHUTDOWN_EARLY = "ENGINE_SHUTDOWN_EARLY"
    GIMBAL_ACTUATOR_LOCK = "GIMBAL_ACTUATOR_LOCK"
    TURBOPUMP_PRESSURE_DROP = "TURBOPUMP_PRESSURE_DROP"
    # Drone Faults
    MOTOR_FAILURE = "MOTOR_FAILURE"
    BATTERY_CELL_COLLAPSE = "BATTERY_CELL_COLLAPSE"
    SEVERE_WIND_GUST = "SEVERE_WIND_GUST"
    # Aeroplane Faults
    ONE_ENGINE_INOPERATIVE = "ONE_ENGINE_INOPERATIVE"
    PITOT_TUBE_ICING = "PITOT_TUBE_ICING"
    TRIM_RUNAWAY = "TRIM_RUNAWAY"
    # Satellite Faults
    SOLAR_PANEL_DEGRADATION = "SOLAR_PANEL_DEGRADATION"
    REACTION_WHEEL_DESAT = "REACTION_WHEEL_DESAT"
    ATMOSPHERIC_DRAG_SURGE = "ATMOSPHERIC_DRAG_SURGE"


class FaultInjectionConfig(BaseModel):
    """Fault injection scenario parameters."""
    target_vehicle: Optional[VehicleType] = None
    fault_type: FaultType
    onset_time_s: float = Field(..., description="Timestamp in seconds when the fault triggers", ge=0.0)
    severity: float = Field(0.8, description="Fault severity magnitude from 0.0 to 1.0", ge=0.0, le=1.0)
    subsystem_target: str = Field("propulsion", description="Target subsystem name")


class MissionEvent(BaseModel):
    """Discrete milestone or alert event during simulation."""
    timestamp_s: float
    event_name: str
    description: str
    severity: str = "INFO"  # "INFO", "WARNING", "CRITICAL"


class TelemetryFrame(BaseModel):
    """High-frequency synchronized telemetry sample frame."""
    timestamp_s: float
    altitude_m: float
    velocity_ms: float
    mach: float
    dynamic_pressure_pa: float
    acceleration_g: float
    mass_kg: float
    propellant_or_battery_pct: float
    temperature_c: float
    subsystem_health: Dict[str, float] = Field(default_factory=dict)
    vehicle_specific: Dict[str, Any] = Field(default_factory=dict)


class DigitalTwinSimulationResult(BaseModel):
    """Comprehensive digital twin simulation output package."""
    simulation_id: str
    vehicle_type: VehicleType
    vehicle_name: str
    simulation_mode: SimulationMode
    duration_s: float
    time_step_s: float
    total_samples: int
    frames: List[TelemetryFrame]
    events: List[MissionEvent]
    summary_metrics: Dict[str, Any]
    safety_envelope_passed: bool
    safety_violations: List[str]
    provenance_hash: str

    @classmethod
    def compute_provenance(cls, payload: Dict[str, Any]) -> str:
        s = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
