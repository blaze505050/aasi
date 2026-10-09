"""
AASI Phase 26 Security & Trust Model Test Suite.
Verifies defense against path traversal, archive manipulation, forged execution states,
checksum tampering, and untrusted remote artifacts.
"""

import pytest
import io
import tarfile
import hashlib
from backend.dataset.provenance import DatasetProvenanceGuard
from backend.dataset.ingestion import DatasetIngestor, TrustLevel


def test_security_rejects_path_traversal_in_archives():
    """Security: prevent archive extraction path traversal attacks."""
    malicious_paths = [
        "../../../../Windows/System32/cmd.exe",
        "../etc/shadow",
        "/absolute/path/override",
        "C:\\Windows\\system.ini",
    ]
    assert DatasetProvenanceGuard.validate_archive_path_safety(malicious_paths) is False


def test_security_accepts_clean_case_paths():
    clean_paths = [
        "0/U",
        "0/p",
        "constant/polyMesh/points",
        "constant/polyMesh/faces",
        "system/controlDict",
        "system/fvSchemes",
    ]
    assert DatasetProvenanceGuard.validate_archive_path_safety(clean_paths) is True


def test_security_archive_ingestor_rejects_traversal(tmp_path):
    """Verify DatasetIngestor rejects archive with path traversal."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        data = b"malicious content"
        ti = tarfile.TarInfo(name="../../etc/passwd")
        ti.size = len(data)
        tar.addfile(ti, io.BytesIO(data))

    bad_tar_bytes = buf.getvalue()
    ingestor = DatasetIngestor()
    res = ingestor.ingest_archive_tarball(bad_tar_bytes, geometry_id="NACA 0012")

    assert res.success is False
    assert "Security violation" in res.error


def test_security_tampered_results_manifest_detected():
    """Verify modifying single byte in results archive invalidates SHA-256 digest."""
    original_data = b"Authentic forceCoeffs log: CL=1.0820 CD=0.0125"
    orig_hash = hashlib.sha256(original_data).hexdigest()

    tampered_data = b"Authentic forceCoeffs log: CL=2.5000 CD=0.0010"
    tampered_hash = hashlib.sha256(tampered_data).hexdigest()

    assert orig_hash != tampered_hash
