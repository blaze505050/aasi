# AASI Scientific Source Fabric Architecture

## 1. Architectural Purpose & Unified Connector Interface

The AASI Scientific Source Fabric manages external data retrieval across aerospace agencies, academic preprint servers, institutional archives, and commercial aerospace companies.

To eliminate hallucinated connectivity, every data source extends a unified abstract interface:

```python
class BaseSourceConnector(ABC):
    """Abstract interface governing all external data connectors."""
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SourceDocument]: ...

    @abstractmethod
    def fetch(self, document_id: str) -> Optional[SourceDocument]: ...

    @abstractmethod
    def normalize(self, raw_payload: Dict[str, Any]) -> SourceDocument: ...

    @abstractmethod
    def verify(self, document: SourceDocument) -> bool: ...

    @abstractmethod
    def get_provenance(self, document_id: str) -> Optional[ProvenanceChain]: ...
```

---

## 2. Declared Access Methods & Freshness Semantics

Every data source in the AASI registry declares its legitimate access mechanism:

| Access Method | Description | Implementation Status |
|:---|:---|:---:|
| `LIVE_API` | Authenticated or public REST API with real-time network retrieval. | **[REAL]** (arXiv XML Atom API) |
| `PUBLIC_DOWNLOAD` | Direct HTTPS download of open-access public files with checksum validation. | **[REAL]** (NASA NTRS public URLs, UIUC Airfoil DB) |
| `RSS` | Real-time XML/RSS news and launch schedule syndication. | **[REAL]** (Spaceflight News API integration) |
| `PUBLIC_WEB` | Headless parsing of published public regulatory filings or press archives. | **[REAL]** (SpaceX Starship public license filings) |
| `STATIC_SEED` | Curated offline baseline records packaged with the repository. | **[REAL]** (ISRO, ESA offline mission seeds) |
| `METADATA_ONLY` | Bibliographic index records without on-disk raw PDF/polar files. | **[REAL]** (NTRS search index) |
| `MANUAL_IMPORT` | Datasets or case outputs provided by the user via file upload. | **[REAL]** (OpenFOAM logs, CSV polars) |
| `DISABLED` | Connectors temporarily taken offline or gated pending legal/API verification. | **[REAL]** (Proprietary CAD/mesh portals) |

### Freshness Semantics
Every retrieved piece of information reports:
1. `publication_timestamp`: Date when the document or polar was originally published.
2. `retrieval_timestamp`: ISO 8601 UTC timestamp of retrieval into AASI.
3. `age_days`: Elapsed time since retrieval.
4. `freshness_state`: `FRESH` ($\le 7$ days), `STABLE_HISTORICAL` (verified archived literature), or `STALE` (exceeds TTL).
5. `is_live`: Explicit boolean preventing static data from pretending to be real-time telemetry.

---

## 3. Source Categorization & Authority

### A. Government & Scientific Institutions
- **NASA NTRS & Open Data:** Index of peer-reviewed technical reports (e.g. NASA-TM-4083, NASA-TN-D-628). Epistemic classification: `AGENCY_TECHNICAL_REPORT`.
- **arXiv (`physics.flu-dyn`, `astro-ph`):** Automated live XML retrieval via `ArxivConnector` (`backend/sources/arxiv_connector.py`). Epistemic classification: `UNVERIFIED_PREPRINT`.
- **ESA & ISRO:** Static seed catalogs with honest diagnostic messaging indicating offline state until legitimate API endpoints are authenticated.

### B. Commercial Aerospace Entities (SpaceX, Rocket Lab, Blue Origin)
AASI enforces a strict separation:
- **PUBLICLY VERIFIED:** FAA environmental assessment filings, published Falcon 9 user manuals, NASA commercial crew milestone reports, public technical presentations.
- **PROPRIETARY / UNAVAILABLE:** Internal CAD models, proprietary raptor chamber CFD, unpublished telemetry. AASI **never implies access** to private proprietary engineering data.

---

## 4. Source Fabric Diagnostics (`GET /api/sources/diagnostics`)

The system provides real-time transparency into the operational state of all connectors:
- Active connectors and their access methods
- In-memory document counts
- Last refresh timestamp
- Verification levels (Cryptographic SHA-256 vs Metadata-Only)
