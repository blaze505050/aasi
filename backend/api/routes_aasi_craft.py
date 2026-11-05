"""
AASI-Craft API Router.
Exposes endpoints for the 4-step reverse-engineering and verification loop:
- /api/v2/craft/study
- /api/v2/craft/build
- /api/v2/craft/check
- /api/v2/craft/ready
- /api/v2/craft/pipeline
- /api/v2/craft/presets
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

root_dir = Path(__file__).resolve().parent.parent.parent
for mod_name in ["aasi-craft", "aasi-orbital-gnc", "aasi-aero-fno", "aasi-constitution-rta"]:
    mod_path = root_dir / mod_name
    if str(mod_path) not in sys.path:
        sys.path.insert(0, str(mod_path))

from aasi_craft.evidence_dossier import EvidenceDossier
from aasi_craft.parsers.polar_parser import AirfoilPolarParser
from aasi_craft.parsers.telemetry_parser import CcsdsTelemetryParser
from aasi_craft.synthesis.clean_room_synthesizer import CleanRoomSynthesizer
from aasi_craft.verification.asme_vv20 import AsmeVv20Verifier
from aasi_craft.assurance.rta_packager import RtaAirworthinessPackager
from aasi_craft.cad.geometry_engine import CadGeometryEngine
from aasi_craft.mesher.automated_mesher import AutomatedMesher
from aasi_craft.exporters.autopilot_exporter import AutopilotHardwareExporter
from aasi_orbital_gnc.hil_bridge import HilFlightBridge
from aasi_aero_fno.adaskip_tmr import TmrRadiationExecutive
from aasi_craft.flagship_workflow import (
    run_naca4412_surrogate_pipeline,
    run_spadex_eclipse_docking_pipeline,
    NACA_4412_EXPERIMENTAL_POLAR,
)

# Global HIL singleton bridge
hil_bridge_singleton = HilFlightBridge()
tmr_exec_singleton = TmrRadiationExecutive()

router = APIRouter(prefix="/api/v2/craft", tags=["AASI-Craft Reverse Engineering"])


class StudyRequest(BaseModel):
    preset: str = Field(default="naca4412", description="Built-in preset: naca4412, spadex")
    file_content: Optional[str] = None
    target_name: Optional[str] = None


class CheckRequest(BaseModel):
    f1_fine: float = Field(default=1.670, description="Fine grid metric value")
    f2_medium: float = Field(default=1.658, description="Medium grid metric value")
    f3_coarse: float = Field(default=1.625, description="Coarse grid metric value")
    refinement_ratio: float = Field(default=2.0, ge=1.1, description="Grid refinement ratio")
    metric_name: str = Field(default="CL_max", description="Target metric name")


class ReadyRequest(BaseModel):
    target_name: str = "NACA_4412"
    merkle_root: str
    is_asme_vv20_verified: bool = True
    action_type: str = "DEPLOY_TO_FLIGHT_COMPUTER"
    summary: str = "Authorize deployment of verified surrogate model"
    auto_approve: bool = True


class PipelineRequest(BaseModel):
    preset: str = Field(default="naca4412", description="naca4412 or spadex")
    auto_approve: bool = Field(default=True, description="Auto-approve RTA flight safety cards")


@router.get("/presets")
def get_flagship_presets() -> Dict[str, Any]:
    """Returns available flagship aerospace reverse-engineering presets."""
    return {
        "presets": [
            {
                "id": "naca4412",
                "title": "NACA 4412 Transonic Aerodynamic Surrogate",
                "domain": "Aerodynamics & CFD",
                "description": "Clean-room FourNetFlows surrogate synthesis from NASA LTPT wind tunnel polar. ASME V&V 20 3-grid Richardson verification.",
                "target_type": "WIND_TUNNEL_POLAR",
                "status": "READY_FOR_STUDY",
            },
            {
                "id": "spadex",
                "title": "ISRO SpaDeX-2 / BAS-01 Rendezvous Sensor Fusion",
                "domain": "Orbital GNC & Space Missions",
                "description": "CCSDS Blue Book telemetry ingestion and NavIC+ISL filter synthesis. Eliminates 225m post-eclipse drift anomaly.",
                "target_type": "TELEMETRY_STREAM",
                "status": "READY_FOR_STUDY",
            },
            {
                "id": "catfm_monsoon",
                "title": "AAI C-ATFM Monsoon Network Flow Optimizer",
                "domain": "National Airspace Systems",
                "description": "Ingests Mumbai FIR radar convective squalls and calculates fuel-optimal Ground Delay Programs.",
                "target_type": "AIRSPACE_SCHEDULE",
                "status": "READY_FOR_STUDY",
            },
            {
                "id": "netra_debris",
                "title": "Project NETRA Orbital Conjunction & CAM Burn",
                "domain": "Space Situational Awareness",
                "description": "Multi-radar track ingestion, Foster 2D collision probability calculation, and optimal delta-v maneuver planning.",
                "target_type": "RADAR_TRACK",
                "status": "READY_FOR_STUDY",
            },
        ]
    }


@router.post("/study")
def post_study(req: StudyRequest) -> Dict[str, Any]:
    """Executes deterministic study phase on target polar or stream."""
    if req.preset.lower() == "naca4412":
        content = req.file_content or NACA_4412_EXPERIMENTAL_POLAR
        dossier = AirfoilPolarParser.parse_csv_stream(content, airfoil_name=req.target_name or "NACA_4412")
        return dossier.to_dict()
    elif req.preset.lower() == "spadex":
        # Create representative packet stream
        stream = bytearray()
        for i in range(10):
            pkt = CcsdsTelemetryParser.create_ccsds_packet(
                apid=0x042A,
                seq_count=i,
                timestamp_s=float(i * 10),
                pos_xyz=(100.0 - i * 9.0, 0.0, 0.0),
                vel_xyz=(-0.12, 0.0, 0.0),
                quat_wxyz=(1.0, 0.0, 0.0, 0.0),
            )
            stream.extend(pkt)
        dossier = CcsdsTelemetryParser.parse_telemetry_stream(bytes(stream), stream_name="SPADEX_2_TLM")
        return dossier.to_dict()
    raise HTTPException(status_code=400, detail=f"Unsupported preset: {req.preset}")


@router.post("/check")
def post_check(req: CheckRequest) -> Dict[str, Any]:
    """Executes ASME V&V 20 Richardson GCI calculation."""
    report = AsmeVv20Verifier.evaluate_3grid_richardson(
        f1=req.f1_fine,
        f2=req.f2_medium,
        f3=req.f3_coarse,
        r21=req.refinement_ratio,
        r32=req.refinement_ratio,
        metric_name=req.metric_name,
    )
    return report.to_dict()


@router.post("/ready")
def post_ready(req: ReadyRequest) -> Dict[str, Any]:
    """Executes ASTM F3269-21 RTA packaging, human safety card, and Ed25519 signing."""
    packager = RtaAirworthinessPackager()
    card = packager.generate_approval_card(
        action_type=req.action_type,
        target_system=req.target_name,
        plain_summary=req.summary,
        load_factor_g=1.0,
    )
    if req.auto_approve:
        card.approve("FLIGHT_OPERATIONS_DIRECTOR")

    pkg = packager.package_flight_release(
        target_name=req.target_name,
        merkle_root=req.merkle_root,
        is_asme_vv20_verified=req.is_asme_vv20_verified,
        approved_cards=[card],
    )
    return pkg.to_dict()


@router.post("/pipeline")
def post_pipeline(req: PipelineRequest) -> Dict[str, Any]:
    """Executes the complete 4-step loop end-to-end."""
    if req.preset.lower() in ["naca4412", "aero"]:
        return run_naca4412_surrogate_pipeline(auto_approve=req.auto_approve)
    elif req.preset.lower() in ["spadex", "orbital"]:
        return run_spadex_eclipse_docking_pipeline(auto_approve=req.auto_approve)
    raise HTTPException(status_code=400, detail=f"Unsupported pipeline preset: {req.preset}")


# ─── CAD, MESHING, HIL & SPACEBORNE EDGE EXTENSIONS ───

class CadInspectRequest(BaseModel):
    name: str = "TRIBAL_TACTICAL_UAV"
    raw_ascii_stl: Optional[str] = None
    use_preset_uav: bool = True


class MesherRequest(BaseModel):
    geometry_name: str = "TRIBAL_TACTICAL_UAV"
    chord_m: float = 1.0
    u_inf_mps: float = 60.0
    target_y_plus: float = 0.95
    grid_ratio: float = 1.414


class HilStepRequest(BaseModel):
    dt_sec: float = 0.01


class HilInjectFaultRequest(BaseModel):
    fault_mode: str = Field(default="ACTUATOR_JAM_AILERON", description="ACTUATOR_JAM_AILERON, ACTUATOR_FLOAT_RUDDER, ORBITAL_ECLIPSE_GNSS_OUTAGE, SAA_COSMIC_SEU, NOMINAL")


class TmrEvaluateRequest(BaseModel):
    alpha_deg: float = 4.0
    inject_seu_channel: Optional[int] = None


class AutopilotExportRequest(BaseModel):
    airframe_name: str = "TRIBAL_TACTICAL_UAV"
    mass_kg: float = 12.5
    span_m: float = 2.4
    chord_m: float = 0.35
    v_cruise_mps: float = 24.0
    cl_alpha: float = 5.85
    cm_alpha: float = -0.62


@router.post("/cad/inspect-stl")
def post_inspect_stl(req: CadInspectRequest) -> Dict[str, Any]:
    """Parses 3D surface STL, calculates MAC, planform area, aspect ratio, and sweep."""
    if req.raw_ascii_stl:
        metrics = CadGeometryEngine.parse_stl_ascii(req.raw_ascii_stl, name=req.name)
    else:
        sample_bytes = CadGeometryEngine.generate_sample_uav_wing_stl()
        metrics = CadGeometryEngine.parse_stl_binary(sample_bytes, name=req.name)
    return metrics.to_dict()


@router.post("/mesher/generate-asme-grid")
def post_generate_asme_grid(req: MesherRequest) -> Dict[str, Any]:
    """Synthesizes ASME V&V 20 3-level grid hierarchy with prism inflation (y+ < 1.0)."""
    hierarchy = AutomatedMesher.generate_asme_vv20_grid_hierarchy(
        geometry_name=req.geometry_name,
        base_chord_m=req.chord_m,
        u_inf=req.u_inf_mps,
        grid_refinement_ratio=req.grid_ratio,
    )
    return hierarchy.to_dict()


@router.post("/hil/step-telemetry")
def post_hil_step(req: HilStepRequest) -> Dict[str, Any]:
    """Steps the real-time 100 Hz Hardware-in-the-Loop simulation cycle."""
    frame = hil_bridge_singleton.step_simulation_cycle(dt=req.dt_sec)
    return frame.to_dict()


@router.post("/hil/inject-failure")
def post_hil_inject_failure(req: HilInjectFaultRequest) -> Dict[str, Any]:
    """Injects or clears flight hardware fault into the active HIL bridge."""
    status_msg = hil_bridge_singleton.inject_failure(req.fault_mode)
    return {"status": status_msg, "active_fault": hil_bridge_singleton.active_fault}


@router.post("/space/tmr-evaluate")
def post_tmr_evaluate(req: TmrEvaluateRequest) -> Dict[str, Any]:
    """Executes on-orbit Triple Modular Redundancy (TMR) evaluation with AdaSkip pruning."""
    res = tmr_exec_singleton.evaluate_with_tmr(
        alpha_deg=req.alpha_deg,
        inject_seu_channel=req.inject_seu_channel
    )
    return res.to_dict()


@router.post("/export/autopilot")
def post_export_autopilot(req: AutopilotExportRequest) -> Dict[str, Any]:
    """Synthesizes ready-to-flash ArduPilot .param and PX4 mixer configurations."""
    pkg = AutopilotHardwareExporter.generate_autopilot_package(
        airframe_name=req.airframe_name,
        mass_kg=req.mass_kg,
        span_m=req.span_m,
        chord_m=req.chord_m,
        v_cruise_mps=req.v_cruise_mps,
        cl_alpha=req.cl_alpha,
        cm_alpha=req.cm_alpha,
    )
    return pkg.to_dict()


