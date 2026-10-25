---
name: license-compliance-review
version: 2.0.0
description: Audits third-party dependencies, skills, and model integrations against commercial distribution and intellectual property policies.
triggers:
  - "review dependency licenses"
  - "audit open source licenses"
  - "check commercial compliance"
preconditions:
  - Dependency manifests (pyproject.toml, package.json, requirements.txt) or source headers available
permitted_tools:
  - inspect_ast
required_inputs:
  package_manifest: string
  target_tier: string
output_schema:
  compliant: boolean
  spdx_inventory: list
  viral_copyleft_detected: boolean
  attribution_obligations: list
  recommendations: list
resource_estimate:
  ram_mb: 32
  wall_time_seconds: 4
---

# License Compliance Review Skill

## Purpose
Ensures AASI 2.0 and its modular tool ecosystem maintain spotless intellectual property boundaries. Evaluates software licenses (Apache-2.0, MIT, BSD-3-Clause, LGPL, GPL-3.0, AGPL-3.0, and proprietary terms) to safeguard AASI's commercial distribution rights and prevent license contamination.

## Execution Procedure
1. Scan project manifests (`requirements.txt`, `package.json`, `pyproject.toml`) and transitive dependency trees.
2. Cross-reference licenses against SPDX standard identifiers.
3. Classify components into:
   - Permissive (MIT, Apache-2.0, BSD): Approved for direct inclusion with attribution notices.
   - Weak Copyleft (LGPL, MPL): Permitted via dynamic linking or out-of-process CLI/adapter isolation.
   - Strong Copyleft (GPL-3.0, AGPL-3.0): Strictly quarantined; accessed only through decoupled subprocess/adapter protocols (e.g. OpenFOAM, SU2) without static linking.
   - Proprietary / Unclear: Flagged for legal review.
4. Verify presence of required copyright notices and `THIRD_PARTY_NOTICES.md`.
5. Enforce fail-closed blocking on unauthorized AGPL packages in SaaS deployments.

## Compliance Guarantees
- Never assume an unstated license is public domain.
- ASD-STE100 terminology is strictly separated from copyrighted specification text; no false certification claims are allowed.
