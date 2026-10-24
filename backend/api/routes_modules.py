"""
AASI Control Plane: 30-Problem Modular Architecture & Benchmark Registry API.

Provides endpoints to:
1. Discover problem modules and supported fidelity ladders (L0, L1, L2).
2. Execute deterministic physical solves with cryptographic evidence records.
3. Retrieve Guide to Uncertainty in Measurement (GUM) uncertainty budgets.
4. Run published reference benchmarks and continuous validation suites.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.modules.base import FidelityLevel
from backend.modules.benchmark_registry import benchmark_registry

router = APIRouter(prefix="/modules", tags=["Modules & Benchmark Registry"])


class SolveModuleRequest(BaseModel):
    fidelity: FidelityLevel = Field(default=FidelityLevel.L1_REDUCED_ORDER)
    inputs: Dict[str, Any] = Field(default_factory=dict)


@router.get("", summary="List all registered problem modules and fidelity capabilities")
def list_modules():
    """
    Returns the catalog of registered aerospace problem modules across Tier 1 (Aerodynamics Core),
    Tier 2 (Vehicle Systems & Propulsion), and Tier 3 (Space Operations).
    """
    return {
        "status": "success",
        "total_modules": len(benchmark_registry.list_modules()),
        "modules": benchmark_registry.list_modules(),
    }


@router.get("/benchmarks", summary="List all registered aerospace reference benchmarks")
def list_all_benchmarks():
    """
    Returns all registered reference benchmarks with literature citations and expected tolerances.
    """
    cases = benchmark_registry.list_all_benchmarks()
    return {
        "status": "success",
        "total_benchmarks": len(cases),
        "benchmarks": cases,
    }


@router.post("/benchmarks/run-all", summary="Execute continuous validation suite across all modules")
def run_all_benchmarks():
    """
    Executes all reference benchmarks (NACA 0012, RAE 2822, E387, ONERA M6),
    verifies tolerance criteria, and returns a cryptographic platform validation dossier.
    """
    report = benchmark_registry.run_all()
    return report.model_dump()


@router.get("/{module_id}", summary="Get details and specifications for a specific problem module")
def get_module(module_id: str):
    mod = benchmark_registry.get_module(module_id)
    if not mod:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")
    return {
        "module_id": mod.module_id,
        "problem_id": mod.problem_id,
        "name": mod.name,
        "tier": mod.tier,
        "description": mod.description,
        "supported_fidelities": [f.value for f in mod.supported_fidelities],
        "benchmarks": [b.model_dump() for b in mod.benchmarks()],
    }


@router.post("/{module_id}/solve", summary="Solve forward problem using specified fidelity level")
def solve_module(module_id: str, request: SolveModuleRequest):
    """
    Solves physical problem deterministically and returns outputs, uncertainty, and evidence record.
    """
    mod = benchmark_registry.get_module(module_id)
    if not mod:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")

    try:
        result = mod.solve(inputs=request.inputs, fidelity=request.fidelity)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Solver execution error: {str(e)}")


@router.post("/{module_id}/uncertainty", summary="Compute GUM 5-tier uncertainty intervals")
def module_uncertainty(module_id: str, inputs: Dict[str, Any]):
    """
    Computes formal 95% confidence intervals on aerodynamic and system coefficients.
    """
    mod = benchmark_registry.get_module(module_id)
    if not mod:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")

    try:
        uncert = mod.uncertainty(inputs=inputs)
        return uncert
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Uncertainty computation error: {str(e)}")


@router.get("/{module_id}/benchmarks", summary="Get benchmark cases for a module")
def get_module_benchmarks(module_id: str):
    mod = benchmark_registry.get_module(module_id)
    if not mod:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")
    return [b.model_dump() for b in mod.benchmarks()]


@router.post("/{module_id}/verify", summary="Verify module against reference benchmarks")
def verify_module(module_id: str):
    """
    Runs reference benchmarks for this module and reports pass/fail against published data.
    """
    try:
        report = benchmark_registry.run_module_benchmarks(module_id)
        return report.model_dump()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failure: {str(e)}")
