# AASI Monetization Model — Phase 7

> **Audit Date:** 2026-09-25
> **⚠️ All prices are PROPOSED ASSUMPTIONS, not market facts. To be validated with customer interviews.**

---

## Monetization Principles

1. **The unit of value is the scientific investigation**, not the chat message
2. **AASI sells intelligence + orchestration + verification + memory**, not compute
3. **Compute costs should not destroy margins** — BYOC is default
4. **Each paid tier must unlock meaningful economic value**, not cosmetic features
5. **Free tier exists for adoption**, not charity — it creates the funnel

---

## Tier Structure

### Free / Research Tier

| Feature | Limit |
|---|---|
| Investigations per month | 5 |
| Experiments per investigation | 3 |
| AI reasoning tokens | 50K/month |
| Scientific memory entries | 100 |
| Storage | 500 MB |
| Compute | Colab (user-provided) only |
| Tools | Panel solver, analytical |
| Exports | Basic JSON |
| Support | Community |

**Purpose:** University students, evaluation, funnel creation.

---

### Professional — PROPOSED: $99/month

| Feature | Limit |
|---|---|
| Investigations per month | 25 |
| Experiments per investigation | 10 |
| AI reasoning tokens | 500K/month |
| Scientific memory entries | 1,000 |
| Storage | 5 GB |
| Compute | Colab + user-provided HPC |
| Tools | All (OpenFOAM staging, XFOIL, panel, analytical) |
| Exports | JSON, CSV, DATCOM, SHABP, PDF reports |
| Private memory | ✅ |
| API access | ✅ (rate-limited) |
| Support | Email, 48h response |

**Target:** Individual engineers, consultants, PhD researchers with grants.

---

### Team — PROPOSED: $399/month (up to 5 users, +$79/additional user)

| Feature | Limit |
|---|---|
| Investigations per month | 100 |
| Experiments per investigation | 25 |
| AI reasoning tokens | 2M/month |
| Scientific memory entries | 10,000 |
| Storage | 25 GB |
| Compute | All providers + user HPC |
| Organization workspace | ✅ |
| Shared scientific memory | ✅ |
| Projects | ✅ |
| RBAC (roles) | ✅ |
| Collaboration | ✅ |
| Exports | All formats + team reports |
| API access | ✅ |
| Support | Email, 24h response |

**Target:** UAV startups, small aerospace teams, consultancies.

---

### Enterprise — PROPOSED: Custom pricing (starting ~$2,000/month)

| Feature | Limit |
|---|---|
| Investigations | Unlimited |
| Experiments | Unlimited |
| AI reasoning tokens | Custom |
| Storage | Custom |
| Compute | All + private HPC + on-prem |
| SSO / SAML | ✅ |
| Audit logs | ✅ |
| Data retention policies | ✅ |
| Private deployment | ✅ |
| Custom tool integrations | ✅ |
| Dedicated support | ✅ |
| SLA | ✅ |

**Target:** Aerospace OEMs, defense, large R&D organizations.

---

## Monetization Dimensions

| Dimension | Free | Professional | Team | Enterprise |
|---|---|---|---|---|
| AI investigation reasoning | Limited | Standard | Advanced | Unlimited |
| Scientific memory | 100 entries | 1,000 | 10,000 | Unlimited |
| Compute orchestration | Colab only | + user HPC | + team HPC | + private |
| Storage (CAS) | 500 MB | 5 GB | 25 GB | Custom |
| Team/Org management | ❌ | ❌ | ✅ | ✅ |
| RBAC / Audit | ❌ | ❌ | Basic | Full |
| API access | ❌ | Rate-limited | Standard | Unlimited |
| Private deployment | ❌ | ❌ | ❌ | ✅ |
| Export formats | JSON | All standard | All + custom | All + custom |
| Support | Community | Email 48h | Email 24h | Dedicated |

---

## Usage-Based Overages (Proposed)

For Professional and Team tiers:
- Additional AI tokens: $10 per 100K tokens
- Additional storage: $5 per GB/month
- Additional investigations: $5 per investigation

---

## Revenue Model Options

| Model | Fit for AASI | Rationale |
|---|---|---|
| Pure subscription | ✅ Good base | Predictable revenue, simple |
| Pure usage-based | ⚠️ Risky | Unpredictable, hard to forecast |
| **Hybrid (subscription + usage)** | ✅ Best fit | Base subscription for access + overages for heavy use |
| Enterprise license | ✅ For large customers | Custom pricing for private deployment |
| API pricing | ✅ For integrations | Per-call pricing for embedded use cases |

**Recommended:** Hybrid (base subscription + metered overages) for self-serve tiers, custom enterprise pricing for large customers.
