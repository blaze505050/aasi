# Scientific Data Sources & Registry Adapters

AASI enforces an extensible `SourceRegistry` that defines how external scientific repositories and technical publications are accessed, ingested, and cited.

---

## Registered Sources

### 1. NASA Technical Reports Server (`NASA_NTRS`)
- **Status**: `IMPLEMENTED`
- **Organization**: National Aeronautics and Space Administration (NASA)
- **Endpoint**: `https://ntrs.nasa.gov/api/citations`
- **Access / License**: Public Domain (NASA Technical Reports)
- **Capabilities**: REST API search, metadata normalization, PDF extraction via `pypdf` with safety size limits.

### 2. NACA Technical Reports (`NACA`)
- **Status**: `IMPLEMENTED`
- **Organization**: National Advisory Committee for Aeronautics (1915–1958)
- **Access / License**: Public Domain (US Government Work pre-1958)
- **Capabilities**: Historical aerodynamic technical reports, variable-density wind tunnel measurements, airfoil families.

### 3. arXiv Open Access Preprints (`ARXIV`)
- **Status**: `IMPLEMENTED`
- **Organization**: Cornell University / arXiv.org
- **Endpoint**: `http://export.arxiv.org/api/query`
- **Access / License**: Open Access (CC-BY, arXiv.org non-exclusive)
- **Scope**: `physics.flu-dyn`, `astro-ph`, aerospace engineering preprints.

### 4. European Space Agency (`ESA`)
- **Status**: `NOT IMPLEMENTED — REASON`
- **Organization**: European Space Agency (ESA)
- **Reason**: ESA does not offer an open unauthenticated REST API for bulk automated document downloading. Ingestion of ESA publications requires verified open-access document curation.
- **Future Roadmap**: Open Archives Initiative Protocol for Metadata Harvesting (OAI-PMH) integration.

### 5. Indian Space Research Organisation (`ISRO`)
- **Status**: `NOT IMPLEMENTED — REASON`
- **Organization**: Indian Space Research Organisation (ISRO)
- **Reason**: ISRO technical documents and mission summaries are distributed across dynamic web portals without an automated public search API. Blind web scraping is prohibited.
- **Future Roadmap**: Validated open mission telemetry datasets and payload archive ingestion.

### 6. Curated Open Datasets (`OPEN_DATASETS`)
- **Status**: `IMPLEMENTED`
- **Organization**: AASI Open Aerodynamic Benchmark Catalog
- **Access / License**: Public Domain / CC0
- **Scope**: Experimental wind tunnel aerodynamic polars and reference CFD simulations.
