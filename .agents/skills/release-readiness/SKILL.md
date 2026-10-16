---
name: release-readiness
description: Release readiness checklist for AASI releases. Use when preparing a release candidate, evaluating deployment readiness, or reviewing commercial launch criteria.
---

# Release Readiness Skill

## Purpose
Defines the acceptance criteria that must be met before any AASI release.

## Pre-Release Checklist

### 1. Scientific Correctness
- [ ] All 946+ tests pass (`pytest tests/ -v`)
- [ ] No new warnings in test output
- [ ] Panel solver validated against NACA 0012 reference data
- [ ] Surrogate model has verified checkpoint (if applicable)
- [ ] All predictions carry proper epistemic classification
- [ ] Uncertainty estimates are honest (calibrated vs uncalibrated documented)

### 2. Code Quality
- [ ] TypeScript type check passes (`npx tsc --noEmit`)
- [ ] Python linting clean (ruff/flake8)
- [ ] No hardcoded credentials in source
- [ ] No TODO items in critical paths
- [ ] `main.py` routes consolidated into `api/routes_*.py`

### 3. Security
- [ ] Authentication enforced on sensitive routes
- [ ] Secret key not using default value
- [ ] CORS properly restricted for production
- [ ] File upload limits configured
- [ ] Subprocess execution reviewed
- [ ] No sensitive data in logs

### 4. Usability
- [ ] End-to-end airfoil workflow functions from UI
- [ ] Clear error messages for invalid inputs
- [ ] Loading states for async operations
- [ ] Results are exportable (JSON, CSV, DATCOM)
- [ ] Onboarding guide works

### 5. Documentation
- [ ] README reflects actual capabilities (not aspirational)
- [ ] API endpoints documented (Swagger/OpenAPI)
- [ ] Installation instructions verified on clean machine
- [ ] Known limitations documented
- [ ] Engineering disclaimer present

### 6. Deployment
- [ ] Docker build succeeds
- [ ] Health check endpoint working
- [ ] Environment variables documented
- [ ] Backup/restore procedure exists
- [ ] Monitoring/alerting configured

### 7. No Fabrication
- [ ] No fake functionality (buttons that don't work)
- [ ] No fabricated test results or benchmark numbers
- [ ] No claims of capabilities that don't exist
- [ ] All displayed data comes from actual computation
