# Aerospace Dataset & CFD Data Schema

AASI provides structured models for experimental wind-tunnel datasets and computational fluid dynamics (CFD) simulation archives.

---

## Dataset Schema

```python
class Dataset(BaseModel):
    dataset_id: str             # e.g. AASI-EXP-AERO-NACA0012-M03-RE5E5
    name: str                   # Descriptive benchmark title
    source: str                 # NASA Langley, AGARD, etc.
    version: str                # Version string
    license: str                # Public Domain / CC0
    geometry: str               # e.g. NACA 0012
    physical_domain: str        # aerodynamics, CFD, propulsion, structures, thermal
    variables: List[str]        # ['alpha', 'cl', 'cd', 'cm']
    units: Dict[str, str]       # Units dictionary
    conditions: Dict[str, Any]  # {'Mach': 0.3, 'Reynolds': 500000}
    resolution: Optional[str]   # Grid resolution or AoA increment
    is_experimental: bool       # True for wind tunnel; False for CFD
    validation_status: str      # VALIDATED, BENCHMARK, PRELIMINARY
    uncertainty: Dict[str, float] # Measurement or numerical bounds
    citation: str               # Full bibliographical citation
    checksum: str               # SHA-256 checksum of tabular payload
    cfd_metadata: Optional[CFDDataModel]
    data_points: List[Dict[str, Any]]
```

---

## CFD Physics Metadata Model

For numerical fluid dynamics runs and future AI surrogates:

```python
class CFDDataModel(BaseModel):
    geometry: str               # Airfoil or vehicle geometry
    mesh: Optional[str]         # Mesh topology and cell count
    solver: str                 # e.g. OpenFOAM v2312 (simpleFoam)
    governing_equations: str    # RANS, Euler, LES, DNS
    boundary_conditions: Dict[str, str]
    initial_conditions: Dict[str, Any]
    mach: float                 # Freestream Mach
    reynolds: float             # Reynolds number
    aoa_deg: float              # Angle of attack
    temperature_k: Optional[float]
    pressure_pa: Optional[float]
    density_kg_m3: Optional[float]
    velocity_m_s: Optional[float]
    turbulence_model: Optional[str] # Spalart-Allmaras, k-omega SST
    convergence_criteria: Optional[str] # Residual tolerance
    cl: Optional[float]         # Lift coefficient
    cd: Optional[float]         # Drag coefficient
    cm: Optional[float]         # Moment coefficient
    cp_distribution: Optional[List[Dict[str, float]]]
    classification: CFDClassification # REFERENCE_CFD, NEW_CFD, ML_SURROGATE
```

---

## Condition-Based Query Engine

Researchers can query the dataset registry by physical conditions:

```http
POST /api/knowledge/datasets/query
Content-Type: application/json

{
  "geometry": "NACA 0012",
  "mach": 0.3,
  "reynolds": 500000.0,
  "aoa_deg": 8.0
}
```

Returns:
- Exact experimental data point ($C_D = 0.0142, C_L = 0.820$)
- Uncertainty bounds ($\pm 0.0005$ for $C_D$, $\pm 0.015$ for $C_L$)
- Source citation (`NASA TN-D-628`)
- Provenance checksum
