"""
AASI CFD Knowledge Retrieval Engine.
Retrieves and ranks nearest-neighbor CFD cases and authentic wind tunnel polars.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.dataset.catalog import CFDCatalog
from backend.dataset.similarity import AerodynamicSimilarity
from backend.dataset.schema import CFDRecord


class CFDRetrievalEngine:
    """Retrieves verified CFD and wind tunnel aerodynamic cases."""

    def __init__(self, catalog: Optional[CFDCatalog] = None):
        self.catalog = catalog or CFDCatalog()

    def retrieve_similar(
        self,
        geometry: str,
        alpha_deg: float,
        reynolds: float,
        mach: float = 0.15,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k closest records from the catalog, ranked by composite aerodynamic distance.
        """
        all_records = self.catalog.query()
        ranked = []

        for rec in all_records:
            dist = AerodynamicSimilarity.compute_distance(
                target_geom=geometry,
                target_alpha=alpha_deg,
                target_re=reynolds,
                target_mach=mach,
                candidate_geom=rec.geometry.geometry_id,
                candidate_alpha=rec.flow.aoa_deg,
                candidate_re=rec.flow.reynolds,
                candidate_mach=rec.flow.mach,
            )
            ranked.append({
                "record_id": rec.record_id,
                "dataset_name": rec.dataset_name,
                "geometry": rec.geometry.geometry_id,
                "alpha_deg": rec.flow.aoa_deg,
                "reynolds": rec.flow.reynolds,
                "mach": rec.flow.mach,
                "distance": dist,
                "results": {
                    "cl": rec.results.cl,
                    "cd": rec.results.cd,
                    "cm": rec.results.cm,
                },
                "provenance": {
                    "epistemic_source": rec.provenance.epistemic_source,
                    "merkle_root": rec.provenance.merkle_provenance_root,
                },
            })

        ranked.sort(key=lambda x: x["distance"])
        return ranked[:top_k]
