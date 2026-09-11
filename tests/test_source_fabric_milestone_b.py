"""
Unit and Integration Tests for Milestone B: Provenance & Source-Fabric Hardening.

Validates:
- Cryptographic provenance chain isolation (metadata vs byte vs content hashes)
- Epistemic classifications (Preprints vs Agency Reports vs Commercial Releases)
- SpaceX commercial publicity boundary & proprietary rejection
- arXiv live/offline connector resilience & XML parsing
- Central catalog connector routing and runtime diagnostics
- API endpoints: /api/sources/diagnostics and /api/sources/arxiv/search
"""

import pytest
import hashlib
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.sources.models import (
    ProvenanceChain,
    ProvenanceVerificationLevel,
    EpistemicClassification,
    CommercialPublicityStatus,
    SourceDocument,
    DocumentFragment,
    AccessMethod,
)
from backend.sources.base_connector import BaseSourceConnector
from backend.sources.arxiv_connector import ArxivSourceConnector
from backend.sources.nasa import NASASourceAdapter
from backend.sources.spacex import SpaceXPublicSourceAdapter
from backend.sources.catalog import ScientificSourceCatalog


client = TestClient(app)


def test_provenance_chain_separation():
    """Validates that metadata hash, raw byte hash, and content hash are strictly distinct."""
    meta_hash = hashlib.sha256(b"DOC-001:Title:2024").hexdigest()
    raw_hash = hashlib.sha256(b"%PDF-1.4 simulated pdf bytes").hexdigest()
    content_hash = hashlib.sha256(b"Extracted normalized text").hexdigest()

    chain = ProvenanceChain(
        metadata_descriptor_hash=meta_hash,
        raw_artifact_hash=raw_hash,
        extracted_content_hash=content_hash,
        verification_level=ProvenanceVerificationLevel.RAW_BYTE_VERIFIED,
    )

    assert chain.metadata_descriptor_hash != chain.raw_artifact_hash
    assert chain.metadata_descriptor_hash != chain.extracted_content_hash
    assert chain.raw_artifact_hash != chain.extracted_content_hash
    assert chain.verification_level == ProvenanceVerificationLevel.RAW_BYTE_VERIFIED


def test_base_connector_verification_levels():
    """Validates verify_provenance() behavior on documents and fragments."""
    nasa = NASASourceAdapter()

    # 1. Metadata only
    meta_hash = nasa.build_metadata_hash("NASA-TN-D-628", "NACA 0012", "1961")
    doc_meta = SourceDocument(
        document_id="NASA-TN-D-628",
        source_id="NASA_NTRS",
        title="NACA 0012",
        authors=["Critzos"],
        organization="NASA",
        publication_date="1961",
        url="https://ntrs.nasa.gov",
        license="Public Domain",
        access_method=AccessMethod.STATIC_SEED,
        epistemic_classification=EpistemicClassification.AGENCY_TECHNICAL_REPORT,
        provenance_chain=ProvenanceChain(
            metadata_descriptor_hash=meta_hash,
            raw_artifact_hash=None,
            extracted_content_hash=None,
            verification_level=ProvenanceVerificationLevel.METADATA_VERIFIED,
        ),
    )
    assert nasa.verify_provenance(doc_meta) == ProvenanceVerificationLevel.METADATA_VERIFIED

    # 2. Byte verified
    doc_raw = doc_meta.model_copy(deep=True)
    doc_raw.provenance_chain.raw_artifact_hash = hashlib.sha256(b"pdf bytes").hexdigest()
    assert nasa.verify_provenance(doc_raw) == ProvenanceVerificationLevel.RAW_BYTE_VERIFIED

    # 3. Fragment content verification
    body = "Lift coefficient reaches maximum at 16 degrees."
    correct_hash = hashlib.sha256(body.strip().encode("utf-8")).hexdigest()
    frag = DocumentFragment(
        fragment_id="FRAG-1",
        document_id="NASA-TN-D-628",
        content=body,
        content_hash=correct_hash,
    )
    assert nasa.verify_provenance(frag) == ProvenanceVerificationLevel.CONTENT_VERIFIED

    bad_frag = DocumentFragment(
        fragment_id="FRAG-2",
        document_id="NASA-TN-D-628",
        content=body,
        content_hash="tampered_hash_value",
    )
    assert nasa.verify_provenance(bad_frag) == ProvenanceVerificationLevel.UNVERIFIED


