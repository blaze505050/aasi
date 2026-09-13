"""
AASI Phase 21: CFD Cryptographic Provenance Engine.
Governing Rule: Absolute Anti-Fabrication Rule.
Computes deterministic SHA-256 provenance trees across case decks, geometry, mesh, solver, and outputs.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class CFDProvenanceEngine:
    """Tracks full cryptographic lineage of CFD simulations."""

    @staticmethod
    def hash_file(file_path: Path) -> str:
        """Compute SHA-256 hash of a single file."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return ""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def hash_directory(cls, dir_path: Path, pattern: str = "*") -> Dict[str, str]:
        """Compute per-file SHA-256 hashes inside a directory."""
        path = Path(dir_path)
        hashes: Dict[str, str] = {}
        if not path.exists() or not path.is_dir():
            return hashes
        for file in sorted(path.glob(pattern)):
            if file.is_file():
                rel_path = file.relative_to(path).as_posix()
                hashes[rel_path] = cls.hash_file(file)
        return hashes

    @classmethod
    def compute_case_provenance(
        cls,
        case_dir: Path,
        solver_name: str,
        solver_version: str,
        environment_manifest_hash: str = "",
    ) -> Dict[str, Any]:
        """Compute complete provenance tree for an OpenFOAM case directory."""
        case_path = Path(case_dir)

        system_hashes = cls.hash_directory(case_path / "system")
        constant_hashes = cls.hash_directory(case_path / "constant")
        initial_hashes = cls.hash_directory(case_path / "0")

        # Hash geometry if present
        geom_hash = cls.hash_file(case_path / "geometry.dat")

        # Hash log outputs if present
        log_hashes = {}
        for log_file in case_path.glob("log.*"):
            if log_file.is_file():
                log_hashes[log_file.name] = cls.hash_file(log_file)

        # Hash postProcessing outputs if present
        post_hashes = cls.hash_directory(case_path / "postProcessing", pattern="**/*.dat")

        # Compute combined Merkle root
        manifest = {
            "case_dir": str(case_path),
            "solver": {
                "name": solver_name,
                "version": solver_version,
                "environment_manifest_hash": environment_manifest_hash,
            },
            "geometry_hash": geom_hash,
            "system_hashes": system_hashes,
            "constant_hashes": constant_hashes,
            "initial_conditions_hashes": initial_hashes,
            "log_hashes": log_hashes,
            "post_processing_hashes": post_hashes,
        }

        canonical_json = json.dumps(manifest, sort_keys=True)
        merkle_root = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return {
            "merkle_root": merkle_root,
            "manifest": manifest,
        }
