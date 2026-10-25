"""
AASI 2.0 Aerospace Digital Twin REST Endpoints.

Exposes real-time high-fidelity physics simulations and fault injection campaigns for:
- Multi-Stage Orbital Rocket
- Autonomous Drone / Hexacopter & Hybrid eVTOL
- Commercial / Tactical Aeroplane
- Low Earth Orbit (LEO) Satellite
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.digital_twin.models import (
    VehicleType,
    SimulationMode,
    FaultType,
    FaultInjectionConfig,
    DigitalTwinSimulationResult,
)
from backend.digital_twin.twin_orchestrator import DigitalTwinOrchestrator, DigitalTwinCatalogItem
from backend.digital_twin.rocket_twin import RocketDigitalTwinConfig
from backend.digital_twin.drone_twin import DroneDigitalTwinConfig
from backend.digital_twin.aeroplane_twin import AeroplaneDigitalTwinConfig
from backend.digital_twin.satellite_twin import SatelliteDigitalTwinConfig

logger = logging.getLogger("aasi.api.digital_twin")

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])


class SimulationRequest(BaseModel):
    vehicle_type: VehicleType = Field(..., description="Target vehicle type (ROCKET, DRONE, AEROPLANE, SATELLITE)")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Custom vehicle engineering parameters")
    fault: Optional[FaultInjectionConfig] = Field(None, description="Optional fault-injection scenario")


class FaultTestRequest(BaseModel):
    vehicle_type: VehicleType
    fault_type: FaultType
    onset_time_s: float = 60.0
    severity: float = 0.8
    subsystem_target: str = "propulsion"


@router.get("/catalog", response_model=List[DigitalTwinCatalogItem])
async def get_digital_twin_catalog() -> List[DigitalTwinCatalogItem]:
    """Returns specifications, governing physics, and fault modes for all digital twin vehicles."""
    return DigitalTwinOrchestrator.get_vehicle_catalog()


@router.post("/simulate", response_model=DigitalTwinSimulationResult)
async def simulate_digital_twin(request: SimulationRequest) -> DigitalTwinSimulationResult:
    """Runs a complete high-fidelity digital twin simulation with deterministic provenance."""
    try:
        return DigitalTwinOrchestrator.run_simulation(
            vehicle_type=request.vehicle_type,
            custom_config=request.custom_config,
            fault=request.fault,
        )
    except Exception as exc:
        logger.exception("Error executing digital twin simulation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(exc)}",
        )


@router.post("/rocket/simulate", response_model=DigitalTwinSimulationResult)
async def simulate_rocket(
    config: Optional[RocketDigitalTwinConfig] = None,
    fault: Optional[FaultInjectionConfig] = None,
) -> DigitalTwinSimulationResult:
    """Runs multi-stage rocket ascent and orbital insertion simulation."""
    try:
        custom_dict = config.model_dump() if config else None
        return DigitalTwinOrchestrator.run_simulation(
            vehicle_type=VehicleType.ROCKET,
            custom_config=custom_dict,
            fault=fault,
        )
    except Exception as exc:
        logger.exception("Rocket simulation error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/drone/simulate", response_model=DigitalTwinSimulationResult)
async def simulate_drone(
    config: Optional[DroneDigitalTwinConfig] = None,
    fault: Optional[FaultInjectionConfig] = None,
) -> DigitalTwinSimulationResult:
    """Runs drone / eVTOL BEMT rotor dynamics and battery ECM simulation."""
    try:
        custom_dict = config.model_dump() if config else None
        return DigitalTwinOrchestrator.run_simulation(
            vehicle_type=VehicleType.DRONE,
            custom_config=custom_dict,
            fault=fault,
        )
    except Exception as exc:
        logger.exception("Drone simulation error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/aeroplane/simulate", response_model=DigitalTwinSimulationResult)
async def simulate_aeroplane(
    config: Optional[AeroplaneDigitalTwinConfig] = None,
    fault: Optional[FaultInjectionConfig] = None,
) -> DigitalTwinSimulationResult:
    """Runs commercial transport aircraft 3D drag polar and Breguet range simulation."""
    try:
        custom_dict = config.model_dump() if config else None
        return DigitalTwinOrchestrator.run_simulation(
            vehicle_type=VehicleType.AEROPLANE,
            custom_config=custom_dict,
            fault=fault,
        )
    except Exception as exc:
        logger.exception("Aeroplane simulation error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/satellite/simulate", response_model=DigitalTwinSimulationResult)
async def simulate_satellite(
    config: Optional[SatelliteDigitalTwinConfig] = None,
    fault: Optional[FaultInjectionConfig] = None,
) -> DigitalTwinSimulationResult:
    """Runs LEO satellite J2 perturbation, eclipse power, and drag decay simulation."""
    try:
        custom_dict = config.model_dump() if config else None
        return DigitalTwinOrchestrator.run_simulation(
            vehicle_type=VehicleType.SATELLITE,
            custom_config=custom_dict,
            fault=fault,
        )
    except Exception as exc:
        logger.exception("Satellite simulation error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/fault-injection", response_model=DigitalTwinSimulationResult)
async def run_fault_injection_campaign(request: FaultTestRequest) -> DigitalTwinSimulationResult:
    """Executes a stressed envelope fault-injection scenario to evaluate airworthiness resilience."""
    try:
        fault_cfg = FaultInjectionConfig(
            target_vehicle=request.vehicle_type,
            fault_type=request.fault_type,
            onset_time_s=request.onset_time_s,
            severity=request.severity,
            subsystem_target=request.subsystem_target,
        )
        return DigitalTwinOrchestrator.run_simulation(
            vehicle_type=request.vehicle_type,
            fault=fault_cfg,
        )
    except Exception as exc:
        logger.exception("Fault-injection campaign error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
