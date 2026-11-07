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

__all__ = ["api_router", "api_v1_router"]


