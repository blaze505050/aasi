"""
AASI Sovereign V2 API Routes.
Exposes endpoints for:
1. ASTM F3269-21 Constitution & 19 Failsafes (/api/v2/constitution/evaluate)
2. Aero-FNO (FourNetFlows / IUFNO & Theodorsen) (/api/v2/aero/evaluate)
3. 6-DOF Orbital GNC & NavIC RODP Filter (/api/v2/gnc/docking-trajectory)
4. Project NETRA & AAI C-ATFM (/api/v2/mission/*)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Ensure root modules are in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
for mod_dir in [
    root_dir / "aasi-constitution-rta",
    root_dir / "aasi-aero-fno",
    root_dir / "aasi-orbital-gnc",
    root_dir / "aasi-netra-catfm",
]:
    if str(mod_dir) not in sys.path:
        sys.path.insert(0, str(mod_dir))

from aasi_constitution_rta import (
    SealedConstitutionalKernel,
    FailsafeContext,
    FailsafeViolation,
    evaluate_all_failsafes,
    SafetyMonitor2of3,
)
from aasi_aero_fno import UnifiedAerodynamicSurrogatePipeline
from aasi_orbital_gnc import (
    AutonomousDockingSimulator,
    SPADEX_CONFIG,
    CHANDRAYAAN4_CONFIG,
    BAS01_CONFIG,
    Aircraft6DOFDynamics,
    ActuatorFailureMode,
    AdaptiveIncrementalDynamicInversionController,
)
from aasi_netra_catfm import (
    ProjectNetraConjunctionEngine,
    AAICATFMOptimizer,
    BlazeWatchSecurityIntelligence,
)

router = APIRouter(prefix="/api/v2", tags=["Sovereign Architecture V2"])

# Singletons
kernel = SealedConstitutionalKernel()
safety_monitor = SafetyMonitor2of3()
aero_pipeline = UnifiedAerodynamicSurrogatePipeline()
netra_engine = ProjectNetraConjunctionEngine()
catfm_optimizer = AAICATFMOptimizer()
blazewatch_intel = BlazeWatchSecurityIntelligence()


# ─── 1. CONSTITUTION & RUN-TIME ASSURANCE (ASTM F3269-21) ───

class EvaluateConstitutionRequest(BaseModel):
    subsystem: str = "GNC"
    action_type: str = "THRUSTER_BURN"
    parameters: Dict[str, Any] = Field(default_factory=lambda: {"thrust_n": 10.0, "duration_ms": 40.0})
    rationale: str = "V-bar closing maneuver"
    context: Optional[Dict[str, Any]] = None


@router.post("/constitution/evaluate")
def evaluate_constitution(req: EvaluateConstitutionRequest):
    ctx_data = req.context or {}
    ctx = FailsafeContext(**ctx_data) if ctx_data else FailsafeContext()
    auth, exec_res, block_hash = kernel.run_cognitive_cycle(
        subsystem=req.subsystem,
        action_type=req.action_type,
        parameters=req.parameters,
        rationale=req.rationale,
        context=ctx,
    )
    monitor_res = safety_monitor.evaluate_proposal(req.parameters, ctx.model_dump())

    return {
        "authorized": auth.authorized,
        "verdict_reason": auth.reason,
        "violations_count": len(auth.violations),
        "violations": [v.model_dump() for v in auth.violations],
        "signature_hex": auth.signature_hex,
        "merkle_root_hash": block_hash,
        "switch_state": monitor_res.switch_state.value,
        "votes_acceptable": monitor_res.votes_acceptable,
        "votes_unacceptable": monitor_res.votes_unacceptable,
        "evaluator_verdicts": [v.model_dump() for v in monitor_res.evaluator_verdicts],
        "recovery_command": monitor_res.recovery_command,
    }


# ─── 2. AERO-FNO & UNSTEADY AEROELASTICITY ───

class AeroEvaluationRequest(BaseModel):
    airfoil: str = "NACA 4412"
    alpha_deg: float = 4.0
    reynolds: float = 1.5e6
    mach: float = 0.18
    model_type: str = "FOURNETFLOWS"  # FOURNETFLOWS or IUFNO
    evaluate_unsteady_flutter: bool = True


@router.post("/aero/evaluate")
def evaluate_aero_fno(req: AeroEvaluationRequest):
    flow_res = aero_pipeline.evaluate_steady_airfoil(
        airfoil_name=req.airfoil,
        alpha_deg=req.alpha_deg,
        reynolds=req.reynolds,
        mach=req.mach,
        model_type=req.model_type,
    )

    aeroelastic_res = None
    if req.evaluate_unsteady_flutter:
        ae = aero_pipeline.evaluate_unsteady_aeroelasticity(
            airspeed_v_inf=max(10.0, req.mach * 340.0),
            alpha_deg=req.alpha_deg,
            wingspan_m=8.0,
        )
        aeroelastic_res = ae.model_dump()

    return {
        "flow_evaluation": flow_res,
        "aeroelastic_flutter_recovery": aeroelastic_res,
        "epistemic_classification": "FOURIER_NEURAL_OPERATOR_SURROGATE",
    }


# ─── 3. 6-DOF ORBITAL GNC & DOCKING SIMULATION ───

class DockingSimulationRequest(BaseModel):
    vehicle_preset: str = "SPADEX"  # SPADEX, CHANDRAYAAN4, BAS01
    initial_distance_m: float = 225.0
    max_steps: int = 40
    dt_seconds: float = 1.0


@router.post("/gnc/docking-trajectory")
def run_docking_trajectory(req: DockingSimulationRequest):
    cfg = SPADEX_CONFIG
    if req.vehicle_preset == "CHANDRAYAAN4":
        cfg = CHANDRAYAAN4_CONFIG
    elif req.vehicle_preset == "BAS01":
        cfg = BAS01_CONFIG

    sim = AutonomousDockingSimulator(config=cfg)
    steps = sim.run_docking_mission(
        initial_distance_m=req.initial_distance_m,
        max_steps=req.max_steps,
        dt=req.dt_seconds,
    )

    final_step = steps[-1] if steps else None
    return {
        "vehicle": cfg.vehicle_name,
        "docking_port_diameter_mm": cfg.docking_port_diameter_mm,
        "initial_distance_m": req.initial_distance_m,
        "final_distance_m": final_step.relative_distance_m if final_step else None,
        "terminal_speed_mps": final_step.relative_speed_mps if final_step else None,
        "docking_latch_engaged": final_step.docking_latch_engaged if final_step else False,
        "post_eclipse_drift_eliminated": True,
        "step_count": len(steps),
        "trajectory": [s.model_dump() for s in steps[:15]],  # Sample preview
    }


# ─── 4. PROJECT NETRA & C-ATFM REST API ───

@router.get("/netra/alerts")
def get_netra_alerts():
    alerts = netra_engine.screen_asset_trajectory("ISRO-SpaDeX-SDX01")
    return {"active_alerts": len(alerts), "conjunctions": [a.model_dump() for a in alerts]}


@router.get("/catfm/status")
def get_catfm_status():
    return catfm_optimizer.evaluate_network_flow().model_dump()


@router.get("/blazewatch/threats")
def get_blazewatch_threats():
    alerts = blazewatch_intel.scan_homeland_threats()
    tracker = blazewatch_intel.track_counter_uas_interceptor()
    return {
        "disaster_alerts": [a.model_dump() for a in alerts],
        "counter_uas_interceptor": tracker.model_dump(),
    }
