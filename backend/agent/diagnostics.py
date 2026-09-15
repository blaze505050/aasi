"""
AASI Automatic CFD Error Diagnosis Engine.
Classifies simulation and mesh failures into deterministic diagnostic categories.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import re


class CFDErrorClass(str, Enum):
    MISSING_SOLVER = "MISSING_SOLVER"
    MISSING_EXECUTABLE = "MISSING_EXECUTABLE"
    MESH_GENERATION_FAILURE = "MESH_GENERATION_FAILURE"
    MESH_QUALITY_FAILURE = "MESH_QUALITY_FAILURE"
    INVALID_BOUNDARY_CONDITION = "INVALID_BOUNDARY_CONDITION"
    DIVERGENCE = "DIVERGENCE"
    RESIDUAL_STAGNATION = "RESIDUAL_STAGNATION"
    FLOATING_POINT_FAILURE = "FLOATING_POINT_FAILURE"
    NEGATIVE_PHYSICAL_FIELD = "NEGATIVE_PHYSICAL_FIELD"
    MISSING_FORCE_COEFFICIENTS = "MISSING_FORCE_COEFFICIENTS"
    INCOMPLETE_RESULT_ARCHIVE = "INCOMPLETE_RESULT_ARCHIVE"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    RUNTIME_TERMINATION = "RUNTIME_TERMINATION"
    PHYSICS_GATE_VIOLATION = "PHYSICS_GATE_VIOLATION"
    UNKNOWN = "UNKNOWN"


class DiagnosticReport(BaseModel):
    """Structured failure diagnosis output."""
    error_class: CFDErrorClass
    evidence: List[str]
    diagnosis: str
    confidence: float
    repair_candidates: List[str]


class CFDDiagnosticsEngine:
    """
    Parses solver logs, mesh logs, residual curves, and result manifests to diagnose failures.
    """

    @classmethod
    def diagnose(
        cls,
        solver_log: Optional[str] = None,
        mesh_log: Optional[str] = None,
        residuals: Optional[Dict[str, List[float]]] = None,
        forces: Optional[Dict[str, float]] = None,
        manifest: Optional[Dict[str, Any]] = None,
        exit_code: Optional[int] = None,
    ) -> DiagnosticReport:
        evidence = []

        # 1. Missing solver / executable
        if solver_log and ("command not found" in solver_log.lower() or "not recognized as an internal or external command" in solver_log.lower()):
            evidence.append("Shell reported solver command not found.")
            return DiagnosticReport(
                error_class=CFDErrorClass.MISSING_SOLVER,
                evidence=evidence,
                diagnosis="OpenFOAM solver executable is not installed or not in PATH.",
                confidence=0.99,
                repair_candidates=[
                    "Install OpenFOAM-10 via source environment script.",
                    "Route simulation to Google Colab remote backend where OpenFOAM is pre-installed.",
                ],
            )

        # 2. Floating point failure
        if solver_log and ("floating point exception" in solver_log.lower() or "nan" in solver_log.lower()):
            evidence.append("Solver log contains 'Floating point exception' or NaN values.")
            return DiagnosticReport(
                error_class=CFDErrorClass.FLOATING_POINT_FAILURE,
                evidence=evidence,
                diagnosis="Numerical overflow / divide-by-zero encountered during matrix inversion.",
                confidence=0.95,
                repair_candidates=[
                    "Decrease relaxation factors in fvSolution (e.g. p: 0.2, U: 0.5).",
                    "Switch convection schemes in fvSchemes from linearUpwind to upwind.",
                    "Refine boundary layer mesh near leading edge to reduce skewness.",
                ],
            )

        # 3. Divergence in residuals
        if residuals:
            for field_name, vals in residuals.items():
                if vals and (vals[-1] > 10.0 or any(v > 100.0 for v in vals[-10:])):
                    evidence.append(f"Residual for field '{field_name}' exploded to {vals[-1]:.2e}.")
                    return DiagnosticReport(
                        error_class=CFDErrorClass.DIVERGENCE,
                        evidence=evidence,
                        diagnosis=f"Flow solver diverged uncontrollably in field '{field_name}'.",
                        confidence=0.95,
                        repair_candidates=[
                            "Reduce fvSolution relaxation factors by 30%.",
                            "Use bounded first-order upwind schemes for initial iterations.",
                            "Check inlet boundary condition velocity vector.",
                        ],
                    )

        # 4. Residual stagnation
        if residuals:
            p_res = residuals.get("p", [])
            if len(p_res) > 300 and p_res[-1] > 1e-2 and abs(p_res[-1] - p_res[-50]) < 1e-4:
                evidence.append(f"Pressure residual stagnated at {p_res[-1]:.2e} over last 50 iterations.")
                return DiagnosticReport(
                    error_class=CFDErrorClass.RESIDUAL_STAGNATION,
                    evidence=evidence,
                    diagnosis="Residuals ceased decreasing and stagnated above convergence threshold (1e-4).",
                    confidence=0.90,
                    repair_candidates=[
                        "Adjust GAMG solver tolerances in fvSolution.",
                        "Inspect grid resolution in wake region.",
                        "Switch turbulence model wall functions from low-Re to standard wall functions.",
                    ],
                )

        # 5. Mesh quality / generation failure
        if mesh_log:
            if "error in blockMesh" in mesh_log.lower() or "blockMesh error" in mesh_log.lower() or "segmentation fault" in mesh_log.lower():
                evidence.append("blockMesh exited with errors.")
                return DiagnosticReport(
                    error_class=CFDErrorClass.MESH_GENERATION_FAILURE,
                    evidence=evidence,
                    diagnosis="blockMesh failed to parse topology or construct hex cells.",
                    confidence=0.98,
                    repair_candidates=[
                        "Regenerate blockMeshDict with sanitized vertex coordinates.",
                        "Re-compute domain bounding box bounds.",
                    ],
                )
            if "skewness > 4" in mesh_log.lower() or "non-orthogonality > 70" in mesh_log.lower() or "negative cell volume" in mesh_log.lower():
                evidence.append("checkMesh reported severe non-orthogonality or negative cell volumes.")
                return DiagnosticReport(
                    error_class=CFDErrorClass.MESH_QUALITY_FAILURE,
                    evidence=evidence,
                    diagnosis="Generated mesh fails ASME V&V 20 geometric quality standards.",
                    confidence=0.95,
                    repair_candidates=[
                        "Smooth hyperbolic C-grid boundary layer clustering.",
                        "Increase grading ratio on airfoil surface.",
                    ],
                )

        # 6. Invalid boundary condition
        if solver_log and ("patch not found" in solver_log.lower() or "cannot find file" in solver_log.lower() or "incompatible dimensions" in solver_log.lower()):
            evidence.append("Boundary dictionary patch mismatch or dimensional inconsistency.")
            return DiagnosticReport(
                error_class=CFDErrorClass.INVALID_BOUNDARY_CONDITION,
                evidence=evidence,
                diagnosis="Boundary conditions in 0/ do not match mesh patch definitions.",
                confidence=0.95,
                repair_candidates=[
                    "Harmonize patch names in 0/U and 0/p with boundary definitions in constant/polyMesh/boundary.",
                    "Verify kinematic pressure dimensions [0 2 -2 0 0 0 0].",
                ],
            )

        # 7. Missing force coefficients
        if forces is None or len(forces) == 0:
            if solver_log and "simplefoam" in solver_log.lower():
                evidence.append("Solver finished but postProcessing/forceCoeffs is missing or unreadable.")
                return DiagnosticReport(
                    error_class=CFDErrorClass.MISSING_FORCE_COEFFICIENTS,
                    evidence=evidence,
                    diagnosis="Forces functionObject was omitted or failed to log force coefficients.",
                    confidence=0.90,
                    repair_candidates=[
                        "Verify functionObjects declaration in system/controlDict.",
                        "Check liftDir and dragDir vectors in system/forceCoeffs.",
                    ],
                )

        # 8. Physical gate violation: negative drag or excessive Bernoulli Cp
        if forces:
            cd = forces.get("cd", 0.0)
            cl = forces.get("cl", 0.0)
            if cd <= 0.0:
                evidence.append(f"Physical impossibility: CD={cd:.6f} <= 0.0.")
                return DiagnosticReport(
                    error_class=CFDErrorClass.PHYSICS_GATE_VIOLATION,
                    evidence=evidence,
                    diagnosis="Calculated drag coefficient is non-positive, violating thermodynamics.",
                    confidence=0.99,
                    repair_candidates=[
                        "Check dragDir orientation relative to angle of attack.",
                        "Verify skin friction component integration.",
                    ],
                )

        # 9. Incomplete result archive / exit code failure
        if exit_code and exit_code != 0:
            evidence.append(f"Process terminated with non-zero exit code: {exit_code}.")
            return DiagnosticReport(
                error_class=CFDErrorClass.RUNTIME_TERMINATION,
                evidence=evidence,
                diagnosis=f"Simulation process terminated abnormally with exit code {exit_code}.",
                confidence=0.85,
                repair_candidates=[
                    "Check system RAM / swap capacity.",
                    "Verify file write permissions in case directory.",
                ],
            )

        # Fallback
        return DiagnosticReport(
            error_class=CFDErrorClass.UNKNOWN,
            evidence=["No recognized deterministic error signatures found."],
            diagnosis="Simulation state anomalous or unverified.",
            confidence=0.40,
            repair_candidates=["Perform manual log inspection and review preflight checks."],
        )
