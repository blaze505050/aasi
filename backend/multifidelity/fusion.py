"""
AASI Multi-Fidelity Data Fusion.

Provides methodologies for combining heterogeneous observations (e.g. dense low-fidelity
surrogate or XFOIL sweeps with sparse high-fidelity CFD or experimental anchors)
while strictly preserving distinct fidelity tags and provenance lineage.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import hashlib
from backend.multifidelity.models import MultiFidelityResult, FidelityLevel, FlowConditions


class MultiFidelityFusionEngine:
    """Combines heterogeneous fidelity data with provenance tracking."""

    @classmethod
    def apply_bias_corrected_fusion(
        cls,
        low_fidelity_sweep: List[MultiFidelityResult],
        high_fidelity_anchors: List[MultiFidelityResult]
    ) -> List[MultiFidelityResult]:
        """
        Calibrates low-fidelity sweep with sparse high-fidelity anchors
        using condition-weighted residual bias correction.
        """
        if not high_fidelity_anchors or not low_fidelity_sweep:
            return low_fidelity_sweep

        # Calculate mean bias from matched points
        diffs = []
        for h in high_fidelity_anchors:
            for l in low_fidelity_sweep:
                if (
                    h.quantity == l.quantity
                    and abs(h.conditions.aoa_deg - l.conditions.aoa_deg) < 0.2
                    and abs(h.conditions.mach - l.conditions.mach) < 0.05
                ):
                    diffs.append(h.value - l.value)

        mean_bias = float(np.mean(diffs)) if diffs else 0.0

        fused_results = []
        for l in low_fidelity_sweep:
            calibrated_val = l.value + mean_bias
            if l.quantity.upper() == "CD":
                calibrated_val = max(calibrated_val, 0.001)  # Enforce CD > 0

            # Lineage provenance
            prov_input = f"FUSED:{l.provenance_hash}:{mean_bias:.5f}"
            new_hash = hashlib.sha256(prov_input.encode("utf-8")).hexdigest()

            fused_res = MultiFidelityResult(
                result_id=f"FUSED-{l.result_id}",
                geometry=l.geometry,
                geometry_hash=l.geometry_hash,
                fidelity=FidelityLevel.SURROGATE,  # Fused output classified as calibrated surrogate
                quantity=l.quantity,
                value=round(calibrated_val, 6),
                uncertainty=max(l.uncertainty * 0.8, 0.01),  # Variance reduction from calibration
                conditions=l.conditions,
                source=f"Fused ({l.source} + {high_fidelity_anchors[0].source} bias correction)",
                solver="MultiFidelityFusionEngine",
                provenance_hash=new_hash,
                metadata={"applied_bias": round(mean_bias, 6), "anchor_count": len(high_fidelity_anchors)}
            )
            fused_results.append(fused_res)

        return fused_results
