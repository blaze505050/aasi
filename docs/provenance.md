# AASI Cryptographic Provenance Architecture

## 1. Core Principle: "Where Did This Number Come From?"

In scientific engineering, a numerical value without provenance is useless. AASI ensures that every parameter, aerodynamic coefficient, and literature quote can answer:

> **"Where did this number come from?"**

with a traceable, cryptographically signed chain of custody.

---

## 2. Distinction Between Cryptographic Hashes

A common engineering error is conflating metadata hashes with raw file hashes. AASI formally separates three distinct cryptographic hashes:

1. **Document Metadata Hash (`metadata_hash`):**
   - SHA-256 computed across bibliographic metadata: `title + author + publication_year + report_number`.
   - Used for deduplication and source catalog identification.
2. **Downloaded File Hash (`file_hash`):**
   - SHA-256 computed across the exact binary byte stream of the downloaded PDF, dat, or CSV file.
   - Guaranteed immutable fingerprint of the physical external artifact.
3. **Extracted Text / Data Fragment Hash (`fragment_hash`):**
   - SHA-256 computed across the normalized UTF-8 text chunk, coordinate table, or polar snippet.
   - Referenced directly in scientific RAG citations.

---

## 3. The `ProvenanceChain` Data Model (`backend/sources/models.py`)

Every scientific fragment ingested into AASI is bound to an immutable `ProvenanceChain`:

```python
class ProvenanceChain(BaseModel):
    chain_id: str
    source_organization: str          # e.g., "NASA Langley Research Center"
    source_title: str                 # e.g., "Aerodynamic Characteristics of the NACA 0012 Airfoil"
    authors: List[str]                # e.g., ["Critzos, C. C.", "Heyson, H. H.", "Boswinkle, R. W."]
    publication_date: str             # e.g., "1955-01-01"
    report_number: Optional[str]      # e.g., "NACA-TN-3361"
    source_url: Optional[str]         # e.g., "https://ntrs.nasa.gov/citations/19930084346"
    license: str                      # e.g., "Public Domain (US Government Work)"
    access_method: str                # e.g., "PUBLIC_DOWNLOAD"
    document_hash: str                # SHA-256 hash of source metadata
    file_hash: Optional[str]          # SHA-256 hash of raw on-disk file
    chunk_hash: str                   # SHA-256 hash of extracted text/table
    epistemic_classification: str     # e.g., "AGENCY_TECHNICAL_REPORT"
    ingested_at: str                  # UTC ISO 8601 timestamp
```

---

## 4. Academic Citation Formatting (`format_scientific_citation`)

AASI formats retrieved literature into academically rigorous bibliographic citations equipped with cryptographic content hashes and epistemic classification badges:

```text
**[AGENCY_TECHNICAL_REPORT]** Critzos, C. C., Heyson, H. H., Boswinkle, R. W. (1955). *Aerodynamic Characteristics of the NACA 0012 Airfoil at Angles of Attack from 0° to 360°*. NASA Langley Research Center. Report: [NACA-TN-3361]. URL: <https://ntrs.nasa.gov/citations/19930084346> [Hash: `e3b0c44298fc`]
```

- **Agency Technical Reports & Peer-Reviewed Papers:** Linked with permanent DOIs or NTRS URLs.
- **Preprints:** Explicitly prepended with `**[UNVERIFIED_PREPRINT]**` to prevent researchers mistaking draft manuscripts for validated standards.
