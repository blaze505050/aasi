"""
AASI 2.0 Unified Aerospace Digital Twin Orchestrator.

Orchestrates multi-domain digital twins across:
- Rocket (Multi-stage ascent, gravity turn, thermal loads, orbital insertion)
- Drone / eVTOL (BEMT rotor aerodynamics, LiPo ECM, motor thermal rise)
- Aeroplane (3D aero polar, TSFC Breguet range, V-n envelope, OEI trim)
- Satellite (J2 Keplerian propagation, LEO drag decay, eclipse power & thermals)

Provides deterministic fault-injection campaigns, safety envelope evaluation,
and cryptographic SHA-256 result provenance.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.digital_twin.models import (
    VehicleType,
    SimulationMode,
    FaultType,
    FaultInjectionConfig,
    DigitalTwinSimulationResult,
)
from backend.digital_twin.rocket_twin import RocketDigitalTwin, RocketDigitalTwinConfig
from backend.digital_twin.drone_twin import DroneDigitalTwin, DroneDigitalTwinConfig
from backend.digital_twin.aeroplane_twin import AeroplaneDigitalTwin, AeroplaneDigitalTwinConfig
from backend.digital_twin.satellite_twin import SatelliteDigitalTwin, SatelliteDigitalTwinConfig

logger = logging.getLogger("aasi.digital_twin")


class DigitalTwinCatalogItem(BaseModel):
    vehicle_type: VehicleType
    display_name: str
    category: str
    description: str
    default_config: Dict[str, Any]
    supported_faults: List[str]
    governing_physics: List[str]
    industry_standards: List[str]


class DigitalTwinOrchestrator:
    """
    Central dispatch and coordination point for all AASI Digital Twin simulations.
    """

    @classmethod
    def get_vehicle_catalog(cls) -> List[DigitalTwinCatalogItem]:
        """Returns catalog of all supported aerospace digital twin vehicles."""
        return [
            DigitalTwinCatalogItem(
                vehicle_type=VehicleType.ROCKET,
                display_name="Orbital Heavy-Lift Launch Vehicle",
                category="Launch Systems & Space Access",
                description="2-stage cryogenic/kerolox orbital launch vehicle with supersonic staging, US Standard Atmosphere 1976, Max-Q dynamic pressure peak, and orbital insertion.",
                default_config=RocketDigitalTwinConfig().model_dump(),
                supported_faults=[
                    FaultType.ENGINE_SHUTDOWN_EARLY.value,
                    FaultType.GIMBAL_ACTUATOR_LOCK.value,
                    FaultType.TURBOPUMP_PRESSURE_DROP.value,
                ],
                governing_physics=[
                    "Tsiolkovsky Multi-Stage Depletion",
                    "Gravity Turn ODE Integration",
                    "Transonic Wave Drag Rise CD(M)",
                    "Fay-Riddell Aero-Thermal Stagnation Heating",
                    "Keplerian Orbital Insertion Elements",
                ],
                industry_standards=["NASA-STD-7009B", "FAA 14 CFR Part 450", "AIAA S-110-2005"],
            ),
            DigitalTwinCatalogItem(
                vehicle_type=VehicleType.DRONE,
                display_name="Hexacopter & Hybrid eVTOL Airframe",
                category="Autonomous UAVs & Urban Air Mobility",
                description="Heavy-payload 6-rotor autonomous UAV with Blade Element Momentum Theory (BEMT), Cheeseman-Bennett In-Ground-Effect (IGE), and LiPo ECM voltage sag dynamics.",
                default_config=DroneDigitalTwinConfig().model_dump(),
                supported_faults=[
                    FaultType.MOTOR_FAILURE.value,
                    FaultType.BATTERY_CELL_COLLAPSE.value,
                    FaultType.SEVERE_WIND_GUST.value,
                ],
                governing_physics=[
                    "Blade Element Momentum Theory (BEMT)",
                    "Cheeseman-Bennett In-Ground-Effect (IGE)",
                    "Battery Equivalent Circuit Model (ECM)",
                    "Brushless Motor Electro-Thermal Heating",
                    "Dryden Wind Turbulence Model",
                ],
                industry_standards=["ASTM F3322-18", "RTCA DO-178C", "FAA Part 107"],
            ),
            DigitalTwinCatalogItem(
                vehicle_type=VehicleType.AEROPLANE,
                display_name="Twin-Turbofan Commercial Air Transport",
                category="Commercial & Tactical Aviation",
                description="Twin-turbofan transport aircraft simulating 3D compressible drag polar with Korn drag divergence, high-bypass turbofan TSFC fuel flow, and Breguet range.",
                default_config=AeroplaneDigitalTwinConfig().model_dump(),
                supported_faults=[
                    FaultType.ONE_ENGINE_INOPERATIVE.value,
                    FaultType.PITOT_TUBE_ICING.value,
                    FaultType.TRIM_RUNAWAY.value,
                ],
                governing_physics=[
                    "3D Vortex Drag Polar + Transonic Wave Drag",
                    "High-Bypass Turbofan Thrust Lapse & TSFC",
                    "Breguet Payload-Range Profile (FL370)",
                    "V-n Structural Limit Maneuver Envelope",
                    "One-Engine Inoperative (OEI) Asymmetric Trim",
                ],
                industry_standards=["FAR Part 25 (Transport Category)", "ICAO Annex 16", "MIL-STD-1797A"],
            ),
            DigitalTwinCatalogItem(
                vehicle_type=VehicleType.SATELLITE,
                display_name="Sun-Synchronous LEO Observation Satellite",
                category="Spacecraft & Earth Observation",
                description="Low Earth Orbit spacecraft simulating Earth oblateness J2 nodal precession, Harris-Priester upper atmosphere drag decay lifetime, solar array/battery eclipse cycles, and thermal balance.",
                default_config=SatelliteDigitalTwinConfig().model_dump(),
                supported_faults=[
                    FaultType.SOLAR_PANEL_DEGRADATION.value,
                    FaultType.REACTION_WHEEL_DESAT.value,
                    FaultType.ATMOSPHERIC_DRAG_SURGE.value,
                ],
                governing_physics=[
                    "Keplerian Orbit Propagation with J2 Perturbation",
                    "Harris-Priester Scale-Height Thermospheric Drag",
                    "Cylindrical Earth Umbra/Penumbra Eclipse Geometry",
                    "GaAs Triple-Junction Solar Cell Degradation",
                    "Stefan-Boltzmann 4th-Power Thermal Equilibrium",
                ],
                industry_standards=["ECSS-E-ST-10-04C", "NASA-STD-8719.14", "ISO 24113 (Debris Mitigation)"],
            ),
        ]

    @classmethod
    def run_simulation(
        cls,
        vehicle_type: VehicleType,
        custom_config: Optional[Dict[str, Any]] = None,
        fault: Optional[FaultInjectionConfig] = None,
    ) -> DigitalTwinSimulationResult:
        """Executes high-fidelity digital twin simulation for the requested vehicle."""
        logger.info(f"Executing digital twin simulation: vehicle={vehicle_type.value}, fault={fault.fault_type if fault else 'NONE'}")

        if vehicle_type == VehicleType.ROCKET:
            cfg = RocketDigitalTwinConfig(**custom_config) if custom_config else RocketDigitalTwinConfig()
            return RocketDigitalTwin.simulate(cfg, fault)

        elif vehicle_type == VehicleType.DRONE:
            cfg = DroneDigitalTwinConfig(**custom_config) if custom_config else DroneDigitalTwinConfig()
            return DroneDigitalTwin.simulate(cfg, fault)

        elif vehicle_type == VehicleType.AEROPLANE:
            cfg = AeroplaneDigitalTwinConfig(**custom_config) if custom_config else AeroplaneDigitalTwinConfig()
            return AeroplaneDigitalTwin.simulate(cfg, fault)

        elif vehicle_type == VehicleType.SATELLITE:
            cfg = SatelliteDigitalTwinConfig(**custom_config) if custom_config else SatelliteDigitalTwinConfig()
            return SatelliteDigitalTwin.simulate(cfg, fault)

        else:
            raise ValueError(f"Unsupported vehicle type: {vehicle_type}")
