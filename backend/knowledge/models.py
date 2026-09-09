"""Scientific knowledge and dataset data models with provenance-first design."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScientificObjectType(str, Enum):
    """Explicit taxonomy of scientific objects to avoid false equivalences."""
    DOCUMENT = "DOCUMENT"                      # Technical reports, journal papers, manuals
    DATASET = "DATASET"                        # Tabular, structured physical datasets
    EXPERIMENT = "EXPERIMENT"                  # Empirical wind tunnel or flight observations
    SIMULATION = "SIMULATION"                  # Deterministic CFD, FEA, or numerical runs
    SURROGATE = "SURROGATE"                    # ML/AI surrogate model predictions
    ANALYTICAL_RESULT = "ANALYTICAL_RESULT"    # Exact closed-form mathematical equations
    RETRIEVED_REFERENCE = "RETRIEVED_REFERENCE"# Citations and passages from verified literature


class Provenance(BaseModel):
    """Mandatory cryptographic and bibliographical provenance for every scientific item."""
    source_organization: str = Field(..., description="Organization publishing the item, e.g. NASA, NACA, ESA, ISRO, arXiv")
    title: str = Field(..., description="Title of the paper, technical report, or dataset")
    authors: List[str] = Field(default_factory=list, description="List of author names")
    publication_date: Optional[str] = Field(None, description="Publication date or year (ISO-8601 or YYYY)")
    source_url: Optional[str] = Field(None, description="Direct URL to source repository or document")
    doi: Optional[str] = Field(None, description="Digital Object Identifier if available")
    report_number: Optional[str] = Field(None, description="Official technical report number e.g. NACA-TR-824, NASA-TN-D-628")
    dataset_id: Optional[str] = Field(None, description="Unique dataset identifier if applicable")
    license: str = Field("Public Domain", description="License or access conditions, e.g. Public Domain, CC-BY-4.0")
    source_type: ScientificObjectType = Field(ScientificObjectType.DOCUMENT, description="Categorization of scientific object")
    discipline: str = Field("Aerospace", description="Scientific discipline, e.g. Aerodynamics, Propulsion, Orbital Mechanics")
    version: str = Field("1.0", description="Document or dataset version")
    ingestion_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp of ingestion into AASI"
    )
    content_hash: str = Field(..., description="SHA-256 cryptographic checksum of original text or binary payload")

    @classmethod
    def compute_hash(cls, content: str | bytes) -> str:
        """Compute SHA-256 checksum for given string or bytes."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()


class Equation(BaseModel):
    """First-class representation of scientific equations preserving context and notation."""
    equation_id: str = Field(..., description="Unique identifier for the equation")
    equation_text: str = Field(..., description="Plain-text representation or formula")
    latex: Optional[str] = Field(None, description="LaTeX representation if extractable")
    source_document_id: str = Field(..., description="ID of the parent document")
    page: Optional[int] = Field(None, description="Page number where equation appears")
    surrounding_context: str = Field("", description="Surrounding text or paragraph defining the equation")
    variables: Dict[str, str] = Field(default_factory=dict, description="Identified variable names and descriptions")
    units: Dict[str, str] = Field(default_factory=dict, description="Identified units for variables")
    extraction_confidence: float = Field(1.0, ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)")


class Chunk(BaseModel):
    """Structure-aware document chunk preserving section hierarchy and provenance."""
    chunk_id: str = Field(..., description="Unique ID for this chunk (e.g. doc-id#p1-s2)")
    document_id: str = Field(..., description="ID of the source document")
    source_id: str = Field(..., description="Organization or repository source ID")
    page: Optional[int] = Field(None, description="Page number")
    section: Optional[str] = Field(None, description="Section or chapter name (e.g. 'Methodology', 'Results')")
    heading: Optional[str] = Field(None, description="Subheading or subsection title")
    content: str = Field(..., description="Text content of the chunk")
    equations: List[Equation] = Field(default_factory=list, description="Equations located within this chunk")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted tables or structured data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional structured metadata")
    content_hash: str = Field(..., description="SHA-256 checksum of chunk text")


class Document(BaseModel):
    """Full scientific document representation with structural metadata."""
    document_id: str = Field(..., description="Unique identifier for the document")
    title: str = Field(..., description="Document title")
    abstract: Optional[str] = Field(None, description="Abstract or executive summary")
    provenance: Provenance = Field(..., description="Full bibliographical and cryptographic provenance")
    raw_path: Optional[str] = Field(None, description="Local or cached storage path")
    chunks: List[Chunk] = Field(default_factory=list, description="Structured chunks extracted from document")
    equations: List[Equation] = Field(default_factory=list, description="All equations extracted from document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata and key-value fields")


class CFDClassification(str, Enum):
    """Classification of CFD and numerical simulations."""
    REFERENCE_CFD = "REFERENCE_CFD"      # Benchmark peer-reviewed CFD dataset
    NEW_CFD = "NEW_CFD"                  # Newly executed or candidate CFD run
    ML_SURROGATE = "ML_SURROGATE"        # Neural operator / surrogate model prediction


