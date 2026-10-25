---
name: scientific-report-generation
version: 2.0.0
description: Synthesizes aerospace engineering verification dossiers and audit reports adhering to NASA-STD-7009B and ASME V&V 20 standards.
triggers:
  - "generate verification report"
  - "compile engineering dossier"
  - "export nasa 7009b dossier"
preconditions:
  - Validated simulation or calculation results with cryptographically signed provenance hashes
permitted_tools:
  - benchmark_verify
  - uncertainty_quantify
  - export_datcom
  - export_shabp
required_inputs:
  case_id: string
  solver_metadata: object
  aerodynamic_polar: object
  provenance_hashes: list
output_schema:
  report_markdown: string
  dossier_sha256: string
  standards_compliance: object
  credibility_assessment_score: float
resource_estimate:
  ram_mb: 48
  wall_time_seconds: 5
---

# Scientific Report Generation Skill

## Purpose
Generates formal, un-hallucinated verification and validation reports. Documents model pedigree, input parameters, mesh convergence indices (GCI), residuals, experimental comparison, and Merkle tree provenance.

## Execution Procedure
1. Ingest case metadata, raw convergence histories, and epistemic classifications.
2. Verify SHA-256 integrity of all input geometries, meshes, and configuration dictionaries.
3. Construct the NASA-STD-7009B Credibility Assessment Matrix across 8 dimensions:
   - Verification
   - Validation
   - Input Pedigree
   - Results Uncertainty
   - Results Robustness
   - Use History
   - M&S Management
   - People Qualifications
4. Format aerodynamic coefficient polars ($C_L, C_D, C_m$) in standardized tabular and graphical representations.
5. Record explicit limitations, bounds of applicability, and un-modeled physics.
6. Compute SHA-256 hash of the rendered dossier and append to the immutable lineage ledger.

## Anti-Fabrication Guarantees
- Unverified results are prominently marked with `UNVERIFIED` banners.
- Failed solver cases retain their `FAILED` exit status and root-cause diagnostics; they are never omitted or masked.
- All numbers cited in the text must trace directly to deterministic solver outputs.
