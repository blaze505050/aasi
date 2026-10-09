# AASI Security Audit — Phase 17

> **Audit Date:** 2026-09-25
> **Classification:** Internal — Pre-Commercial Security Review

---

## Summary

AASI has a **solid security foundation** with proper password hashing, signed session tokens, rate limiting, tenant-isolated job ownership, and anti-fabrication enforcement. However, several issues must be addressed before charging customers.

---

## Authentication & Session Management

| Check | Status | Detail |
|---|---|---|
| Password hashing algorithm | ✅ PASS | PBKDF2-HMAC-SHA256, 100,000 iterations |
| Salt generation | ✅ PASS | `secrets.token_hex(16)` — cryptographically random |
| Constant-time comparison | ✅ PASS | `hmac.compare_digest()` used |
| Session token signing | ✅ PASS | HMAC-SHA256 with server-side secret |
| Token expiration | ✅ PASS | Configurable (default 24h) |
| Token nonce | ✅ PASS | `secrets.token_hex(8)` per token |
| Default password in prod | ⚠️ **FAIL** | `aerospace-secure-password-2026` created on startup |
| Default secret key | ⚠️ **FAIL** | Hardcoded fallback `aasi-secret-key-phase27-production-secure` |
| Token revocation | ⚠️ MISSING | No server-side session invalidation |
| Password complexity rules | ⚠️ MISSING | No enforcement of strength requirements |

---

## Authorization & Access Control

| Check | Status | Detail |
|---|---|---|
| Role-based access | ✅ PASS | RESEARCHER, ENGINEER, ADMIN roles |
| Job ownership isolation | ✅ PASS | `verify_job_ownership()` enforced |
| Admin bypass | ✅ PASS | Admin can access all jobs |
| Rate limiting | ✅ PASS | Sliding window, configurable per-minute limit |
| Concurrent job quotas | ✅ PASS | Per-user limits enforced |
| Archive size limits | ✅ PASS | Configurable max (default 100 MB) |
| Organization isolation | ⚠️ MISSING | No Organization entity — all users share namespace |
| Project-level RBAC | ⚠️ MISSING | No project-level access control |

---

## Network & CORS

| Check | Status | Detail |
|---|---|---|
| CORS configuration | ⚠️ **WARN** | Default includes wildcard `*` in deployment config |
| CORS in production | ✅ PASS | `.env.example` correctly specifies restricted origins |
| Production readiness check | ✅ PASS | `validate_production_readiness()` flags wildcard CORS |
| HTTPS enforcement | ⚠️ MISSING | Not enforced at application level (relies on reverse proxy) |
| CSRF protection | ℹ️ N/A | API-only backend; no cookie-based form auth |

---

## Input Validation & Injection

| Check | Status | Detail |
|---|---|---|
| Request validation | ✅ PASS | Pydantic models with field constraints |
| SQL injection | ✅ PASS | No SQL database — JSON file storage |
| Path traversal | ⚠️ **REVIEW** | File operations should validate against base directory |
| Shell injection | ✅ PASS | No `subprocess` or `os.system` calls found in backend |
| File upload limits | ✅ PASS | `max_archive_size_bytes` enforced |
| Archive extraction (Zip bomb) | ⚠️ **REVIEW** | `tarfile.extractall()` used with deprecation warning |
| Command execution | ✅ PASS | OpenFOAM execution is sandboxed in runner, not backend |

---

## Secrets Management

| Check | Status | Detail |
|---|---|---|
| Secret key from env | ✅ PASS | `AASI_SECRET_KEY` env variable supported |
| Default secret key detection | ✅ PASS | Production readiness check flags defaults |
| Secrets in code | ⚠️ **WARN** | Default secret key string in `deployment/config.py:21` |
| API keys in logs | ✅ PASS | No API key logging found |
| User data files | ⚠️ **REVIEW** | User credentials stored in `data/auth/users.json` — should be encrypted at rest |

---

## Compute & Remote Execution

| Check | Status | Detail |
|---|---|---|
| Colab notebook injection | ✅ PASS | Generated notebooks use parameterized templates |
| Colab solver version spoofing | ✅ PASS | `colab.py:603` explicitly rejects fake/mock/spoof solver versions |
| CFD runtime timeout | ✅ PASS | `max_cfd_runtime_seconds` enforced |
| Anti-fabrication rule | ✅ PASS | `forbid_synthetic_substitution` and `stage_10_gate_enforced` |
| Runner sandboxing | ✅ PASS | Dedicated runner agent with sandbox module |
| SSRF | ⚠️ **REVIEW** | Source connectors (NASA, arXiv) make outbound HTTP — should validate URLs |

---

## Findings Summary

### Critical (Must Fix Before Charging)

| # | Finding | Location | Remediation |
|---|---|---|---|
| S1 | Default user with known password created on startup | `auth/security.py:58-66` | Only create in dev mode when `AASI_DEV_MODE=true` |
| S2 | Default secret key allows token forgery | `deployment/config.py:21` | Require non-default value; refuse to start without |

### High (Fix Before Launch)

| # | Finding | Location | Remediation |
|---|---|---|---|
| S3 | CORS wildcard default | `deployment/config.py:46` | Change default to empty list; require explicit configuration |
| S4 | No token revocation mechanism | `auth/security.py` | Add server-side token blocklist |
| S5 | User credentials file unencrypted | `data/auth/users.json` | File-level encryption or migrate to database |

### Medium (Plan to Fix)

| # | Finding | Location | Remediation |
|---|---|---|---|
| S6 | No password complexity enforcement | `auth/security.py` | Add minimum length, complexity rules |
| S7 | `tarfile.extractall()` without filter | `compute/colab.py:559` | Use `filter='data'` parameter (Python 3.12+) |
| S8 | No Organization-level isolation | `auth/` | Add Organization model with data isolation |
| S9 | Source connector URL validation | `sources/` | Validate outbound URLs against allowlist |

### Low

| # | Finding | Location | Remediation |
|---|---|---|---|
| S10 | Placeholder hashes in surrogate models | `science/surrogates.py` | Validate against actual model checksums |
