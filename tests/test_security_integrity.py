"""
Tests for AASI Security & Production Integrity Hardening:
Path Traversal Defenses, Regex Validation, and Artifact Ingestion Size Limits.
"""

import pytest
from backend.compute.models import ComputeRequest, UploadedArtifactPayload
from backend.compute.user_provided import UserProvidedCaseGenerator
from backend.compute.artifacts import ArtifactIngestionService


def test_user_provided_case_rejects_path_traversal():
    gen = UserProvidedCaseGenerator(base_output_dir="data/test_cases")

    # Insecure case_id with directory traversal
    req_bad_case = ComputeRequest(
        case_id="../../etc_shadow_case",
        geometry="NACA 0012",
        mach=0.15,
        reynolds=3000000.0,
        aoa_deg=5.0
    )
    with pytest.raises(ValueError, match="Insecure or invalid case_id"):
        gen.generate_case(req_bad_case)

    # Insecure geometry with directory traversal
    req_bad_geom = ComputeRequest(
        case_id="case_valid_123",
        geometry="../../secret_airfoil",
        mach=0.15,
        reynolds=3000000.0,
        aoa_deg=5.0
    )
    with pytest.raises(ValueError, match="Insecure or invalid geometry identifier"):
        gen.generate_case(req_bad_geom)


def test_artifact_ingestion_payload_size_limit():
    service = ArtifactIngestionService()

    # Oversized payload exceeding 10 MB limit
    oversized_content = "x" * (11 * 1024 * 1024)  # 11 MB
    payload = UploadedArtifactPayload(
        case_id="case_valid_456",
        solver="openfoam",
        file_name="forceCoeffs.dat",
        file_content=oversized_content
    )
    with pytest.raises(ValueError, match="exceeds the maximum limit of 10485760 bytes"):
        service.ingest_artifact(payload)


def test_artifact_ingestion_rejects_insecure_filename():
    service = ArtifactIngestionService()
    payload = UploadedArtifactPayload(
        case_id="case_valid_456",
        solver="openfoam",
        file_name="../../malicious_path/forceCoeffs.dat",
        file_content="# OpenFOAM dummy coeffs\n0  1  0.02  0.5  0\n"
    )
    with pytest.raises(ValueError, match="Insecure file name"):
        service.ingest_artifact(payload)
