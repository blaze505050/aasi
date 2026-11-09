"""
AASI Phase 27: Control Plane Modular API Routers.
Combines authentication, compute providers, persistent jobs, dataset storage,
scientific investigation, result verification, and observability.
"""

from fastapi import APIRouter

from backend.api.routes_auth import router as auth_router
from backend.api.routes_compute import router as compute_router
from backend.api.routes_dataset import router as dataset_router
from backend.api.routes_investigation import router as investigation_router
from backend.api.routes_jobs import router as jobs_router
from backend.api.routes_results import router as results_router
from backend.api.routes_observability import router as observability_router
from backend.api.routes_runner import router as runner_router
from backend.api.routes_hypotheses import router as hypotheses_router
from backend.api.routes_planner import router as planner_router
from backend.api.routes_evidence import router as evidence_router
from backend.api.routes_memory import router as memory_router
from backend.api.routes_surrogate import router as surrogate_router
from backend.api.routes_closed_loop import router as closed_loop_router
from backend.api.routes_geometry import router as geometry_router
from backend.api.routes_aerodb import router as aerodb_router
from backend.api.routes_cognitive import router as cognitive_router
from backend.api.routes_model_zoo import router as model_zoo_router
from backend.api.routes_commercial import router as commercial_router
from backend.api.routes_export import router as export_router
from backend.api.routes_aml import router as aml_router
from backend.api.routes_compiler import router as compiler_router
from backend.api.routes_certification import router as certification_router
from backend.api.routes_system import router as system_router
from backend.api.routes_modules import router as modules_router
from backend.api.routes_agent import router as agent_router
from backend.api.routes_digital_twin import router as digital_twin_router
from backend.api.routes_mission import router as mission_router
from backend.api.routes_investigation_flagship import router as flagship_router
from backend.api.routes_transonic_transolver import router as transonic_router
from backend.api.routes_turbulence_sciml import router as turbulence_router
from backend.api.routes_equivariant_gnn import router as gnn_router
from backend.api.routes_conformal_uncertainty import router as conformal_router
from backend.api.routes_hypersonic_aerothermo import router as hypersonic_router
from backend.api.routes_fsi_flutter import router as flutter_router
from backend.api.routes_inverse_diffusion import router as diffusion_router
from backend.api.routes_active_flow_control import router as afc_router
from backend.api.routes_asme_vv20 import router as asme_vv20_router
from backend.api.routes_orbital_dynamics import router as orbital_dynamics_router
from backend.api.routes_spadex_docking import router as spadex_docking_router
from backend.api.routes_netra_cam import router as netra_cam_router
from backend.api.routes_neural_lyapunov import router as neural_lyapunov_router
from backend.api.routes_airspace_catfm import router as catfm_router
from backend.api.routes_popperian_discovery import router as discovery_router
from backend.api.routes_rotating_detonation import router as rde_router
from backend.api.routes_certified_code import router as certified_code_router
from backend.api.routes_hil_avionics import router as hil_avionics_router
from backend.api.routes_landmark_publication import router as publication_router
from backend.api.routes_cislunar_manifolds import router as cislunar_router
from backend.api.routes_planetary_edl import router as edl_router
from backend.api.routes_mhd_plasma import router as mhd_router
from backend.api.routes_neuromorphic_ssa import router as ssa_router
from backend.api.routes_optical_qkd import router as optical_qkd_router
from backend.api.routes_swarm_coordinator import router as swarm_router
from backend.api.routes_hypersonic_interceptor import router as interceptor_router
from backend.api.routes_metamaterial_rcs import router as rcs_router
from backend.api.routes_post_quantum_bus import router as pqc_bus_router
from backend.api.routes_aerial_refueling import router as refueling_router
from backend.api.routes_generative_mdo import router as mdo_router
from backend.api.routes_lpbf_meltpool import router as meltpool_router
from backend.api.routes_acoustic_ndt import router as acoustic_ndt_router
from backend.api.routes_composite_fracture import router as composite_fracture_router
from backend.api.routes_digital_thread import router as digital_thread_router
from backend.api.routes_constellation_insurance import router as insurance_router
from backend.api.routes_airworthiness_dossier import router as airworthiness_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(compute_router)
api_router.include_router(dataset_router)
api_router.include_router(investigation_router)
api_router.include_router(jobs_router)
api_router.include_router(results_router)
api_router.include_router(observability_router)
api_router.include_router(runner_router)
api_router.include_router(hypotheses_router)
api_router.include_router(planner_router)
api_router.include_router(evidence_router)
api_router.include_router(memory_router)
api_router.include_router(surrogate_router)
api_router.include_router(closed_loop_router)
api_router.include_router(geometry_router)
api_router.include_router(aerodb_router)
api_router.include_router(cognitive_router)
api_router.include_router(model_zoo_router)
api_router.include_router(commercial_router)
api_router.include_router(export_router)
api_router.include_router(aml_router)
api_router.include_router(compiler_router)
api_router.include_router(certification_router)
api_router.include_router(system_router)
api_router.include_router(modules_router)
api_router.include_router(agent_router)
api_router.include_router(digital_twin_router)
api_router.include_router(mission_router)
api_router.include_router(flagship_router)
api_router.include_router(transonic_router)
api_router.include_router(turbulence_router)
api_router.include_router(gnn_router)
api_router.include_router(conformal_router)
api_router.include_router(hypersonic_router)
api_router.include_router(flutter_router)
api_router.include_router(diffusion_router)
api_router.include_router(afc_router)
api_router.include_router(asme_vv20_router)
api_router.include_router(orbital_dynamics_router)
api_router.include_router(spadex_docking_router)
api_router.include_router(netra_cam_router)
api_router.include_router(neural_lyapunov_router)
api_router.include_router(catfm_router)
api_router.include_router(discovery_router)
api_router.include_router(rde_router)
api_router.include_router(certified_code_router)
api_router.include_router(hil_avionics_router)
api_router.include_router(publication_router)
api_router.include_router(cislunar_router)
api_router.include_router(edl_router)
api_router.include_router(mhd_router)
api_router.include_router(ssa_router)
api_router.include_router(optical_qkd_router)
api_router.include_router(swarm_router)
api_router.include_router(interceptor_router)
api_router.include_router(rcs_router)
api_router.include_router(pqc_bus_router)
api_router.include_router(refueling_router)
api_router.include_router(mdo_router)
api_router.include_router(meltpool_router)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(compute_router)
api_v1_router.include_router(dataset_router)
api_v1_router.include_router(investigation_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(results_router)
api_v1_router.include_router(observability_router)
api_v1_router.include_router(runner_router)
api_v1_router.include_router(hypotheses_router)
api_v1_router.include_router(planner_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(memory_router)
api_v1_router.include_router(surrogate_router)
api_v1_router.include_router(closed_loop_router)
api_v1_router.include_router(geometry_router)
api_v1_router.include_router(aerodb_router)
api_v1_router.include_router(cognitive_router)
api_v1_router.include_router(model_zoo_router)
api_v1_router.include_router(commercial_router)
api_v1_router.include_router(export_router)
api_v1_router.include_router(aml_router)
api_v1_router.include_router(compiler_router)
api_v1_router.include_router(certification_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(modules_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(digital_twin_router)
api_v1_router.include_router(mission_router)
api_v1_router.include_router(flagship_router)
api_v1_router.include_router(transonic_router)
api_v1_router.include_router(turbulence_router)
api_v1_router.include_router(gnn_router)
api_v1_router.include_router(conformal_router)
api_v1_router.include_router(hypersonic_router)
api_v1_router.include_router(flutter_router)
api_v1_router.include_router(diffusion_router)
api_v1_router.include_router(afc_router)
api_v1_router.include_router(asme_vv20_router)
api_v1_router.include_router(orbital_dynamics_router)
api_v1_router.include_router(spadex_docking_router)
api_v1_router.include_router(netra_cam_router)
api_v1_router.include_router(neural_lyapunov_router)
api_v1_router.include_router(catfm_router)
api_v1_router.include_router(discovery_router)
api_v1_router.include_router(rde_router)
api_v1_router.include_router(certified_code_router)
api_v1_router.include_router(hil_avionics_router)
api_v1_router.include_router(publication_router)
api_v1_router.include_router(cislunar_router)
api_v1_router.include_router(edl_router)
api_v1_router.include_router(mhd_router)
api_v1_router.include_router(ssa_router)
api_v1_router.include_router(optical_qkd_router)
api_v1_router.include_router(swarm_router)
api_v1_router.include_router(interceptor_router)
api_v1_router.include_router(rcs_router)
api_v1_router.include_router(pqc_bus_router)
api_v1_router.include_router(refueling_router)
api_v1_router.include_router(mdo_router)
api_v1_router.include_router(meltpool_router)
api_v1_router.include_router(acoustic_ndt_router)
api_v1_router.include_router(composite_fracture_router)
api_v1_router.include_router(digital_thread_router)
api_v1_router.include_router(insurance_router)
api_v1_router.include_router(airworthiness_router)

__all__ = ["api_router", "api_v1_router"]


