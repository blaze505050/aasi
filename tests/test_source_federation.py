"""
Tests for AASI Scientific Source Federation, Guardrails, and Current Events.
"""

import pytest
from backend.sources.catalog import ScientificSourceCatalog
from backend.sources.guardrails import CitationGuardrail
from backend.sources.models import KnowledgeType, AccessMethod, SourceStatus
from backend.sources.current_info import CurrentInformationService


def test_source_catalog_disciplines_and_registrations():
    """Verifies that ScientificSourceCatalog registers sources across 15 disciplines."""
    catalog = ScientificSourceCatalog()
    assert len(catalog.CATEGORIES) == 15
    sources = catalog.list_sources()
    assert len(sources) >= 14

    # Verify primary sources exist
    nasa = catalog.get_source("NASA_NTRS")
    assert nasa is not None
    assert nasa.organization == "NASA"
    assert nasa.access_method == AccessMethod.DIRECT_API

    isro = catalog.get_source("ISRO_PUBLIC")
    assert isro is not None
    assert isro.organization == "ISRO"

    esa = catalog.get_source("ESA_PUBLIC")
    assert esa is not None
    assert esa.organization == "ESA"

    spacex = catalog.get_source("SPACEX_PUBLIC")
    assert spacex is not None
    assert "PROPRIETARY" in spacex.notes or "RESTRICTED" in spacex.notes


def test_guardrails_license_validation():
    """Tests that CitationGuardrail accepts open licenses and rejects proprietary."""
    open_lic = CitationGuardrail.validate_license("Public Domain (NASA Technical Report)")
    assert open_lic["valid"] is True
    assert open_lic["open_access"] is True

    cc_lic = CitationGuardrail.validate_license("CC-BY-4.0")
    assert cc_lic["valid"] is True

    prop_lic = CitationGuardrail.validate_license("Proprietary and Confidential")
    assert prop_lic["valid"] is False
    assert "Restricted" in prop_lic["error"]

    itar_lic = CitationGuardrail.validate_license("ITAR-Controlled Data")
    assert itar_lic["valid"] is False


def test_guardrails_report_identifier_validation():
    """Tests that authentic scientific report identifiers pass and fake ones fail."""
    assert CitationGuardrail.validate_report_identifier("NASA-TN-D-628") is True
    assert CitationGuardrail.validate_report_identifier("NACA-TR-824") is True
    assert CitationGuardrail.validate_report_identifier("ESA-SP-1200") is True
    assert CitationGuardrail.validate_report_identifier("arXiv:2203.01234") is True
    assert CitationGuardrail.validate_report_identifier("FAKE-PAPER-XYZ-999") is False
    assert CitationGuardrail.validate_report_identifier("invented_citation_123") is False


def test_nasa_source_adapter_excludes_restricted():
    """Verifies NASA adapter returns public documents and blocks restricted."""
    catalog = ScientificSourceCatalog()
    results = catalog.nasa_adapter.search("NACA 0012")
    assert len(results) > 0
    assert any("NASA-TN-D-628" in r["report_number"] for r in results)

    # Search for restricted document
    restricted_results = catalog.nasa_adapter.search("Restricted")
    assert len(restricted_results) == 0  # Should never surface

    doc_meta = catalog.nasa_adapter.get_document_metadata("NASA-RESTRICTED-001")
    assert doc_meta is not None
    assert doc_meta["access"] == "RESTRICTED"
    assert "cannot access" in doc_meta["error"]


def test_isro_source_adapter_honesty():
    """Verifies ISRO adapter provides accurate metadata without faking non-existent REST APIs."""
    catalog = ScientificSourceCatalog()
    chandrayaan = catalog.isro_adapter.get_record("ISRO-CHANDRAYAAN-3")
    assert chandrayaan is not None
    assert chandrayaan["portal"] == "ISSDC (Indian Space Science Data Centre)"
    assert chandrayaan["machine_api_available"] is False
    assert "ChaSTE" in chandrayaan["payloads"]

    aditya = catalog.isro_adapter.get_record("ISRO-ADITYA-L1")
    assert aditya is not None
    assert "VELC" in aditya["payloads"]


def test_spacex_adapter_proprietary_rejection():
    """Verifies that SpaceX adapter strictly rejects requests for internal proprietary engineering data."""
    catalog = ScientificSourceCatalog()
    is_pub, msg = catalog.spacex_adapter.verify_request_is_public("What is the payload fairing dimension from the user guide?")
    assert is_pub is True

    is_pub2, msg2 = catalog.spacex_adapter.verify_request_is_public("Can you show me the SpaceX internal CFD database for Starship?")
    assert is_pub2 is False
    assert "proprietary commercial data" in msg2


def test_current_information_service():
    """Verifies that current events are labeled CURRENT_INFORMATION with retrieval timestamps."""
    service = CurrentInformationService()
    events = service.get_latest_events()
    assert len(events) >= 4

    # Check Artemis item
    artemis = [e for e in events if "Artemis" in e.title][0]
    assert artemis.label == "CURRENT_INFORMATION"
    assert artemis.published_at.startswith("2024")
    assert len(artemis.provenance_hash) == 64

    # Format check
    formatted = service.format_current_info_response(artemis)
    assert "**[CURRENT_INFORMATION]**" in formatted
    assert "Retrieved Timestamp:" in formatted
    assert "distinct from peer-reviewed SCIENTIFIC_REFERENCE" in formatted
