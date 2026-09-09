# Provenance-First Architecture

AASI enforces cryptographic and bibliographical provenance for all scientific items. Unattributed scientific facts are never admitted to the knowledge base.

---

## Provenance Schema

Every document chunk, physical dataset, and cited snippet retains:

```python
class Provenance(BaseModel):
    source_organization: str    # e.g. NASA, NACA, ESA, ISRO, arXiv
    title: str                  # Title of technical report or dataset
    authors: List[str]          # Author list
    publication_date: str       # Year or ISO-8601 date
    source_url: Optional[str]   # Direct canonical link
    doi: Optional[str]          # Digital Object Identifier
    report_number: str          # Official report identifier (e.g. NACA-TR-824)
    dataset_id: Optional[str]   # Unique dataset identifier if applicable
    license: str                # Public Domain, CC-BY-4.0, etc.
    source_type: ScientificObjectType # DOCUMENT, DATASET, EXPERIMENT, SIMULATION...
    discipline: str             # Aerodynamics, Propulsion, Orbital, etc.
    version: str                # Version string
    ingestion_timestamp: str    # ISO-8601 timestamp of ingestion
    content_hash: str           # SHA-256 cryptographic checksum
```

---

## Scientific Object Distinction

To prevent presenting simulation outputs as empirical facts or vice versa, AASI explicitly classifies all scientific objects:

1. **`DOCUMENT`**: Technical papers, monographs, standards (NASA SP, NACA TR).
2. **`DATASET`**: Tabular and structured physical databases.
3. **`EXPERIMENT`**: Measured wind tunnel or flight telemetry.
4. **`SIMULATION`**: Deterministic solver outputs (OpenFOAM, SU2).
5. **`SURROGATE`**: Neural operator predictions (PINN, FNO, GNN).
6. **`ANALYTICAL_RESULT`**: Closed-form mathematical derivations.
7. **`RETRIEVED_REFERENCE`**: Specific literature passages cited during inference.

---

## Integrity & Checksum Verification

All documents and datasets compute a SHA-256 checksum during ingestion. When queries return data or passages, the original content hash is exposed in the provenance payload so researchers can independently verify that the retrieved excerpt has not been altered.
