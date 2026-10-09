# AASI Open Core Strategy — Phase 28

> **Audit Date:** 2026-09-25

---

## Strategy Recommendation: Open Core

AASI should adopt an **open-core strategy** where the core scientific investigation framework is open-source, and commercial features are proprietary.

---

## What Should Be Open Source

| Component | Rationale |
|---|---|
| Panel solver (`physics/panel_solver.py`) | Demonstrates engineering credibility; attracts contributors |
| Airfoil parser (`physics/airfoil_parser.py`) | Utility value drives adoption |
| ASME V&V 20 implementation (`cfd/asme_vv20.py`) | Standards implementation should be verifiable |
| Evidence data models (`science/evidence.py` — models only) | Enables community tooling |
| Scientific memory data models | Enables interoperability |
| AeroDB export formats (DATCOM, SHABP, CSV) | Industry-standard format support |
| Basic CLI for local investigation | Developer adoption |
| Example investigation notebooks | Demonstrates value |
| Test suite (selected) | Builds trust in correctness |
| Documentation | Drives adoption |

**Purpose:** Build credibility, attract aerospace engineers, create an ecosystem.

---

## What Should Be Paid

| Component | Rationale |
|---|---|
| Cognitive orchestrator (full loop) | Core differentiator |
| Multi-cycle autonomous investigation | Primary product value |
| Scientific memory (persistence + search) | Retention/stickiness feature |
| Compute orchestration (Colab/HPC routing) | Operational value |
| Investigation reports (professional PDF) | Customer deliverable |
| Team/Organization management | Collaboration value |
| API access (programmatic) | Integration value |
| Private deployment | Enterprise value |
| Advanced tools (XFOIL adapter, CFD staging) | Power user value |
| Usage analytics and observability | Enterprise operational value |

---

## What Should Be Free Tier

| Component | Limit | Rationale |
|---|---|---|
| Single-user investigations | 5/month | Experience the product |
| Panel solver + analytical tools | Unlimited | Zero marginal cost, builds habit |
| Basic scientific memory | 100 entries | Taste of retention value |
| Community support | — | Low cost |
| JSON export | — | Basic utility |

---

## What Should Be Enterprise-Only

| Component | Rationale |
|---|---|
| Private deployment (air-gapped) | Deployment cost + support |
| SSO/SAML integration | Integration complexity |
| Audit logging | Compliance requirement |
| Custom tool integrations | Engineering effort |
| Dedicated support + SLA | Support cost |
| Custom data retention | Compliance requirement |

---

## Open Source License Recommendation

**Server Side Public License (SSPL)** or **Business Source License (BSL 1.1)**

Rationale:
- Prevents cloud providers from hosting AASI as a competing service
- Allows self-hosting for development and evaluation
- Converts to open source after time delay (BSL: 3-4 years)
- Used successfully by MongoDB, MariaDB, CockroachDB, Sentry

Alternative: **Apache 2.0** for the open-source components if a cleaner separation is maintained between open and proprietary.

---

## Risk Analysis

| Risk | Mitigation |
|---|---|
| Open-source components used without paying | Core value (orchestration, memory, reports) is proprietary |
| Competitor forks open-source | BSL/SSPL prevents commercial hosting; cognitive loop is proprietary |
| Community expects more for free | Clear free tier limits; transparent about what's paid |
| Too little open → no adoption | Panel solver + airfoil tools + export formats provide genuine standalone value |
| Too much open → revenue leakage | Cognitive loop + memory + orchestration are the product; these stay proprietary |
