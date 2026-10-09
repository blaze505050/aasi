# AASI Data Moat Strategy — Phase 19

> **Audit Date:** 2026-09-25

---

## Defensible Accumulation Potential

Over time, AASI can build defensible value through:

| Asset | Description | Defensibility | Status |
|---|---|---|---|
| **Verified Investigation Corpus** | Collection of completed, verified aerodynamic investigations with full provenance | **HIGH** — domain-specific, verified, hard to replicate | Architecture exists; needs volume |
| **Failure/Recovery Corpus** | Diagnosed CFD failures with repair plans and outcomes | **HIGH** — negative evidence is extremely valuable and rare | Architecture exists; needs volume |
| **Tool Performance Knowledge** | Which tools work best for which conditions (solver × regime × geometry) | **MEDIUM** — builds with usage | Implicit in memory; needs explicit tracking |
| **Experiment Selection History** | Which experiments were most informative for which questions | **MEDIUM** — builds with usage | Next-experiment engine exists |
| **Engineering Provenance Graph** | Complete graph of evidence → hypothesis → experiment → result chains | **HIGH** — unique to AASI | Investigation graph exists |
| **Domain-Specific Scientific Skills** | Learned patterns for common aerospace investigation types | **MEDIUM** — builds with volume | Demonstrations module exists |
| **Validated Surrogate Models** | Trained, verified physics surrogates with known accuracy bounds | **HIGH** — expensive to reproduce | Model zoo exists; needs real models |

---

## Strict Data Separation

```
┌─────────────────────────────────────────────────────────────┐
│ AASI GLOBAL KNOWLEDGE                                       │
│ • Seed corpus (NACA reports, textbook physics)              │
│ • Tool capability profiles                                  │
│ • Default physics models (panel solver, analytical)          │
│ • Public benchmark data (NACA 0012 validated polars)        │
│ • Open-source investigation templates                       │
├─────────────────────────────────────────────────────────────┤
│ CUSTOMER-PRIVATE KNOWLEDGE (per organization)               │
│ • Organization's scientific memory                           │
│ • Private investigations and evidence                        │
│ • Custom geometry data                                       │
│ • Proprietary CFD results                                    │
│ • Private hypotheses and experiment plans                    │
│ • Organization-specific tool configurations                  │
│ • Custom surrogate models                                    │
├─────────────────────────────────────────────────────────────┤
│ PUBLIC SCIENTIFIC KNOWLEDGE                                  │
│ • arXiv preprints (via connector)                            │
│ • NASA NTRS reports                                          │
│ • Published experimental data                                │
│ • Open benchmark datasets                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Ethics Principles

1. **Customer data NEVER silently becomes shared training data**
2. Customers can export all their data at any time
3. Customers can delete their data permanently
4. AASI global knowledge is transparent and auditable
5. Opt-in only: customers may choose to contribute anonymized investigation patterns to improve global knowledge
6. Public scientific knowledge sources are attributed with proper citations

---

## Moat Building Strategy

### Short-term (0-12 months)
- Accumulate verified investigation examples with full provenance
- Build failure diagnosis corpus from beta users
- Document tool performance characteristics across conditions

### Medium-term (12-24 months)
- Train domain-specific investigation skills from verified corpus
- Build experiment selection model from historical outcomes
- Create validated surrogate models for common geometries

### Long-term (24+ months)
- Engineering provenance graph becomes the authoritative record
- Investigation patterns enable autonomous skill acquisition
- Platform effects: more users → better tool knowledge → better recommendations
