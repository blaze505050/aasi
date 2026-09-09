"""Scientific resolution models, epistemic classifications, and condition specifications."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EpistemicStatus(str, Enum):
    """Rigorous epistemic and provenance classification for all scientific results."""
    OFFICIAL_EXPERIMENT = "OFFICIAL_EXPERIMENT"      # Authentic peer-reviewed experimental report (e.g. NASA TN-D-628)
    VALIDATED_EXPERIMENT = "VALIDATED_EXPERIMENT"    # Independently reproduced experimental measurement
    OFFICIAL_CFD = "OFFICIAL_CFD"                    # Official agency benchmark CFD solution (e.g. NASA TMR)
    VALIDATED_CFD = "VALIDATED_CFD"                  # Local or peer-reviewed CFD with verified grid independence & y+ < 1
    LOCAL_CFD = "LOCAL_CFD"                          # Locally computed simulation without external experimental calibration
    UNVALIDATED_CFD = "UNVALIDATED_CFD"              # Simulation with incomplete grid convergence or high residuals
    SURROGATE_PREDICTION = "SURROGATE_PREDICTION"    # AI/ML neural surrogate prediction within validated envelope
    ANALYTICAL_RESULT = "ANALYTICAL_RESULT"          # Closed-form symbolic / numerical engineering solver (Astropy, SymPy)
    ESTIMATE = "ESTIMATE"                            # Engineering order-of-magnitude approximation
    DEMO_DATA = "DEMO_DATA"                          # Illustrative or synthetic test data for development
    NO_RESULT = "NO_RESULT"                          # No verified result exists in the declared domain


class ConditionMatchStatus(str, Enum):
    """Condition match classification with physical tolerance."""
    EXACT_MATCH = "EXACT_MATCH"                      # Match within strict physical tolerance
    NEAR_MATCH = "NEAR_MATCH"                        # Match within declared engineering tolerance
    INTERPOLATION_CANDIDATE = "INTERPOLATION_CANDIDATE" # Bounded by validated domain points; requires permission
    OUTSIDE_VALIDATION_DOMAIN = "OUTSIDE_VALIDATION_DOMAIN" # Query lies outside calibrated operational envelope
    NO_MATCH = "NO_MATCH"                            # Geometry or flow regime not covered


class FlowRegime(str, Enum):
    """Aerodynamic and fluid flow regime."""
    INCOMPRESSIBLE = "incompressible"                # Mach < 0.3
    SUBSONIC = "subsonic"                            # 0.3 <= Mach < 0.8
    TRANSONIC = "transonic"                          # 0.8 <= Mach < 1.2
    SUPERSONIC = "supersonic"                        # 1.2 <= Mach < 5.0
    HYPERSONIC = "hypersonic"                        # Mach >= 5.0
    UNKNOWN = "unknown"


class NormalizedConditions(BaseModel):
    """Canonical structured representation of physical engineering conditions extracted from queries."""
    geometry: Optional[str] = Field(None, description="Canonical geometry identifier (e.g. NACA 0012)")
    domain: str = Field("aerodynamics", description="Physical domain: aerodynamics, propulsion, orbital, thermal")
    mach: Optional[float] = Field(None, description="Freestream Mach number (dimensionless)")
    reynolds: Optional[float] = Field(None, description="Reynolds number based on characteristic chord (dimensionless)")
    aoa_deg: Optional[float] = Field(None, description="Angle of attack in degrees")
    flow_regime: FlowRegime = Field(FlowRegime.UNKNOWN, description="Classified flow regime")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional physical parameters with SI units")
    requested_outputs: List[str] = Field(default_factory=list, description="Target variables e.g. ['CD', 'CL', 'CM']")
    missing_critical_conditions: List[str] = Field(default_factory=list, description="Physically necessary inputs missing from query")
    raw_query: str = Field("", description="Original natural language query string")


class SourceDiscrepancy(BaseModel):
    """Analysis of numerical discrepancies across multiple scientific sources."""
    quantity: str = Field(..., description="Target quantity e.g. CD")
    sources_compared: List[Dict[str, Any]] = Field(default_factory=list, description="List of source results compared")
    max_relative_difference: float = Field(0.0, description="Max relative percentage difference across sources")
    physical_reasons: List[str] = Field(default_factory=list, description="Physical and numerical reasons for variation")
    recommended_source: Optional[str] = Field(None, description="Authoritative source recommended for design")


class ScientificResult(BaseModel):
    """Unified scientific result model with complete epistemic provenance."""
    result_id: str = Field(..., description="Unique result identifier")
    epistemic_status: EpistemicStatus = Field(..., description="Epistemic classification")
    quantity: str = Field(..., description="Physical variable name e.g. CD, CL, orbital_velocity")
    value: Optional[float] = Field(None, description="Numerical value of the result")
    units: str = Field("dimensionless", description="SI or normalized units")
    uncertainty: Optional[Dict[str, float]] = Field(None, description="Reported or estimated uncertainty bounds")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Operating conditions under which result holds")
    source: str = Field(..., description="Authoritative source or facility (e.g. NASA Langley Research Center)")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Bibliographical and cryptographic provenance")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Scientific confidence score")
    method: str = Field(..., description="Specific measurement or calculation method used")
    validation_status: str = Field("VALIDATED", description="VALIDATED, BENCHMARK, DEMO_DATA, UNVALIDATED")
    discrepancy_analysis: Optional[SourceDiscrepancy] = Field(None, description="Comparative discrepancy if multiple sources exist")
    notes: List[str] = Field(default_factory=list, description="Technical caveats and physical assumptions")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
