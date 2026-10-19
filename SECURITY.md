# AASI Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in AASI, please report it responsibly:

1. **Email:** Send details to `security@projectpolaris.in`
2. **Do NOT** open a public GitHub issue for security vulnerabilities
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Any suggested remediation

## Response Timeline

- **Acknowledgment:** Within 48 hours
- **Assessment:** Within 5 business days
- **Remediation:** Critical issues within 14 days; others within 30 days

## Security Architecture

### Authentication & Authorization
- JWT-based session tokens with configurable expiry (default: 24 hours)
- Role-Based Access Control (RBAC): `RESEARCHER`, `AERODYNAMICIST`, `ADMIN`, `ENTERPRISE_ADMIN`
- Secret key must be cryptographically random in production (minimum 32 bytes)

### Data Integrity
- SHA-256 checksums on all geometry inputs, solver outputs, and verification metrics
- Append-only Merkle DAG provenance chain ensuring tamper-evident audit trails
- Atomic file operations with collision-resistant temporary files

### Network Security
- CORS restricted to explicitly configured trusted origins in production
- No wildcard (`*`) CORS allowed in production deployment
- Rate limiting enforced per-user and per-endpoint

### Supply Chain
- Docker images built from official Python 3.12 and Node.js 20 Alpine base images
- Non-root container execution in production
- No development dependencies in production containers

### Anti-Fabrication Doctrine
- Every computation result carries an epistemic classification
- Surrogate predictions are never labeled as "experimental" or "validated"
- Panel solver results are labeled `VERIFIED_PANEL_VISCOUS`, never "CFD"
- Stage-10 gate enforcement prevents synthetic data substitution

## Known Limitations

1. The default secret key (`aasi-dev-key-CHANGE-IN-PRODUCTION`) must be replaced before deployment
2. File upload endpoints should have additional content-type validation for hardened deployments
3. Subprocess execution for external solvers (OpenFOAM, SU2) requires careful sandboxing in multi-tenant environments
