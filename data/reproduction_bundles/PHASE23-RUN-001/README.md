# AASI Reproduction Bundle: PHASE23-RUN-001
**Campaign ID:** `P23-E001_to_E005`
**Backend:** Google Colab / Remote Compute Fabric
**Solver:** OpenFOAM simpleFoam
**Governing Doctrine:** Absolute Anti-Fabrication Rule

## Reproduction Instructions
Run the standalone verifier:
```bash
python -c "from pathlib import Path; from backend.research.reproduction_verifier_phase23 import Phase23ReproductionVerifier; print(Phase23ReproductionVerifier.verify_bundle(Path('.')))"
```
All assets must match SHA-256 checksums in `checksums.sha256`.
