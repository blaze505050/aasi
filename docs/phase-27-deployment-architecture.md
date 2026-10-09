# AASI Phase 27: Public Deployment Architecture

## 1. Architectural Philosophy & Governing Doctrine
The primary directive of **AASI Phase 27** is to transition the autonomous aerospace scientific intelligence platform from a local research workbench to a **publicly deployable, production-ready scientific application** with a **zero-local-load guarantee**.

Under the **Absolute Anti-Fabrication Rule**:
1. Zero computational CFD burden is placed on the operator's laptop: all meshing, simulation solving, and heavy post-processing are delegated to external compute fabrics (Google Colab and Remote HPC clusters).
2. Under zero-cost mode or when remote hardware is temporarily unavailable, AASI will **never substitute missing CFD solutions with synthetic fixtures or fabricated numbers**.
3. Every displayed numerical quantity carries immutable cryptographic provenance and epistemic classification.

```
+-------------------------------------------------------------------------------+
|                       AASI Phase 27 Production Topography                     |
+-------------------------------------------------------------------------------+
                                     |
               Public Internet HTTPS (Cloudflare / Reverse Proxy)
                                     |
             +-----------------------+-----------------------+
             |                                               |
      Port 3000 (Next.js 14)                          Port 8000 (FastAPI)
   +-----------------------+                       +-----------------------+
   |  Frontend Workspace   |                       |    Control Plane      |
   | - SSR & Static Pages  |  SSE Streams & APIs   | - Modular API Routers |
   | - Real-time SSE Feed  | <-------------------> | - Cryptographic Auth  |
   | - Epistemic Badges    |                       | - Resource Governance |
   | - Interactive Polars  |                       | - CAS Object Store    |
   +-----------------------+                       +-----------------------+
                                                               |
                                              +----------------+----------------+
                                              |                                 |
                                     Google Colab Fabric              Remote HPC Cluster
                                    (User-Authorized 1-Click)           (SLURM Batch Queue)
                                    - Automated case deck               - #SBATCH Job Script
                                    - 15-step OpenFOAM run              - Non-mutating retries
                                    - HMAC signed archive               - Merkle verified
```

---

## 2. Containerization & Deployment Orchestration

AASI is containerized into two lean, production-grade microservices coordinated by `docker-compose.yml`:

### A. Backend Control Plane (`Dockerfile.backend`)
- **Base**: `python:3.11-slim`
- **Exposed Port**: `8000`
- **Responsibilities**:
  - Modular API routing (`/api/v1/auth`, `/api/v1/compute`, `/api/v1/jobs`, `/api/v1/results`, `/api/v1/observability`).
  - Persistent 15-state HMAC-SHA256 job queue.
  - Multi-tenant tenant isolation and token lifecycle.
  - Content-Addressed Storage (CAS) with 2-byte prefix sharding (`objects/sha256/ab/abcdef...`).
  - Server-Sent Events (SSE) stream multiplexing with auto-replay for disconnected clients.

### B. Frontend Workspace (`Dockerfile`)
- **Base**: `node:18-alpine` multi-stage build (`builder` -> `runner`)
- **Exposed Port**: `3000`
- **Output**: Optimized static export and standalone Next.js 14 production bundle.
- **Features**:
  - Zero hardcoded `localhost` URLs: dynamically resolves reverse-proxy routes via `NEXT_PUBLIC_API_URL`.
  - Tailored aerospace dark-mode aesthetics with Glassmorphism and Lucide telemetry icons.
  - Real-time SSE execution logs with honest status indicators (`REMOTE STATUS UNKNOWN` when external VM telemetry cannot be observed directly).

---

## 3. Cryptographic Authentication & Multi-Tenant Isolation

### A. Password Security
- Passwords are encrypted using **PBKDF2-HMAC-SHA256** with 100,000 iterations and 16-byte random cryptographic salts.
- Formatted as `pbkdf2_sha256$100000$<salt>$<hash>`.
- Constant-time verification prevents timing side-channel analysis.

### B. Signed Tamper-Proof Session Tokens
- Tokens are prefixed with `aasi_tok_` followed by base64-encoded URL-safe JSON claims and HMAC-SHA256 digital signatures signed by the platform secret key.
- Token claims include: `user_id`, `username`, `role`, `exp` (24-hour expiration), `iat`, and `nonce`.
- Any signature tampering immediately invalidates the session without database lookup.

### C. Multitenancy Governance Engine
- **Active Job Limits**: Maximum 2 concurrent CFD jobs per user prevents resource monopolization.
- **Archive Size Caps**: Uploads bounded at 100 MB default (configurable up to 500 MB).
- **Execution Timeouts**: Remote executions timeout at 1800s (30 minutes).
- **Sliding Window Rate Limiter**: 60 requests/minute per IP/tenant using sliding timestamp windows.
- **Tenant Isolation**: Non-admin users cannot access, observe, or cancel jobs initiated by other tenants.

---

## 4. Content-Addressed Object Store (CAS)

The `LargeObjectStore` decouples large numerical datasets from JSON metadata:
- Large mesh files, velocity/pressure field dictionaries, OpenFOAM logs, and `.tar.gz` bundles are hashed with SHA-256.
- Objects are placed on disk/object-storage using two-character directory sharding:
  `data/storage/large_objects/objects/sha256/fa/fa08b9c...`
- Metadata registry tracks:
  - `object_id`
  - `sha256`
  - `size_bytes`
  - `epistemic_class` (from the 8 standardized tiers)
  - `category` (`CASE_ARCHIVE`, `MESH`, `PRESSURE_FIELD`, `VELOCITY_FIELD`, `TURBULENCE_FIELD`, `FORCE_HISTORY`, `RESIDUAL_HISTORY`, `VTK`)
  - `created_at` timestamp.
