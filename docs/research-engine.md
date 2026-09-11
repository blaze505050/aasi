# AASI Scientific Research Engine & Two-Stage RAG

## 1. Research Mode Philosophy & Query Decomposition

AASI approaches complex aerospace questions as an investigative scientist rather than a superficial conversationalist:

```text
COMPLEX AEROSPACE INQUIRY
             │
             ▼
QUESTION DECOMPOSITION (Flight Regimes, Governing Equations, Unknowns)
             │
             ▼
TWO-STAGE SCIENTIFIC RAG (Primary Peer-Reviewed & Agency Reports)
             │
             ▼
CROSS-SOURCE CONFLICT ANALYSIS & EMPIRICAL RECONCILIATION
             │
             ▼
DETERMINISTIC SYMBOLIC CALCULATION (SymPy / Astropy / Pint)
             │
             ▼
SURROGATE INFERENCE (If within validated domain) OR CFD DECK GENERATION
             │
             ▼
EVIDENCE SYNTHESIS WITH FORMAL BIBLIOGRAPHIC CITATIONS
```

---

## 2. Epistemic Claim Segregation

In research mode synthesis, every factual assertion must be tagged with its epistemic lineage:

- **Established Fact:** Verifiable physical constants, standard atmospheric models, documented planetary parameters.
- **Calculated Result:** Quantities computed via SymPy or closed-form expressions (with reported numerical tolerance).
- **Experimental Result:** Wind tunnel polars or flight test measurements from cited agency reports.
- **Simulation Result:** Converged numerical solutions from OpenFOAM/SU2 with reported residual history.
- **Model Prediction:** Surrogate evaluations inside verified parameter hypercubes (with epistemic variance bands).
- **Inference / Physical Deduction:** Derived consequences based on established aerodynamic theory (e.g., boundary layer thickening leading to trailing-edge stall).
- **Speculation / Open Hypothesis:** Clearly marked unverified hypotheses requiring future experiment or simulation.

---

## 3. Two-Stage Scientific RAG & Authority Reranker (`backend/knowledge/reranker.py`)

Standard vector similarity search frequently prioritizes unverified recent preprints or popular web articles over foundational NASA technical reports. AASI implements a **two-stage epistemic reranking pipeline**:

### Stage 1: Dense & Lexical Candidate Retrieval
- Retrieves $3 \times k$ candidates using hybrid embedding search and BM25 lexical token matching.

### Stage 2: Scientific Authority Reranking
1. **Epistemic Authority Weighting:**
   - Peer-Reviewed Journal Articles (AIAA, JFM): **$\times 1.35$**
   - Agency Technical Reports (NASA NTRS, NACA, ESA, DLR): **$\times 1.25$**
   - Conference Proceedings (AIAA SciTech): **$\times 1.10$**
   - Academic Preprints (arXiv): **$\times 0.90$**
   - Commercial Specifications / Whitepapers: **$\times 0.75$**
2. **Exact Scientific Identifier Boosting:**
   - Detects standard alphanumeric report identifiers (`NASA-TM-XXXX`, `NASA-TN-XXXX`, `AIAA-XXXX`, `NACA-TR-XXXX`, `arXiv:XXXX.XXXXX`).
   - Grants an additive $+0.25$ boost if an exact query identifier matches document metadata.
3. **Diversity & Redundancy Suppression:**
   - Computes token-level Jaccard similarity across candidate snippets from the same source document.
   - If overlap exceeds $60\%$, the lower-scoring duplicate is suppressed to promote diverse multi-source evidence.

---

## 4. Autonomous Research Loop Guardrails

The autonomous research loop orchestrates campaigns to resolve active learning objectives:
1. **Objectives:** Quantified uncertainty reduction goals (e.g. `OBJ-AERO-001`: high-AoA stall characterization).
2. **Simulation Campaigns:** Automated batch job generation based on maximum epistemic variance sampling.
3. **Strict Autonomy Guardrails:**
   - **No Synthetic Data Generation:** AASI is strictly forbidden from creating artificial simulation data to "fill in" missing test points.
   - **Fail-Closed Retraining:** Surrogates are retrained only against immutable datasets with verified SHA-256 provenance.
   - **4-Tier Promotion Gate:** Any retrained model must pass Loss Convergence, Benchmark Non-Regression, Physics Positivity ($C_D > 0$), and ASME V&V 20 uncertainty encompassing before promotion.
