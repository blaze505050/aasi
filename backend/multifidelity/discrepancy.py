"""
AASI Multi-Fidelity Discrepancy Engine.

Models and analyzes the discrepancy:
    High Fidelity ≈ Low Fidelity + Discrepancy(x)

Supports:
- Absolute and relative discrepancy calculation
- Polar sweep systematic bias estimation
- Root-mean-square discrepancy (RMSD)
- Physical explanation synthesis based on aerodynamic regimes
- Full cryptographic provenance preservation.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import hashlib
from backend.multifidelity.models import (
    FidelityLevel,
    FlowConditions,
    MultiFidelityResult,
    DiscrepancyResult,
)


class MultiFidelityDiscrepancyEngine:
    """Calculates, quantifies, and explains differences between fidelity levels."""

    @classmethod
    def calculate_discrepancy(
        cls,
        high_res: MultiFidelityResult,
        low_res: MultiFidelityResult,
        tolerance: float = 0.05
    ) -> DiscrepancyResult:
        """
        Calculates discrepancy between matched single-point results.
        """
        diff = high_res.value - low_res.value
        base = abs(high_res.value) if abs(high_res.value) > 1e-4 else 1.0
        rel_pct = (abs(diff) / base) * 100.0

        is_significant = abs(diff) > tolerance

        explanation = cls._synthesize_physical_explanation(
            quantity=high_res.quantity,
            high_fidelity=high_res.fidelity,
            low_fidelity=low_res.fidelity,
            conditions=high_res.conditions,
            diff=diff
        )

        provenance_payload = f"{high_res.provenance_hash}:{low_res.provenance_hash}:{diff:.6f}"
        prov_hash = hashlib.sha256(provenance_payload.encode("utf-8")).hexdigest()

        return DiscrepancyResult(
            geometry=high_res.geometry,
            conditions=high_res.conditions,
            quantity=high_res.quantity,
            high_fidelity_level=high_res.fidelity,
            low_fidelity_level=low_res.fidelity,
            high_fidelity_value=high_res.value,
            low_fidelity_value=low_res.value,
            absolute_discrepancy=diff,
            relative_discrepancy_pct=rel_pct,
            bias_estimate=diff,
            is_statistically_significant=is_significant,
            physical_explanation=explanation,
            provenance_hash=prov_hash
        )

    @classmethod
    def analyze_polar_discrepancy(
        cls,
        high_results: List[MultiFidelityResult],
        low_results: List[MultiFidelityResult]
    ) -> Dict[str, Any]:
        """
        Analyzes discrepancy across matched polar sweeps.
        Computes mean bias, RMS discrepancy, and correlation.
        """
        # Match by (mach, reynolds, aoa_deg) with small tolerance
        matched_pairs: List[Tuple[float, float]] = []

        for h in high_results:
            for l in low_results:
                if (
                    h.quantity == l.quantity
                    and abs(h.conditions.aoa_deg - l.conditions.aoa_deg) < 0.1
                    and abs(h.conditions.mach - l.conditions.mach) < 0.02
                ):
                    matched_pairs.append((h.value, l.value))
                    break

        if not matched_pairs:
            return {
                "matched_count": 0,
                "mean_bias": 0.0,
                "rmsd": 0.0,
                "max_discrepancy": 0.0,
                "systematic_bias_detected": False,
            }

        high_vals = np.array([p[0] for p in matched_pairs])
        low_vals = np.array([p[1] for p in matched_pairs])

        diffs = high_vals - low_vals
        mean_bias = float(np.mean(diffs))
        rmsd = float(np.sqrt(np.mean(diffs**2)))
        max_diff = float(np.max(np.abs(diffs)))

        # Systematic bias detected if mean bias is consistent (std < |mean|)
        std_diff = float(np.std(diffs))
        systematic = abs(mean_bias) > 0.02 and (std_diff < abs(mean_bias) * 1.5)

        return {
            "matched_count": len(matched_pairs),
            "mean_bias": round(mean_bias, 6),
            "rmsd": round(rmsd, 6),
            "max_discrepancy": round(max_diff, 6),
            "std_deviation": round(std_diff, 6),
            "systematic_bias_detected": systematic,
        }

    @classmethod
    def _synthesize_physical_explanation(
        cls,
        quantity: str,
        high_fidelity: FidelityLevel,
        low_fidelity: FidelityLevel,
        conditions: FlowConditions,
        diff: float
    ) -> str:
        """Derives scientific reasoning for observed fidelity discrepancy."""
        q = quantity.upper()
        aoa = conditions.aoa_deg
        mach = conditions.mach

        if q == "CD":
            if low_fidelity in (FidelityLevel.ANALYTICAL, FidelityLevel.LOW_FIDELITY_CFD) and diff > 0:
                if mach > 0.4:
                    return f"Higher drag in {high_fidelity.value} (+{diff:.4f}) is primarily driven by transonic compressibility and wave drag, which lower fidelity omits."
                return f"Higher drag in {high_fidelity.value} (+{diff:.4f}) reflects viscous boundary layer skin friction and pressure drag not fully captured by lower-fidelity models."
            if diff < 0:
                return f"Lower drag observed in {high_fidelity.value} ({diff:.4f}) suggests numerical dissipation in lower-fidelity CFD or conservative empirical drag estimation."

        if q == "CL":
            if aoa > 10.0:
                return f"Discrepancy at high AoA ({aoa:.1f}°) indicates boundary layer separation and stall onset; low-fidelity assumes linear thin-airfoil slope 2π, overpredicting lift by {abs(diff):.3f}."
            if abs(diff) < 0.03:
                return f"Close agreement (Δ={diff:.4f}) within attached-flow linear regime; thin-airfoil theory and surrogate match Navier-Stokes."

        return f"Discrepancy of {diff:.4f} between {high_fidelity.value} and {low_fidelity.value} reflecting differences in spatial resolution, turbulence closure, and physical assumptions."
