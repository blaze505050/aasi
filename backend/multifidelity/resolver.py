"""
AASI Multi-Fidelity Scientific Resolver.

Determines the highest trustworthy fidelity level for an aerospace query
according to the deterministic scientific priority cascade:
1. Exact Authoritative Experiment (Tier 1)
2. Validated High-Fidelity CFD (Tier 2)
3. Validated Surrogate within Envelope (Tier 5)
4. Analytical Approximation (Tier 4)
5. Generate Simulation Request via Simulation Planner
"""

from typing import Dict, Any, Optional, List, Tuple
from backend.multifidelity.models import (
    FidelityLevel,
    CFDQualityClassification,
    FlowConditions,
    MultiFidelityResult,
)
from backend.physics_ai.service import PhysicsAIService
from backend.physics_ai.schemas import DomainStatusEnum


class MultiFidelityResolver:
    """Resolves scientific queries by routing to the most appropriate fidelity tier."""

    def __init__(self):
        self.surrogate_service = PhysicsAIService.get_instance()

    def resolve_best_source(
        self,
        geometry: str,
        mach: float,
        reynolds: float,
        aoa_deg: float,
        quantity: str = "CL",
        available_experiments: Optional[List[MultiFidelityResult]] = None,
        available_cfd: Optional[List[MultiFidelityResult]] = None,
    ) -> Dict[str, Any]:
        """
        Executes cascade resolution for aerodynamic conditions.
        """
        conditions = FlowConditions(mach=mach, reynolds=reynolds, aoa_deg=aoa_deg)
        trace: List[str] = []

        # =====================================================================
        # TIER 1: EXACT EXPERIMENT
        # =====================================================================
        trace.append("Tier 1: Searching verified experimental wind tunnel / flight records...")
        if available_experiments:
            for exp in available_experiments:
                if (
                    exp.geometry.lower() == geometry.lower()
                    and exp.quantity.upper() == quantity.upper()
                    and abs(exp.conditions.mach - mach) <= 0.02
                    and abs(exp.conditions.aoa_deg - aoa_deg) <= 0.25
                    and abs(exp.conditions.reynolds - reynolds) / max(reynolds, 1e4) <= 0.20
                ):
                    trace.append(f"Tier 1 MATCH: Found authentic experimental measurement from {exp.source}.")
                    return {
                        "resolution_tier": FidelityLevel.EXPERIMENT.value,
                        "is_resolved": True,
                        "result": exp,
                        "value": exp.value,
                        "uncertainty": exp.uncertainty,
                        "source": exp.source,
                        "solver": None,
                        "provenance_hash": exp.provenance_hash,
                        "trace": trace,
                        "action_required": None,
                    }
        trace.append("Tier 1: No exact matched experimental record in database.")

        # =====================================================================
        # TIER 2: VALIDATED HIGH-FIDELITY CFD
        # =====================================================================
        trace.append("Tier 2: Searching validated high-fidelity converged CFD database...")
        if available_cfd:
            for cfd in available_cfd:
                if (
                    cfd.geometry.lower() == geometry.lower()
                    and cfd.quantity.upper() == quantity.upper()
                    and cfd.quality_classification in (CFDQualityClassification.CONVERGED, CFDQualityClassification.GRID_CONVERGED)
                    and abs(cfd.conditions.mach - mach) <= 0.02
                    and abs(cfd.conditions.aoa_deg - aoa_deg) <= 0.25
                ):
                    trace.append(f"Tier 2 MATCH: Found validated CFD result ({cfd.quality_classification.value}) from {cfd.solver}.")
                    return {
                        "resolution_tier": FidelityLevel.HIGH_FIDELITY_CFD.value,
                        "is_resolved": True,
                        "result": cfd,
                        "value": cfd.value,
                        "uncertainty": cfd.uncertainty,
                        "source": cfd.source,
                        "solver": cfd.solver,
                        "provenance_hash": cfd.provenance_hash,
                        "trace": trace,
                        "action_required": None,
                    }
        trace.append("Tier 2: No matched validated CFD solution available on disk.")

        # =====================================================================
        # TIER 3: VALIDATED SURROGATE WITHIN OPERATIONAL ENVELOPE
        # =====================================================================
        trace.append("Tier 3: Querying AeroSurrogateV1 neural operator validity envelope...")
        try:
            prediction = self.surrogate_service.predict(
                geometry=geometry,
                mach=mach,
                reynolds=reynolds,
                aoa_deg=aoa_deg
            )

            if prediction.domain_status in (DomainStatusEnum.IN_DOMAIN, DomainStatusEnum.EXTRAPOLATION_NEAR_BOUNDARY):
                val = getattr(prediction, quantity.lower(), None)
                unc = 0.0
                if prediction.uncertainty:
                    unc = getattr(prediction.uncertainty, f"{quantity.lower()}_uncertainty", 0.0)

                trace.append(f"Tier 3 MATCH: Evaluated AeroSurrogateV1 ({prediction.domain_status.value}) with confidence {prediction.uncertainty.confidence_score*100:.1f}%.")

                surrogate_res = MultiFidelityResult(
                    result_id=f"SURROGATE-{geometry}-{mach:.2f}-{aoa_deg:.1f}",
                    geometry=geometry,
                    geometry_hash=prediction.geometry_hash or "GEOM-RESAMPLED-64",
                    fidelity=FidelityLevel.SURROGATE,
                    quantity=quantity.upper(),
                    value=val,
                    uncertainty=unc,
                    conditions=conditions,
                    source="MODEL-AERO-SURROGATE-V1",
                    solver="AeroSurrogateV1 (Vectorized Neural Operator)",
                    solver_version="1.0.0",
                    provenance_hash=prediction.provenance_hash,
                )

                return {
                    "resolution_tier": FidelityLevel.SURROGATE.value,
                    "is_resolved": True,
                    "result": surrogate_res,
                    "value": val,
                    "uncertainty": unc,
                    "source": "MODEL-AERO-SURROGATE-V1",
                    "solver": "AeroSurrogateV1",
                    "provenance_hash": prediction.provenance_hash,
                    "domain_status": prediction.domain_status.value,
                    "trace": trace,
                    "action_required": None,
                }
            else:
                trace.append(f"Tier 3 REJECTED: Conditions [{mach}, {reynolds:.1e}, {aoa_deg}°] are OUT_OF_DOMAIN for AeroSurrogateV1.")
        except Exception as e:
            trace.append(f"Tier 3 Surrogate evaluation failed: {e}")

        # =====================================================================
        # TIER 4: ANALYTICAL APPROXIMATION (Thin Airfoil Theory / Incompressible)
        # =====================================================================
        trace.append("Tier 4: Checking applicability of analytical thin airfoil theory...")
        if mach < 0.30 and -6.0 <= aoa_deg <= 8.0:
            # Thin Airfoil Theory: dCL/dalpha = 2*pi per radian, CL = 2*pi*(alpha - alpha_0)
            # For symmetric airfoils alpha_0 = 0
            is_symmetric = "00" in geometry or "sym" in geometry.lower()
            alpha_0 = 0.0 if is_symmetric else -0.035  # Approximate camber offset
            alpha_rad = (aoa_deg - alpha_0) * (3.1415926535 / 180.0)
            cl_analytical = 2.0 * 3.1415926535 * alpha_rad
            # Prandtl-Glauert compressibility correction: beta = sqrt(1 - M^2)
            beta = (1.0 - mach**2)**0.5 if mach < 0.99 else 1.0
            cl_analytical /= max(beta, 0.1)

            if quantity.upper() == "CL":
                trace.append(f"Tier 4 MATCH: Thin-airfoil theory with Prandtl-Glauert applied (CL={cl_analytical:.4f}).")
                anal_res = MultiFidelityResult(
                    result_id=f"ANALYTICAL-TAT-{geometry}-{aoa_deg:.1f}",
                    geometry=geometry,
                    geometry_hash="ANALYTICAL-FORMULATION",
                    fidelity=FidelityLevel.ANALYTICAL,
                    quantity="CL",
                    value=round(cl_analytical, 4),
                    uncertainty=0.08,
                    conditions=conditions,
                    source="Thin Airfoil Theory (2*pi*alpha / sqrt(1 - M^2))",
                    provenance_hash="PROV-ANALYTICAL-THIN-AIRFOIL-THEORY",
                )
                return {
                    "resolution_tier": FidelityLevel.ANALYTICAL.value,
                    "is_resolved": True,
                    "result": anal_res,
                    "value": round(cl_analytical, 4),
                    "uncertainty": 0.08,
                    "source": "Thin Airfoil Theory",
                    "solver": "Analytical Formulation",
                    "provenance_hash": "PROV-ANALYTICAL-THIN-AIRFOIL-THEORY",
                    "trace": trace,
                    "action_required": None,
                }
        trace.append("Tier 4: Analytical theory inapplicable (non-linear regime, drag calculation, or transonic conditions).")

        # =====================================================================
        # TIER 5: ESCALATE TO SIMULATION PLANNER
        # =====================================================================
        trace.append("Tier 5: Escalating to Autonomous Simulation Planner to generate candidate CFD case.")
        return {
            "resolution_tier": "ESCALATE_TO_SIMULATION_PLANNER",
            "is_resolved": False,
            "result": None,
            "value": None,
            "uncertainty": None,
            "source": None,
            "solver": None,
            "provenance_hash": None,
            "trace": trace,
            "action_required": "GENERATE_CFD_JOB",
            "recommended_solver": "openfoam" if mach < 0.3 else "su2",
        }
