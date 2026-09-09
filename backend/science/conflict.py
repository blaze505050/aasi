"""Multi-source conflict resolution and physical discrepancy synthesis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from .models import ScientificResult, SourceDiscrepancy


class ConflictResolutionEngine:
    """Evaluates multiple scientific results across experimental, CFD, and surrogate sources.

    Never arbitrarily discards results; synthesizes physical causes of variance.
    """

    def analyze_discrepancy(
        self,
        results: List[ScientificResult],
        quantity: str = "CD",
    ) -> Optional[SourceDiscrepancy]:
        """Analyze differences between multiple results for the same physical quantity."""
        matching = [r for r in results if r.quantity.upper() == quantity.upper() and r.value is not None]
        if len(matching) <= 1:
            return None

        values = [r.value for r in matching]
        min_v = min(values)
        max_v = max(values)
        mean_v = sum(values) / len(values)

        rel_diff = ((max_v - min_v) / mean_v) * 100.0 if mean_v > 0 else 0.0

        sources_summary: List[Dict[str, Any]] = [
            {
                "result_id": r.result_id,
                "source": r.source,
                "method": r.method,
                "epistemic_status": r.epistemic_status.value,
                "value": r.value,
                "units": r.units,
                "uncertainty": r.uncertainty,
            }
            for r in matching
        ]

        physical_reasons = self._diagnose_physical_reasons(matching, quantity)

        # Authoritative recommendation cascade: Official Experiment > Validated CFD > Surrogate > Estimate
        rec_source = None
        for r in matching:
            if r.epistemic_status.value in ["OFFICIAL_EXPERIMENT", "VALIDATED_EXPERIMENT"]:
                rec_source = f"{r.source} ({r.method})"
                break
        if not rec_source:
            for r in matching:
                if r.epistemic_status.value in ["OFFICIAL_CFD", "VALIDATED_CFD"]:
                    rec_source = f"{r.source} ({r.method})"
                    break

        return SourceDiscrepancy(
            quantity=quantity,
            sources_compared=sources_summary,
            max_relative_difference=round(rel_diff, 2),
            physical_reasons=physical_reasons,
            recommended_source=rec_source or "Consult experimental baseline",
        )

    def _diagnose_physical_reasons(
        self,
        results: List[ScientificResult],
        quantity: str,
    ) -> List[str]:
        """Identify scientifically grounded reasons for discrepancies between experimental and numerical sources."""
        reasons: List[str] = []
        statuses = [r.epistemic_status.value for r in results]

        has_experiment = any("EXPERIMENT" in s for s in statuses)
        has_cfd = any("CFD" in s for s in statuses)
        has_surrogate = any("SURROGATE" in s for s in statuses)

        if has_experiment and has_cfd:
            reasons.append(
                "Boundary Layer Transition: Wind tunnel models experience free transition influenced by freestream "
                "turbulence intensity, whereas RANS CFD typically assumes fully turbulent flow unless coupled with a "
                "gamma-Re_theta transition model."
            )
            reasons.append(
                "Wind-Tunnel Wall Interference & Blockage: Experimental measurements include tunnel wall boundary layer "
                "displacement and streamline curvature corrections, whereas CFD models far-field unconfined boundaries."
            )
            reasons.append(
                "Turbulence Closure Model Damping: Isotropic eddy-viscosity models (e.g. SA, k-omega SST) can over-predict "
                "skin friction in adverse pressure gradients or under-predict separation bubble size."
            )

        if has_surrogate:
            reasons.append(
                "Surrogate Generalization Loss: Neural operator predictions inherently trade pointwise exactness for global "
                "inference speed, typically showing 1-3% L2 interpolation error relative to high-fidelity solver truth."
            )

        if not reasons:
            reasons.append("Differences in operational boundary conditions, Reynolds number scaling, or numerical grid resolution.")

        return reasons
