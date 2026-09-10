"""
AASI Multi-Fidelity Scientific Fabric — Models and Enums.

Defines canonical fidelity hierarchies, quality classifications, and data structures
for multi-fidelity aerodynamic results, cross-fidelity discrepancies, and uncertainty calibration.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib
import json


class FidelityLevel(str, Enum):
    """
    Explicit scientific fidelity tiers.
    Strictly preserves provenance; never conflates low/high fidelity or synthetic data.
    """
    EXPERIMENT = "EXPERIMENT"                     # Tier 1: Authoritative wind tunnel or flight test
    HIGH_FIDELITY_CFD = "HIGH_FIDELITY_CFD"       # Tier 2: Validated RANS/LES/DNS with spatial convergence
    LOW_FIDELITY_CFD = "LOW_FIDELITY_CFD"         # Tier 3: Coarse RANS, Euler, panel methods, XFOIL viscous
    ANALYTICAL = "ANALYTICAL"                     # Tier 4: Thin airfoil theory, Prandtl-Glauert, Tsiolkovsky
    SURROGATE = "SURROGATE"                       # Tier 5: Trained neural operator (e.g. AeroSurrogateV1)
    SYNTHETIC_TEST_DATA = "SYNTHETIC_TEST_DATA"   # Tier 6: Software test mock/fixture (quarantined)
    USER_PROVIDED = "USER_PROVIDED"               # Tier 7: Ingested user result pending scientific audit


class CFDQualityClassification(str, Enum):
    """
    Automated CFD result quality classification.
    Never assigns high quality merely because a solver exited with code 0.
    """
    UNVERIFIED = "UNVERIFIED"                     # Ingested, pending quality audit
    CONVERGED = "CONVERGED"                       # Residuals and forces stabilized
    GRID_CONVERGED = "GRID_CONVERGED"             # Verified by 3-grid ASME V&V 20 GCI study
    QUESTIONABLE = "QUESTIONABLE"                 # Minor force oscillations or marginal residuals
    DIVERGED = "DIVERGED"                         # Oscillating/exploding residuals
    INVALID = "INVALID"                           # Physical sanity violation (e.g. CD <= 0, NaN/Inf)


class FlowConditions(BaseModel):
    """Normalized aerodynamic operating conditions."""
    mach: float = Field(..., ge=0.0, le=10.0)
    reynolds: float = Field(..., ge=1e3, le=1e9)
    aoa_deg: float = Field(..., ge=-180.0, le=180.0)
    temperature_k: Optional[float] = Field(default=288.15)
    pressure_pa: Optional[float] = Field(default=101325.0)
    density_kg_m3: Optional[float] = Field(default=1.225)


class MultiFidelityResult(BaseModel):
    """Canonical representation of an aerodynamic measurement, simulation, or prediction."""
    result_id: str
    geometry: str
    geometry_hash: str
    fidelity: FidelityLevel
    quantity: str = Field(..., description="e.g. 'CL', 'CD', 'CM', 'CP'")
    value: float
    uncertainty: float = Field(default=0.0, ge=0.0, description="1-sigma uncertainty estimate")
    conditions: FlowConditions
    source: str = Field(..., description="Citation, archive name, or experiment ID")
    solver: Optional[str] = None
    solver_version: Optional[str] = None
    mesh_cells: Optional[int] = None
    provenance_hash: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.provenance_hash:
            self.provenance_hash = self.compute_provenance_hash()

    def compute_provenance_hash(self) -> str:
        payload = f"{self.result_id}:{self.geometry}:{self.fidelity.value}:{self.quantity}:{self.value}:{self.conditions.mach}:{self.conditions.reynolds}:{self.conditions.aoa_deg}:{self.source}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()



class DiscrepancyResult(BaseModel):
    """Measures the difference between lower and higher fidelity results under matched conditions."""
    geometry: str
    conditions: FlowConditions
    quantity: str
    high_fidelity_level: FidelityLevel
    low_fidelity_level: FidelityLevel
    high_fidelity_value: float
    low_fidelity_value: float
    absolute_discrepancy: float
    relative_discrepancy_pct: float
    bias_estimate: float
    is_statistically_significant: bool
    physical_explanation: Optional[str] = None
    provenance_hash: str


class UncertaintyCalibrationMetrics(BaseModel):
    """Statistical audit comparing predicted surrogate uncertainty against actual validation errors."""
    model_id: str
    dataset_version: str
    sample_count: int
    empirical_coverage_1sigma: float   # Target: ~68.3%
    empirical_coverage_2sigma: float   # Target: ~95.4%
    average_interval_width: float
    mean_absolute_calibration_error: float
    correlation_error_vs_uncertainty: float
    is_well_calibrated: bool
    recommended_scaling_factor: float = 1.0
    audit_notes: List[str] = Field(default_factory=list)
