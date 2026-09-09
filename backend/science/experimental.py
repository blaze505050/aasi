"""Experimental aerospace database cataloging physical wind tunnel and flight test observations."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .models import EpistemicStatus, ScientificResult
from backend.knowledge.models import Provenance


class ExperimentalDataset(BaseModel):
    """Rigorous data model for empirical aerodynamic wind tunnel or flight test series."""
    dataset_id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Human-readable title of experimental test series")
    geometry: str = Field(..., description="Test article geometry e.g. NACA 0012")
    facility: str = Field(..., description="Wind tunnel or test facility e.g. Langley Low-Turbulence Pressure Tunnel")
    test_article_id: Optional[str] = Field(None, description="Physical model or article serial number")
    report_id: str = Field(..., description="Official publication or report number e.g. NASA TN-D-628")
    source: str = Field(..., description="Research organization e.g. NASA Langley Research Center")
    publication_year: int = Field(..., description="Year of publication")
    citation: str = Field(..., description="Full bibliographical reference")
    license: str = Field("Public Domain", description="Data license")
    epistemic_status: EpistemicStatus = Field(EpistemicStatus.OFFICIAL_EXPERIMENT, description="Epistemic status")
    validation_status: str = Field("VALIDATED", description="VALIDATED, DEMO_DATA, UNVERIFIED_SEED")
    conditions: Dict[str, Any] = Field(..., description="Baseline conditions: Mach, Reynolds, temperature, pressure")
    domain_envelope: Dict[str, Any] = Field(default_factory=dict, description="Operational envelope bounds")
    variables: List[str] = Field(default_factory=lambda: ["aoa", "cl", "cd", "cm"], description="Measured quantities")
    units: Dict[str, str] = Field(default_factory=dict, description="Units dictionary")
    uncertainty: Dict[str, float] = Field(default_factory=dict, description="Reported instrumentation uncertainty bounds")
    instrumentation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Balance type, pressure taps, calibration")
    data_points: List[Dict[str, Any]] = Field(default_factory=list, description="Tabular experimental observations")
    checksum: str = Field(..., description="SHA-256 checksum of raw tabular records")


class ExperimentalDatabase:
    """In-memory database for verified physical wind tunnel and flight test observations."""

    def __init__(self):
        self._datasets: Dict[str, ExperimentalDataset] = {}

    def register(self, dataset: ExperimentalDataset):
        """Register an experimental dataset."""
        self._datasets[dataset.dataset_id] = dataset

    def get(self, dataset_id: str) -> Optional[ExperimentalDataset]:
        """Retrieve dataset by ID."""
        return self._datasets.get(dataset_id)

    def list_datasets(self, geometry: Optional[str] = None) -> List[ExperimentalDataset]:
        """List experimental datasets with optional geometry filter."""
        res = list(self._datasets.values())
        if geometry:
            clean_geo = geometry.replace(" ", "").replace("-", "").lower()
            res = [d for d in res if clean_geo in d.geometry.replace(" ", "").replace("-", "").lower()]
        return res

    def query_measurement(
        self,
        geometry: str,
        mach: Optional[float] = None,
        reynolds: Optional[float] = None,
        aoa_deg: Optional[float] = None,
        target_variable: str = "CD",
        tolerance_mach: float = 0.05,
        tolerance_reynolds_rel: float = 0.25,
        tolerance_aoa: float = 0.5,
    ) -> List[ScientificResult]:
        """Search experimental records for measurements matching flight conditions."""
        results: List[ScientificResult] = []
        clean_target_geo = geometry.replace(" ", "").replace("-", "").lower()

        for ds_id, ds in self._datasets.items():
            ds_geo = ds.geometry.replace(" ", "").replace("-", "").lower()
            if clean_target_geo not in ds_geo and ds_geo not in clean_target_geo:
                continue

            ds_mach = ds.conditions.get("Mach") or ds.conditions.get("mach")
            ds_re = ds.conditions.get("Reynolds") or ds.conditions.get("reynolds")

            # Check macro conditions
            if mach is not None and ds_mach is not None:
                if abs(float(ds_mach) - float(mach)) > tolerance_mach:
                    continue

            if reynolds is not None and ds_re is not None:
                rel_diff = abs(float(ds_re) - float(reynolds)) / float(reynolds)
                if rel_diff > tolerance_reynolds_rel:
                    continue

            # Check points
            var_key = target_variable.lower()
            for pt in ds.data_points:
                pt_aoa = pt.get("aoa") if "aoa" in pt else (pt.get("alpha") if "alpha" in pt else pt.get("aoa_deg"))
                if aoa_deg is not None and pt_aoa is not None:
                    if abs(float(pt_aoa) - float(aoa_deg)) > tolerance_aoa:
                        continue

                # Point matched
                val = pt.get(var_key)
                if val is not None:
                    unc_val = ds.uncertainty.get(var_key, 0.0005)
                    results.append(
                        ScientificResult(
                            result_id=f"EXP-{ds.dataset_id}-AOA{pt_aoa}",
                            epistemic_status=ds.epistemic_status,
                            quantity=target_variable,
                            value=float(val),
                            units=ds.units.get(var_key, "dimensionless"),
                            uncertainty={var_key: unc_val},
                            conditions={
                                "geometry": ds.geometry,
                                "mach": ds_mach,
                                "reynolds": ds_re,
                                "aoa_deg": pt_aoa,
                                "facility": ds.facility,
                            },
                            source=ds.source,
                            provenance={
                                "report_id": ds.report_id,
                                "citation": ds.citation,
                                "publication_year": ds.publication_year,
                                "checksum": ds.checksum,
                                "license": ds.license,
                            },
                            confidence=0.98,
                            method=f"Wind Tunnel Observation ({ds.facility})",
                            validation_status=ds.validation_status,
                            notes=[
                                f"Empirical observation from {ds.report_id}.",
                                f"Instrumentation uncertainty: +/- {unc_val}.",
                            ],
                        )
                    )

        return results
