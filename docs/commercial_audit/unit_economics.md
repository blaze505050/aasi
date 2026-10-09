# AASI Unit Economics — Phase 8 & 30

> **Audit Date:** 2026-09-25
> **⚠️ All figures are modeled estimates based on assumptions. Not validated financial data.**

---

## Cost Structure per Customer

### Variable Costs (per customer/month)

| Cost Category | Professional ($99/mo) | Team ($399/mo) | Enterprise (~$2,000/mo) |
|---|---|---|---|
| **AI Inference** | ~$5-15 (500K tokens × $0.01-0.03/K) | ~$20-60 (2M tokens) | ~$50-200 (custom) |
| **Compute** | $0 (BYOC — Colab/user HPC) | $0 (BYOC) | $0 (customer-provided) |
| **Storage** | ~$0.50 (5 GB × $0.10/GB) | ~$2.50 (25 GB) | ~$5-50 (custom) |
| **Bandwidth** | ~$0.50 | ~$2 | ~$5-20 |
| **Infrastructure** (shared) | ~$3-5 | ~$5-10 | ~$10-30 |
| **Total Variable** | **~$9-21** | **~$30-75** | **~$70-300** |

### Gross Margin Estimates

| Tier | MRR | Variable Costs | Gross Profit | Gross Margin |
|---|---|---|---|---|
| Professional | $99 | ~$15 | ~$84 | **~85%** |
| Team (5 users) | $399 | ~$50 | ~$349 | **~87%** |
| Enterprise | $2,000 | ~$150 | ~$1,850 | **~92%** |

---

## Critical Design Principle: Compute Cost Isolation

AASI achieves high gross margins because:

```
AASI Revenue = Intelligence + Orchestration + Verification + Memory + Provenance
                (Software — scales near-zero marginal cost)

Compute Cost = Customer-owned
               LOCAL → user's workstation
               COLAB → user's Google account
               HPC → user's cluster
               CLOUD → metered, explicit, customer pays
```

**AASI never silently absorbs uncontrolled compute costs.**

The Compute Provider Abstraction already exists in the codebase:

| Provider | File | Status | Cost to AASI |
|---|---|---|---|
| `LOCAL` | `compute/local.py` | ✅ Implemented | $0 |
| `COLAB` | `compute/colab.py` | ✅ Implemented | $0 |
| `REMOTE_HPC` | `compute/remote_hpc.py` | ✅ Implemented | $0 |
| `USER_PROVIDED` | `compute/user_provided.py` | ✅ Implemented | $0 |
| `CLOUD_HPC` | Not yet | ❌ Planned | Metered to customer |
| `SURROGATE` | `science/surrogate.py` | ✅ Implemented | $0 (local inference) |
| `ANALYTICAL` | `physics/panel_solver.py` | ✅ Implemented | $0 |

---

## AI Inference Cost Modeling

| Model Type | Cost Assumption | Usage Pattern |
|---|---|---|
| Local Ollama (qwen2.5:0.5b) | $0 | Default — zero cost |
| Cloud LLM API (GPT-4o, Claude) | $0.01-0.03/K tokens | Optional — user provides API key |
| Embedding model (local) | $0 | Local sentence-transformers |

**Key architecture choice:** AASI defaults to local Ollama models, keeping AI inference cost at $0 for the platform. Cloud LLM APIs are optional and can be customer-provided.

---

## Revenue Scaling Model

| Milestone | Customers | Mix | Est. Monthly Revenue |
|---|---|---|---|
| 10 customers | 7 Pro, 2 Team, 1 Enterprise | — | ~$2,900 |
| 50 customers | 30 Pro, 12 Team, 5 Enterprise, 3 Free | — | ~$17,770 |
| 100 customers | 50 Pro, 25 Team, 10 Enterprise, 15 Free | — | ~$34,900 |

---

## Break-Even Analysis (Estimated)

| Fixed Cost Category | Monthly Estimate |
|---|---|
| Cloud infrastructure (API servers) | $200-500 |
| Domain, DNS, CDN | $50 |
| Monitoring/observability | $50-100 |
| CI/CD | $50-100 |
| **Total Fixed** | **$350-750** |

**Break-even:** ~5-8 Professional customers or ~2 Team customers.

---

## Margin Risk Factors

| Risk | Impact | Mitigation |
|---|---|---|
| Customers demanding AASI-hosted compute | Destroys margins | BYOC architecture is default; cloud compute is explicitly metered |
| Cloud LLM API costs spike | Reduces margins | Local Ollama is default; cloud LLM is customer-provided API key |
| Heavy storage users | Storage cost increase | Per-GB metering above tier limit |
| Support burden | Scales with customers | Self-serve documentation, community support for free tier |
| Enterprise customization | Engineering cost | Separate enterprise pricing covers customization |
