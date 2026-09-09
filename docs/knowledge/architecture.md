# Scientific Knowledge & Dataset Architecture

AASI (Autonomous Aerospace Scientific Intelligence) is designed around a multi-tier scientific reasoning architecture where the language model orchestrates verified physical tools, structured dataset catalogs, and literature retrieval rather than memorizing all aerospace knowledge.

```
Aerospace LLM (Orchestrator / Synthesizer)
         ↓
Scientific Agent & Result-Resolution Hierarchy
         ↓
┌──────────────────────┬────────────────────────┬────────────────────────┐
│  Knowledge & RAG     │  Physical Datasets     │  Engineering Tools     │
│  (NASA/NACA/arXiv)   │  (Wind Tunnel / CFD)   │  (Astropy / RocketPy)  │
│                      │                        │                        │
│  • FAISS Vector IP   │  • Condition Search    │  • Orbital Mechanics   │
│  • Exact BM25 Match  │  • NACA 0012 Polars    │  • Rocket Equation     │
│  • Provenance Tracking│  • CFD SA Benchmarks   │  • SymPy Verification  │
└──────────────────────┴────────────────────────┴────────────────────────┘
         ↓
Validation Engine & Provenance Audit
         ↓
Engineered Result (+ Evidence, Assumptions, Provenance, Uncertainty)
```

---

## Status Classification

| Subsystem Component | Status | Details |
| :--- | :--- | :--- |
| **Document Data Model & Provenance** | **IMPLEMENTED** | Typed models (`Document`, `Chunk`, `Equation`, `Provenance`) with SHA-256 integrity. |
| **Scientific Object Taxonomy** | **IMPLEMENTED** | 7 distinct object types (`DOCUMENT`, `DATASET`, `EXPERIMENT`, `SIMULATION`, `SURROGATE`, `ANALYTICAL_RESULT`, `RETRIEVED_REFERENCE`). |
| **Source Registry** | **IMPLEMENTED** | `NASA_NTRS`, `NACA`, `ARXIV`, `ESA`, `ISRO`, `OPEN_DATASETS` with access rules. |
| **NASA / NACA Ingestion Pipeline** | **IMPLEMENTED** | Search, metadata normalization, `pypdf` text extraction, structure chunking. |
| **Structure-Aware Chunking** | **IMPLEMENTED** | Section hierarchy preservation, page retention, LaTeX/ASCII equation extraction. |
| **FAISS Vector Index** | **IMPLEMENTED** | `FAISSVectorIndex` with normalized inner product (cosine similarity) and JSON metadata. |
| **Hybrid Scientific Retrieval** | **IMPLEMENTED** | Blended semantic vector search + exact aerospace keyword matching + metadata filters. |
| **Dataset Registry & CFD Schema** | **IMPLEMENTED** | `CFDDataModel`, `DatasetRegistry`, physical condition query engine (Mach, Re, AoA). |
| **Scientific RAG & Security** | **IMPLEMENTED** | Prompt injection quarantine (`<UNTRUSTED_REFERENCE_DATA>`), answer synthesis. |
| **Physics AI Surrogate Stubs** | **EXPERIMENTAL** | Abstract interfaces (`PINN`, `PINO`, `FNO`, `GNN`, `PhysicsNeMo`) for Phase 4. |
| **Autonomous CFD Solver Runs** | **PLANNED** | Scheduled for Phase 5 (OpenFOAM / SU2 automated meshing and execution). |
| **Automated ESA / ISRO Live Scrapers** | **NOT IMPLEMENTED** | Documented limitation: ESA/ISRO lack open unauthenticated bulk APIs. Manual curation required. |
