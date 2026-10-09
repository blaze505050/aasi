# AASI Implementation Roadmap — Phase 35

> **Audit Date:** 2026-09-25

---

## Prioritization Framework

Every item is evaluated on:
1. **Customer value** — does a paying customer need this?
2. **Revenue impact** — does this unblock revenue?
3. **Scientific credibility** — does this affect trust?
4. **Gross margin** — does this protect margins?
5. **Speed to market** — can we ship it quickly?

---

## NOW (Next 30 days) — P0

Must-do before accepting first payment.

| # | Item | Category | Effort | Impact |
|---|---|---|---|---|
| N1 | **Fix default password creation** — only create in dev mode | Security | 1 hour | CRITICAL |
| N2 | **Enforce non-default secret key in production** — refuse to start | Security | 1 hour | CRITICAL |
| N3 | **Fix CORS wildcard default** — empty list default, require config | Security | 30 min | HIGH |
| N4 | **Add tarfile extraction filter** — `filter='data'` | Security | 30 min | MEDIUM |
| N5 | **Add Organization model** — basic org_id, name, owner, members | Architecture | 4 hours | HIGH |
| N6 | **Add Project model** — project_id, org_id, name, investigation_ids | Architecture | 2 hours | HIGH |
| N7 | **Add Plan/Entitlement model** — plan tiers with limits | Billing | 4 hours | HIGH |
| N8 | **Add UsageEvent tracking** — emit events on investigation/experiment/inference | Billing | 4 hours | HIGH |
| N9 | **Onboarding flow** — welcome screen, guided first investigation | UX | 8 hours | HIGH |
| N10 | **Investigation status bar** — prominent display of current state/cycle | UX | 4 hours | HIGH |
| N11 | **Evidence tier badges** — color-coded visual hierarchy | UX | 4 hours | MEDIUM |
| N12 | **Export report button in UI** — connect frontend to report generator | UX | 4 hours | HIGH |

**Total estimated: ~35 hours of focused work**

---

## NEXT (30-90 days) — P1

Customer-facing differentiation and growth foundations.

| # | Item | Category | Effort | Impact |
|---|---|---|---|---|
| X1 | **API key authentication** — for programmatic access | Platform | 8 hours | HIGH |
| X2 | **Investigation sharing** — shareable read-only URLs | Collaboration | 8 hours | MEDIUM |
| X3 | **Demo mode** — deterministic walkthrough with pre-computed data | Sales | 16 hours | HIGH |
| X4 | **Report export (PDF)** — professional investigation report | Feature | 12 hours | HIGH |
| X5 | **Observability dashboard** — usage metrics, job metrics, error rates | Operations | 8 hours | MEDIUM |
| X6 | **XFOIL integration hardening** — reliable XFOIL execution path | Tools | 8 hours | MEDIUM |
| X7 | **Token revocation** — server-side session blocklist | Security | 4 hours | MEDIUM |
| X8 | **Password complexity rules** — minimum strength requirements | Security | 2 hours | LOW |
| X9 | **`main.py` extraction** — move remaining endpoints to route modules | Architecture | 8 hours | MEDIUM |
| X10 | **Quota enforcement on plans** — check entitlements before investigation | Billing | 8 hours | HIGH |
| X11 | **Scientific tool interface standardization** — uniform ScientificTool protocol | Architecture | 8 hours | MEDIUM |
| X12 | **Commercial documentation** — Getting Started, Concepts, FAQ | Documentation | 16 hours | HIGH |

---

## LATER (90+ days) — P2

Growth features and enterprise readiness.

| # | Item | Category | Effort |
|---|---|---|---|
| L1 | Stripe billing integration | Billing | 24 hours |
| L2 | SSO / OAuth 2.0 | Enterprise | 24 hours |
| L3 | Audit logging | Enterprise | 16 hours |
| L4 | Team RBAC (viewer/editor/admin per project) | Collaboration | 16 hours |
| L5 | Python SDK (`pip install aasi`) | Platform | 24 hours |
| L6 | CLI tool for investigation management | Platform | 16 hours |
| L7 | 3D geometry support (STL/STEP import) | Feature | 40 hours |
| L8 | Additional solver adapters (SU2 staging) | Tools | 16 hours |
| L9 | Customer success dashboard | Operations | 16 hours |
| L10 | Webhook notifications for job completion | Platform | 8 hours |
| L11 | Data export / data deletion (GDPR) | Compliance | 8 hours |
| L12 | Private deployment package (Docker) | Enterprise | 16 hours |

---

## DO NOT BUILD

| Item | Reason |
|---|---|
| Real-time flight simulation | Outside product scope; AASI does investigation |
| CAD/geometry editor | Integrate with existing CAD tools instead |
| Custom LLM training | Use available models; focus on orchestration |
| Structural analysis (FEA) | Premature; focus on aerodynamics first |
| Multi-physics coupling | Premature; nail single-discipline first |
| Mobile app | Engineering work is done on desktop |
| Blockchain provenance | SHA-256 hashing is sufficient; blockchain adds complexity without value |
| AR/VR visualization | Gimmick; engineers need data, not immersion |
| Chat-based social features | AASI is a scientific tool, not a social platform |

---

## Smallest Version That Can Acquire First Paying Customer

```
AASI Minimum Paid Product = 
    Cognitive investigation loop (already exists)
  + Panel solver + analytical tools (already exist)
  + Colab CFD staging (already exists)
  + Verification + provenance (already exist)
  + Scientific memory (already exists)
  + Basic organization + project (N5, N6)
  + Plan-based entitlements (N7)
  + Usage tracking (N8)
  + Onboarding flow (N9)
  + Security fixes (N1-N4)
  + Export report button (N12)
```

**Estimated time to minimum paid product: ~35 hours of focused work**

The scientific core is already built. What's missing is the commercial wrapper.
