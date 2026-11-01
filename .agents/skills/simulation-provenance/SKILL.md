---
name: simulation-provenance
description: Cryptographic provenance and reproducibility tracking for aerospace simulations: SHA-256 Merkle DAG lineage, solver environment recording, input deck hashing, and tamper-evident audit trails.
---

# Simulation Provenance & Reproducibility Skill

## 1. Merkle DAG Lineage
- **Node Hashing**: Every simulation state, mesh, boundary condition file, and solver output is hashed using SHA-256.
- **Parent Reference**: Every derived result includes the exact cryptographic hash of its input deck and solver configuration.
- **Root Manifest**: A complete investigation produces a single root Merkle hash that guarantees bitwise reproducibility of all figures, tables, and conclusions.

## 2. Environment Snapshots
Every simulation record must capture:
- Hardware profile: CPU model, core count, total RAM, GPU device ID and VRAM.
- Software stack: OS release, Python version, installed package versions (`pip freeze`), solver binary checksums.
- Execution parameters: Random seed, start timestamp, completion timestamp, wall-clock duration, peak RAM/CPU usage.
- Exit code & standard streams: Exit code (0 for nominal), captured `stdout` and `stderr` logs.

## 3. Tamper-Evident Dossiers
- Export reports as structured bundles (`.tar.gz` or `.zip`) containing the report markdown, raw CSV/JSON polars, input geometry files, and `manifest.json`.
- Provide a verification command (e.g. `python -m aasi.verify manifest.json`) allowing external auditors, certification authorities, or prime contractors to independently verify data integrity.

