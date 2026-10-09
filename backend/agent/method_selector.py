"""
AASI Phase 28: Explicit Method Selection Engine.
Selects among DATABASE_REAL, SURROGATE, ANALYTICAL, LIVE_CFD, and USER_PROVIDED.
Produces traceable, explainable decision records with physical justification and fallbacks.
"""

from typing import List, Optional, Dict, Any
from backend.agent.canonical_investigation import (
    EpistemicTier,
    MethodCandidate,
    MethodSelectionRecord,
    OperatingConditions,
)


class MethodSelector:
    """
    Evaluates candidate scientific methods and produces explainable selection records.
    Never hardcodes a single method for all problems.
    """

    @classmethod
    def evaluate_candidates(
        cls,
        geometry: str,
        conditions: OperatingConditions,
        user_intent: str,
        has_database_match: bool = False,
        database_distance: float = 1.0,
        surrogate_uncertainty: float = 0.08,
    ) -> MethodSelectionRecord:
        candidates: List[MethodCandidate] = []

        # 1. Analytical Method Candidate (Thin Airfoil Theory / Potential Flow)
        is_thin_airfoil_valid = (
            conditions.mach < 0.3
            and -6.0 <= conditions.alpha_deg <= 8.0
            and ("NACA" in geometry.upper() or "EPPLER" in geometry.upper())
        )
        candidates.append(
            MethodCandidate(
                method_name="Thin Airfoil Potential Theory",
                tier=EpistemicTier.ANALYTICAL,
                applicable=is_thin_airfoil_valid,
                suitability_score=0.70 if is_thin_airfoil_valid else 0.20,
                reason=(
                    "Valid for linear attached lift slope (dCL/dalpha = 2pi). "
                    "Cannot resolve viscous boundary layer pressure drag or flow separation."
                    if is_thin_airfoil_valid
                    else "Inapplicable: Flow regime exceeds linear inviscid limits (high alpha or compressibility)."
                ),
                limitations=[
                    "Zero skin friction drag (assumes inviscid potential flow)",
                    "Cannot predict flow separation or stall onset",
                    "Assumes small camber and small thickness (t/c << 1)",
                ],
            )
        )

        # 2. Database Benchmark Candidate (NACA Report 824 / AirfRANS / Abbott)
        db_applicable = has_database_match or database_distance < 0.20
        candidates.append(
            MethodCandidate(
                method_name="Historical Aerodynamic Benchmark Catalog",
                tier=EpistemicTier.DATABASE_REAL,
                applicable=db_applicable,
                suitability_score=0.95 if database_distance < 0.05 else (0.80 if db_applicable else 0.15),
                reason=(
                    f"Authoritative experimental / peer-reviewed benchmark exists (distance={database_distance:.2f})."
                    if db_applicable
                    else "No close historical benchmark data found in knowledge fabric for this geometry/Re."
                ),
                limitations=[
                    "Limited to discrete test points tested in wind tunnels",
                    "Tunnel wall and turbulence level corrections may be required",
                    "Does not provide full continuous 2D field contours",
                ],
            )
        )

        # 3. Neural Surrogate Candidate (AeroGraphNet / AeroSurrogateV1)
        surrogate_applicable = surrogate_uncertainty < 0.25 and conditions.mach < 0.6
        candidates.append(
            MethodCandidate(
                method_name="AeroSurrogateV1 Neural Operator",
                tier=EpistemicTier.SURROGATE,
                applicable=surrogate_applicable,
                suitability_score=0.85 if surrogate_uncertainty < 0.10 else (0.65 if surrogate_applicable else 0.30),
                reason=(
                    f"Surrogate epistemic uncertainty is acceptable (sigma={surrogate_uncertainty:.2f}). Instant evaluation."
                    if surrogate_applicable
                    else f"Surrogate uncertainty exceeds tolerance (sigma={surrogate_uncertainty:.2f}); extrapolation hazard."
                ),
                limitations=[
                    "Epistemic variance increases outside training envelope",
                    "Smooth spatial kernel averaging may soften sharp adverse pressure peaks",
                    "Statistical approximation rather than exact solution of Navier-Stokes",
                ],
            )
        )

        # 4. Live CFD Simulation Candidate (OpenFOAM RANS SST)
        cfd_required = (
            abs(conditions.alpha_deg) > 8.0
            or conditions.mach >= 0.3
            or database_distance > 0.20
            or surrogate_uncertainty >= 0.20
            or "compare" in user_intent.lower()
            or "cfd" in user_intent.lower()
            or "separation" in user_intent.lower()
            or "drag" in user_intent.lower()
        )
        candidates.append(
            MethodCandidate(
                method_name="OpenFOAM simpleFoam (k-omega SST)",
                tier=EpistemicTier.LIVE_CFD,
                applicable=True,
                suitability_score=0.98 if cfd_required else 0.75,
                reason=(
                    "Navier-Stokes solution resolves viscous boundary layer, pressure gradients, and adverse separation drag."
                ),
                limitations=[
                    "High computational cost requiring external execution fabric",
                    "Turbulence model closure assumptions (Boussinesq hypothesis)",
                    "Mesh quality and boundary layer y+ sensitivity",
                ],
            )
        )

        is_analytical_query = any(k in user_intent.lower() for k in ["analytical", "theoretical", "thin airfoil", "inviscid", "potential flow", "first-order"])

        # Decision Logic:
        if is_analytical_query and "cfd" not in user_intent.lower():
            selected = EpistemicTier.ANALYTICAL
            reason = (
                "Theoretical thin airfoil potential flow solution selected per user inquiry for inviscid lift slope. "
                "Note: inviscid assumptions strictly cannot predict viscous form drag or boundary layer separation."
            )
            confidence = 0.92
            fallback = EpistemicTier.DATABASE_REAL if db_applicable else EpistemicTier.LIVE_CFD
            evidence = [
                "Governing equation: Incompressible Potential Flow / Laplace equation",
                "Classical Thin Airfoil Theory: dCL/dalpha = 2*pi",
                "Strict caveat: zero skin friction and zero pressure drag (d'Alembert paradox)",
            ]
            method_limits = [
                "Cannot resolve viscous drag or separation",
                "Restricted to low angles of attack",
            ]
        # If user asked for full analysis or comparison -> LIVE_CFD with fallback to DATABASE_REAL
        elif "cfd" in user_intent.lower() or cfd_required:
            selected = EpistemicTier.LIVE_CFD
            reason = (
                "The requested flow regime involves viscous drag / separation physics requiring "
                "numerical Navier-Stokes simulation. Staging OpenFOAM CFD execution."
            )
            confidence = 0.95
            fallback = EpistemicTier.DATABASE_REAL if db_applicable else EpistemicTier.SURROGATE
            evidence = [
                "Governing equation: Incompressible RANS with k-omega SST turbulence closure",
                f"Angle of attack alpha={conditions.alpha_deg}° probes boundary layer growth",
                f"Reynolds number Re={conditions.reynolds:.1e}",
            ]
            method_limits = [
                "Requires external hardware execution",
                "Requires post-processing verification before empirical acceptance",
            ]
        elif db_applicable and database_distance < 0.05:
            selected = EpistemicTier.DATABASE_REAL
            reason = "Authoritative peer-reviewed benchmark data exists in verified knowledge fabric; retrieving directly."
            confidence = 0.99
            fallback = EpistemicTier.SURROGATE
            evidence = [
                "NACA Technical Report 824 / Abbott & von Doenhoff benchmark",
                f"Close match distance={database_distance:.3f}",
            ]
            method_limits = [
                "Discrete experimental points only",
            ]
        elif surrogate_applicable:
            selected = EpistemicTier.SURROGATE
            reason = "Surrogate operator uncertainty is within acceptable tolerance; delivering instant prediction."
            confidence = 0.85
            fallback = EpistemicTier.ANALYTICAL
            evidence = [
                f"Surrogate epistemic uncertainty sigma={surrogate_uncertainty:.2f} <= 0.25",
            ]
            method_limits = [
                "Approximate inference bounded by training distribution",
            ]
        else:
            selected = EpistemicTier.ANALYTICAL
            reason = "Analytical potential flow solution provides initial first-order inviscid estimate."
            confidence = 0.70
            fallback = None
            evidence = ["Thin Airfoil Theory dCL/dalpha = 2*pi"]
            method_limits = [
                "Inviscid assumption cannot predict drag",
            ]

        return MethodSelectionRecord(
            candidate_methods=candidates,
            selected_method=selected,
            reason=reason,
            confidence=confidence,
            required_evidence=evidence,
            limitations=method_limits,
            fallback_method=fallback,
        )
