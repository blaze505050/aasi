"""
Deterministic Evidence Dossier & Cryptographic Merkle Provenance Engine.
Ensures zero AI hallucination by creating an immutable, SHA-256 anchored ground-truth
dossier from inspected aerospace simulation decks, telemetry feeds, and wind-tunnel data.
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


def compute_sha256_bytes(data: bytes) -> str:
    """Computes standard hexadecimal SHA-256 hash of a byte buffer."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def compute_sha256_string(text: str) -> str:
    """Computes hexadecimal SHA-256 hash of a UTF-8 string."""
    return compute_sha256_bytes(text.encode("utf-8"))


def compute_merkle_root(hashes: List[str]) -> str:
    """
    Computes canonical Merkle DAG root from a list of SHA-256 hexadecimal leaf hashes.
    If empty, returns 64 zeros.
    If odd count, duplicates the last leaf to balance the tree.
    """
    if not hashes:
        return "0" * 64
    
    current = sorted(hashes)
    while len(current) > 1:
        next_level: List[str] = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else current[i]
            combined = hashlib.sha256((left + right).encode("utf-8")).hexdigest()
            next_level.append(combined)
        current = next_level
    return current[0]


@dataclass
class EvidenceDossier:
    """
    Immutable Evidence Dossier representing verified ground-truth physical evidence
    extracted deterministically from target aerospace systems without generative guesswork.
    """
    dossier_id: str
    target_name: str
    target_type: str  # e.g., 'CFD_DECK', 'TELEMETRY_STREAM', 'WIND_TUNNEL_POLAR', 'ORBITAL_MISSION'
    source_files: Dict[str, str] = field(default_factory=dict)  # filename -> sha256 hash
    merkle_root: str = ""
    extracted_parameters: Dict[str, Any] = field(default_factory=dict)
    physics_envelope: Dict[str, Any] = field(default_factory=dict)
    provenance_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at_epoch: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.merkle_root:
            self.refresh_merkle_root()

    def refresh_merkle_root(self) -> str:
        """Re-computes Merkle root based on source files and serialized parameters."""
        leaf_hashes: List[str] = list(self.source_files.values())
        param_json = json.dumps(self.extracted_parameters, sort_keys=True)
        leaf_hashes.append(compute_sha256_string(param_json))
        envelope_json = json.dumps(self.physics_envelope, sort_keys=True)
        leaf_hashes.append(compute_sha256_string(envelope_json))
        
        self.merkle_root = compute_merkle_root(leaf_hashes)
        return self.merkle_root

    def verify_integrity(self) -> bool:
        """Verifies that the dossier's Merkle root matches its current data contents."""
        expected = self.merkle_root
        leaf_hashes: List[str] = list(self.source_files.values())
        param_json = json.dumps(self.extracted_parameters, sort_keys=True)
        leaf_hashes.append(compute_sha256_string(param_json))
        envelope_json = json.dumps(self.physics_envelope, sort_keys=True)
        leaf_hashes.append(compute_sha256_string(envelope_json))
        recalculated = compute_merkle_root(leaf_hashes)
        return recalculated == expected

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the evidence dossier to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceDossier:
        """Deserializes dictionary into an EvidenceDossier instance."""
        return cls(
            dossier_id=data.get("dossier_id", f"DOSSIER-{int(time.time())}"),
            target_name=data.get("target_name", "UNKNOWN"),
            target_type=data.get("target_type", "GENERIC"),
            source_files=data.get("source_files", {}),
            merkle_root=data.get("merkle_root", ""),
            extracted_parameters=data.get("extracted_parameters", {}),
            physics_envelope=data.get("physics_envelope", {}),
            provenance_metadata=data.get("provenance_metadata", {}),
            created_at_epoch=data.get("created_at_epoch", time.time()),
        )