class CFDDataModel(BaseModel):
    """Detailed CFD physics and numerical simulation metadata schema."""
    geometry: str = Field(..., description="Airfoil, wing, or body geometry name (e.g. 'NACA 0012', 'ONERA M6')")
    mesh: Optional[str] = Field(None, description="Mesh type and cell count (e.g. 'Structured C-grid, 250k cells')")
    solver: str = Field(..., description="Solver name and version (e.g. 'OpenFOAM v2312', 'SU2 v7.5')")
    governing_equations: str = Field("RANS", description="Governing equations: RANS, Euler, LES, DNS, Navier-Stokes")
    boundary_conditions: Dict[str, str] = Field(default_factory=dict, description="Boundary condition definitions")
    initial_conditions: Dict[str, Any] = Field(default_factory=dict, description="Initial flow conditions")
    mach: float = Field(..., ge=0.0, description="Freestream Mach number")
    reynolds: float = Field(..., gt=0.0, description="Reynolds number based on chord")
    aoa_deg: float = Field(..., description="Angle of attack in degrees")
    temperature_k: Optional[float] = Field(None, description="Freestream temperature in Kelvin")
    pressure_pa: Optional[float] = Field(None, description="Freestream static pressure in Pascals")
    density_kg_m3: Optional[float] = Field(None, description="Freestream density in kg/m^3")
    velocity_m_s: Optional[float] = Field(None, description="Freestream velocity in m/s")
    turbulence_model: Optional[str] = Field(None, description="Turbulence closure model (e.g. 'Spalart-Allmaras', 'k-omega SST')")
    convergence_criteria: Optional[str] = Field(None, description="Convergence criterion (e.g. 'Residuals < 1e-6')")
    cl: Optional[float] = Field(None, description="Calculated or measured Lift Coefficient")
    cd: Optional[float] = Field(None, description="Calculated or measured Drag Coefficient")
    cm: Optional[float] = Field(None, description="Calculated or measured Pitching Moment Coefficient")
    cp_distribution: Optional[List[Dict[str, float]]] = Field(None, description="Pressure coefficient distribution (x/c, Cp)")
    velocity_field_available: bool = Field(False, description="Whether 2D/3D field snapshots exist")
    pressure_field_available: bool = Field(False, description="Whether 2D/3D field snapshots exist")
    residual_history: Optional[List[float]] = Field(None, description="Convergence residual history")
    classification: CFDClassification = Field(CFDClassification.REFERENCE_CFD, description="Classification of simulation")


class Dataset(BaseModel):
    """Physical dataset catalog model supporting experimental and computational aerospace data."""
    dataset_id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Descriptive name of the dataset")
    source: str = Field(..., description="Source institution or project")
    version: str = Field("1.0", description="Dataset version")
    license: str = Field("Public Domain", description="Usage license")
    geometry: str = Field(..., description="Test geometry (e.g. 'NACA 0012')")
    physical_domain: str = Field("aerodynamics", description="Domain: aerodynamics, CFD, propulsion, structures, thermal, atmosphere, orbital, reentry, experimental")
    variables: List[str] = Field(default_factory=list, description="Variables included in dataset e.g. ['alpha', 'CL', 'CD', 'CM']")
    units: Dict[str, str] = Field(default_factory=dict, description="Units for variables e.g. {'alpha': 'deg', 'CL': 'dimensionless'}")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Test conditions e.g. {'Mach': 0.3, 'Reynolds': 500000}")
    resolution: Optional[str] = Field(None, description="Spatial/temporal resolution")
    is_experimental: bool = Field(True, description="True if experimental measurements; False if computational")
    solver: Optional[str] = Field(None, description="CFD solver if computational")
    turbulence_model: Optional[str] = Field(None, description="Turbulence model if computational")
    validation_status: str = Field("VALIDATED", description="Validation level: VALIDATED, BENCHMARK, PRELIMINARY, UNVALIDATED")
    uncertainty: Optional[Dict[str, float]] = Field(None, description="Measurement or calculation uncertainty bounds")
    citation: str = Field(..., description="Bibliographical citation string")
    location: Optional[str] = Field(None, description="Relative file path or URI to data payload")
    checksum: str = Field(..., description="SHA-256 checksum of raw dataset")
    cfd_metadata: Optional[CFDDataModel] = Field(None, description="CFD metadata if simulation dataset")
    data_points: List[Dict[str, Any]] = Field(default_factory=list, description="Tabular sample data points")


class Citation(BaseModel):
    """Citation reference for scientific answers."""
    source_title: str = Field(..., description="Title of cited publication")
    source_org: str = Field(..., description="Publishing organization (NASA, NACA, ESA, etc.)")
    year: Optional[int] = Field(None, description="Publication year")
    report_number: Optional[str] = Field(None, description="Technical report number")
    url: Optional[str] = Field(None, description="Direct URL")
    page: Optional[int] = Field(None, description="Page number of cited excerpt")
    relevance_score: float = Field(..., description="Relevance score in [0, 1]")


class RetrievalResult(BaseModel):
    """Unified search and retrieval result with traceable provenance."""
    document_id: str
    chunk_id: str
    title: str
    source: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    page: Optional[int] = None
    snippet: str
    url: Optional[str] = None
    relevance: float
    provenance: Provenance
    object_type: ScientificObjectType = ScientificObjectType.RETRIEVED_REFERENCE
    equations: List[Equation] = Field(default_factory=list)
