# AASI Commercial Architecture — Phase 6

> **Audit Date:** 2026-09-25

---

## Current Architecture Assessment

### What Exists

| Concept | Status | Implementation |
|---|---|---|
| User | ✅ Implemented | `auth/models.py` — User with roles (RESEARCHER, ENGINEER, ADMIN) |
| Session | ✅ Implemented | HMAC-signed session tokens with expiry |
| Password Hashing | ✅ Implemented | PBKDF2-HMAC-SHA256, 100K iterations |
| Rate Limiting | ✅ Implemented | Sliding window rate limiter |
| Job Quotas | ✅ Implemented | Per-user concurrent job limits |
| Job Ownership | ✅ Implemented | Tenant-isolated job access |
| Investigation | ✅ Implemented | `CognitiveInvestigationSession` |
| Evidence | ✅ Implemented | 9-tier `ScientificEvidenceItem` |
| Scientific Memory | ✅ Implemented | Persistent, searchable |
| Provenance | ✅ Implemented | SHA-256 content hashing |
| Compute Routing | ✅ Implemented | LOCAL/COLAB/HPC/USER_PROVIDED |
| File Upload | ✅ Implemented | Archive upload with size limits |

### What Is Missing

| Concept | Status | Priority |
|---|---|---|
| Organization | ❌ Not implemented | **P1** — required for team/billing |
| Project | ❌ Not implemented | **P1** — required for investigation grouping |
| Team | ❌ Not implemented | **P2** — needed for collaboration |
| Subscription / Plan | ❌ Not implemented | **P1** — required for billing |
| Usage Tracking (metered) | ❌ Not implemented | **P1** — required for billing |
| Billing Integration | ❌ Not implemented | **P2** — Stripe/payment later |
| API Keys | ❌ Not implemented | **P2** — for programmatic access |
| Audit Log | ❌ Not implemented | **P2** — for enterprise |
| SSO / OAuth | ❌ Not implemented | **P3** — enterprise only |

---

## Proposed Entity Hierarchy

```
TENANT (implicit — deployment level)
└── ORGANIZATION
    ├── members: [User]
    ├── plan: Plan
    ├── usage: UsageTracker
    ├── settings: OrgSettings
    └── PROJECTS
        ├── members: [User]
        └── INVESTIGATIONS
            ├── world_model: AerospaceWorldModel
            ├── hypotheses: [StructuredHypothesis]
            ├── experiments: [Experiment]
            ├── evidence: [ScientificEvidenceItem]
            ├── memory: [ScientificMemoryEntry]
            ├── timeline: [CognitiveTransitionRecord]
            └── ARTIFACTS
                ├── reports: [ScientificReport]
                ├── case_files: [CFDCase]
                ├── exports: [ExportFile]
                └── provenance: [ProvenanceRecord]
```

---

## Data Model Additions Required

### Organization

```python
class Organization(BaseModel):
    org_id: str           # ORG-XXXX
    name: str
    slug: str             # URL-safe unique identifier
    plan_id: str          # Reference to active plan
    owner_id: str         # User ID of owner
    member_ids: List[str] # User IDs
    created_at: str
    settings: OrgSettings
```

### Project

```python
class Project(BaseModel):
    project_id: str       # PRJ-XXXX
    org_id: str           # Parent organization
    name: str
    description: str
    member_ids: List[str]
    investigation_ids: List[str]
    created_at: str
```

### Plan & Entitlement

```python
class Plan(BaseModel):
    plan_id: str
    name: str             # "researcher", "professional", "team", "enterprise"
    max_investigations_per_month: int
    max_experiments_per_investigation: int
    max_storage_gb: float
    max_ai_tokens_per_month: int
    features: List[str]   # ["private_memory", "exports", "api_access"]

class UsageEvent(BaseModel):
    event_id: str
    org_id: str
    user_id: str
    event_type: str       # "investigation_started", "experiment_run", "ai_inference", "storage_used"
    quantity: float
    timestamp: str
    metadata: Dict[str, Any]
```

---

## Architecture Principles

1. **Organization-scoped isolation** — All investigations, memory, and evidence belong to an organization
2. **Project-level grouping** — Investigations are organized into projects
3. **Usage metering before billing** — Track everything, bill later
4. **Plan-based entitlements** — Features unlocked by plan, not hardcoded
5. **API-key based programmatic access** — Separate from session tokens
6. **Compute costs explicit** — AASI intelligence is the product; compute is customer-provided or metered separately

---

## Migration Path

The current architecture stores data in flat JSON files under `data/`. The migration path:

1. **Phase A (Now):** Add Organization/Project models as wrappers around existing data
2. **Phase B (Next):** Add UsageEvent tracking to all investigation endpoints
3. **Phase C (Later):** Add billing provider integration (Stripe)
4. **Phase D (Enterprise):** Add SSO, audit logs, data retention policies
