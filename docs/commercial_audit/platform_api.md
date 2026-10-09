# AASI Platform API — Phase 20

> **Audit Date:** 2026-09-25

---

## Current API Surface

AASI already has an extensive REST API. Current endpoints include:

### Core Investigation
| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| POST | `/api/v1/cognitive/investigate` | Start cognitive investigation | ✅ |
| GET | `/api/v1/cognitive/session/{id}` | Get investigation state | ✅ |
| POST | `/api/v1/cognitive/advance/{id}` | Advance investigation cycle | ✅ |
| GET | `/api/v1/cognitive/brain/{id}` | Get brain/world model state | ✅ |

### Science & Evidence
| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| POST | `/api/science/resolve` | 8-level scientific resolution | ✅ |
| POST | `/api/science/normalize` | NL → structured conditions | ✅ |
| POST | `/api/v1/hypotheses/generate` | Generate competing hypotheses | ✅ |
| GET | `/api/v1/evidence/reconciliation` | Evidence comparison | ✅ |

### Compute & Execution
| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| POST | `/api/v1/compute/submit` | Submit compute job | ✅ |
| GET | `/api/v1/compute/jobs/{id}` | Job status | ✅ |
| POST | `/api/v1/compute/upload/{id}` | Upload results archive | ✅ |
| GET | `/api/v1/compute/colab/{id}` | Get Colab notebook | ✅ |

### Tools & Solvers
| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| GET | `/api/tools` | List available tools | ✅ |
| GET | `/api/solvers` | Discover available solvers | ✅ |
| POST | `/api/simulations` | Execute simulation | ✅ |

### Knowledge & Memory
| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| POST | `/api/knowledge/search` | Literature search | ✅ |
| GET | `/api/knowledge/sources` | List knowledge sources | ✅ |
| GET | `/api/v1/memory` | Query scientific memory | ✅ |

### AeroDB & Export
| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| POST | `/api/aerodb/generate` | Generate aero database | ✅ |
| GET | `/api/aerodb/{id}/export` | Export (DATCOM/SHABP/CSV/JSON) | ✅ |

### Auth & System
| Method | Endpoint | Purpose | Status |
|---|---|---|---|
| POST | `/api/v1/auth/login` | Authenticate user | ✅ |
| POST | `/api/v1/auth/register` | Register user | ✅ |
| GET | `/api/health` | System health | ✅ |
| GET | `/api/v1/observability/metrics` | System metrics | ✅ |

---

## Proposed API Primitives for External Integration

The following API structure would enable embedding AASI into external engineering workflows:

```
# Investigation Lifecycle
POST   /api/v1/investigations                    # Create investigation
GET    /api/v1/investigations/{id}                # Get investigation state
POST   /api/v1/investigations/{id}/advance        # Advance to next cycle
GET    /api/v1/investigations/{id}/world-model    # Get world model
GET    /api/v1/investigations/{id}/hypotheses     # Get hypotheses
GET    /api/v1/investigations/{id}/experiments    # Get experiment plan
GET    /api/v1/investigations/{id}/evidence       # Get evidence
GET    /api/v1/investigations/{id}/report         # Get investigation report
POST   /api/v1/investigations/{id}/submit-result  # Submit external result

# Scientific Memory
POST   /api/v1/memory/search                     # Search by conditions
POST   /api/v1/memory/store                      # Store verified result
GET    /api/v1/memory/{id}                        # Get memory entry

# Compute
POST   /api/v1/compute/route                     # Get routing recommendation
POST   /api/v1/compute/stage                     # Stage computation
POST   /api/v1/compute/submit-result             # Upload result
GET    /api/v1/compute/jobs                       # List jobs

# Export
GET    /api/v1/investigations/{id}/export/{format} # Export report
```

---

## Integration Targets

AASI API should eventually be embeddable into:

| Platform Type | Integration Method | Priority |
|---|---|---|
| Internal engineering dashboards | REST API + webhooks | **P1** |
| CI/CD engineering pipelines | REST API + CLI tool | **P2** |
| PLM systems (Teamcenter, Windchill) | REST API + connector | **P3** |
| Digital twin platforms | REST API | **P3** |
| Simulation workflow managers | REST API + webhook callbacks | **P2** |
| Jupyter/Python notebooks | Python SDK | **P2** |

---

## API Authentication (Proposed)

| Method | Use Case | Status |
|---|---|---|
| Session token (current) | Browser-based UI | ✅ Implemented |
| API key | Programmatic access | ❌ Needed |
| OAuth 2.0 / JWT | Enterprise SSO integration | ❌ Future |