def test_arxiv_connector_offline_resilience():
    """Validates that ArxivSourceConnector fails closed without crashing if offline."""
    connector = ArxivSourceConnector()
    
    with patch("urllib.request.urlopen", side_effect=OSError("Network unreachable")):
        results = connector.search("boundary layer laminar flow")
        assert results == []
        assert "OFFLINE_FALLBACK" in connector.last_status

        fetched = connector.fetch("2301.99999")
        assert fetched is None


def test_arxiv_xml_parsing():
    """Validates XML parsing from arXiv Atom feed with preprint classification."""
    sample_atom_feed = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2401.00001v1</id>
        <title> Deep Learning Surrogates for Transonic Aerodynamics </title>
        <summary> We propose a geometric deep learning architecture for airfoil polars. </summary>
        <published>2024-01-01T12:00:00Z</published>
        <author><name>John von Karman</name></author>
        <author><name>Ludwig Prandtl</name></author>
      </entry>
    </feed>
    """
    connector = ArxivSourceConnector()
    docs = connector._parse_atom_feed(sample_atom_feed)

    assert len(docs) == 1
    doc = docs[0]
    assert doc.document_id == "ARXIV:2401.00001v1"
    assert doc.title == "Deep Learning Surrogates for Transonic Aerodynamics"
    assert "Karman" in doc.authors[0]
    assert doc.epistemic_classification == EpistemicClassification.UNVERIFIED_PREPRINT
    assert doc.provenance_chain.metadata_descriptor_hash is not None
    assert doc.provenance_chain.verification_level == ProvenanceVerificationLevel.METADATA_VERIFIED


def test_spacex_commercial_publicity_boundary():
    """Validates strict classification of public user guides vs proprietary engine CAD/CFD."""
    adapter = SpaceXPublicSourceAdapter()

    # Public request
    q_pub = "Falcon 9 payload fairing acoustic envelope"
    assert adapter.classify_query(q_pub) == CommercialPublicityStatus.PUBLICLY_VERIFIED_INFORMATION
    is_pub, msg = adapter.verify_request_is_public(q_pub)
    assert is_pub is True

    # Proprietary request
    q_prop = "What is the secret internal CFD database and turbopump metallurgy for Raptor 3?"
    assert adapter.classify_query(q_prop) == CommercialPublicityStatus.PROPRIETARY_UNAVAILABLE
    is_pub2, msg2 = adapter.verify_request_is_public(q_prop)
    assert is_pub2 is False
    assert "proprietary" in msg2.lower()

    # Search rejection
    results = adapter.search(q_prop)
    assert results == []
    assert adapter.last_status == "PROPRIETARY_REJECTED"


def test_catalog_connector_routing_and_diagnostics():
    """Validates central catalog registration, connector routing, and diagnostic metrics."""
    catalog = ScientificSourceCatalog()

    arxiv = catalog.get_connector("ARXIV_AERO")
    assert arxiv is not None
    assert isinstance(arxiv, ArxivSourceConnector)

    nasa = catalog.get_connector("NASA_NTRS")
    assert nasa is not None
    assert isinstance(nasa, NASASourceAdapter)

    diag = catalog.get_diagnostics()
    assert "total_registered_sources" in diag
    assert diag["active_operational_connectors"] >= 3
    assert "ARXIV_AERO" in diag["connectors"]
    assert "NASA_NTRS" in diag["connectors"]


def test_api_source_diagnostics():
    """Tests GET /api/sources/diagnostics endpoint."""
    res = client.get("/api/sources/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert "total_registered_sources" in data
    assert "connectors" in data
    assert "NASA_NTRS" in data["connectors"]


def test_api_arxiv_search():
    """Tests GET /api/sources/arxiv/search endpoint."""
    # Test with offline mock to avoid internet flake during test suite
    with patch.object(ArxivSourceConnector, "search_documents", return_value=[
        SourceDocument(
            document_id="ARXIV:2401.00001",
            source_id="ARXIV_AERO",
            title="Boundary Layer Transition Analysis",
            authors=["A. Scientist"],
            organization="arXiv",
            publication_date="2024-01-01",
            url="https://arxiv.org/abs/2401.00001",
            license="arXiv Non-exclusive License",
            access_method=AccessMethod.DIRECT_API,
            epistemic_classification=EpistemicClassification.UNVERIFIED_PREPRINT,
            provenance_chain=ProvenanceChain(
                metadata_descriptor_hash="mockhash",
                verification_level=ProvenanceVerificationLevel.METADATA_VERIFIED
            )
        )
    ]):
        res = client.get("/api/sources/arxiv/search?q=boundary+layer")
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == "boundary layer"
        assert len(data["results"]) == 1
        assert "UNVERIFIED_PREPRINT" in data["epistemic_notice"]
        assert data["results"][0]["document_id"] == "ARXIV:2401.00001"
