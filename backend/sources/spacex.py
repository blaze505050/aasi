"""
AASI SpaceX & Commercial Aerospace Source Adapter.

Manages public commercial aerospace records (public technical presentations,
AIAA papers, FAA regulatory filings, user guides).
STRICTLY ENFORCES: Never claims access to internal proprietary engineering databases,
confidential CAD, or internal corporate CFD.
"""

import hashlib
from typing import Dict, Any, List, Optional, Tuple

from backend.sources.base_connector import BaseSourceConnector
from backend.sources.models import (
    SourceMetadata,
    KnowledgeType,
    AccessMethod,
    SourceStatus,
    EpistemicClassification,
    CommercialPublicityStatus,
    SourceDocument,
    ProvenanceChain,
    ProvenanceVerificationLevel,
)


class SpaceXPublicSourceAdapter(BaseSourceConnector):
    """Indexes officially released public SpaceX information with strict proprietary isolation."""

    METADATA = SourceMetadata(
        source_id="SPACEX_PUBLIC",
        organization="SpaceX",
        name="SpaceX Public Engineering Material & Regulatory Releases",
        category="ROCKET_PROPULSION",
        base_url="https://www.spacex.com",
        access_method=AccessMethod.METADATA_INGESTION,
        license="Public Corporate Release / Fair Use for Educational Research",
        update_frequency="As Publicly Released",
        public_access=True,
        citation_policy="Cite public document title, release year, or FAA filing reference",
        content_types=[KnowledgeType.DOCUMENT, KnowledgeType.ROCKET, KnowledgeType.SPACECRAFT, KnowledgeType.MISSION],
        status=SourceStatus.ACTIVE,
        notes="RESTRICTED TO OFFICIALLY PUBLIC DATA. Never indexes or claims access to internal CFD or proprietary engineering."
    )

    PUBLIC_RELEASES = {
        "SPACEX-FALCON9-UG": {
            "title": "Falcon 9 Launch Vehicle Payload User's Guide (Rev 2.0)",
            "report_number": "SPACEX-FALCON9-UG",
            "year": 2021,
            "access_classification": "PUBLIC_DOCUMENT",
            "summary": "Payload fairing acoustic, vibrational, thermal, and mechanical environments, payload adapter interfaces, and standard orbit insertion capabilities."
        },
        "SPACEX-STARSHIP-FAA-PEA": {
            "title": "FAA Final Programmatic Environmental Assessment for the SpaceX Starship / Super Heavy Launch Vehicle Program at the Boca Chica Launch Site",
            "report_number": "FAA-PEA-SPACEX-STARSHIP",
            "year": 2022,
            "access_classification": "PUBLIC_REGULATORY_FILING",
            "summary": "Vehicle propellant mass capacities (LOX/CH4), liftoff thrust specifications (~7,500 tf), launch trajectory acoustic profiles, and environmental mitigation."
        },
        "SPACEX-RAPTOR-IAC-2016": {
            "title": "Making Humans a Multi-Planetary Species (IAC Guadalajara Presentation)",
            "report_number": "IAC-2016-MUSK",
            "year": 2016,
            "access_classification": "PUBLIC_CONFERENCE_PRESENTATION",
            "summary": "Public disclosure of full-flow staged combustion cycle (FFSCC) architecture, chamber pressure targets (300+ bar), and sub-cooled methalox densification."
        }
    }

    PROPRIETARY_TERMS = [
        "internal cfd", "confidential cad", "raw telemetry", "proprietary database",
        "secret drawings", "internal test stand data", "unreleased raptor 3 cad",
        "proprietary cooling channels", "turbopump metallurgy"
    ]

    def __init__(self):
        super().__init__(
            source_id="SPACEX_PUBLIC",
            name="SpaceX Public Engineering Material & Regulatory Releases",
            organization="SpaceX",
            category="ROCKET_PROPULSION",
            base_url="https://www.spacex.com",
            access_method=AccessMethod.METADATA_INGESTION,
            epistemic_classification=EpistemicClassification.PUBLIC_COMMERCIAL_RELEASE,
            license="Public Corporate Release / Fair Use for Educational Research",
            citation_policy="Cite public document title, release year, or FAA filing reference",
            content_types=[KnowledgeType.DOCUMENT, KnowledgeType.ROCKET, KnowledgeType.SPACECRAFT, KnowledgeType.MISSION],
            status=SourceStatus.ACTIVE,
            notes="RESTRICTED TO OFFICIALLY PUBLIC DATA. Never indexes or claims access to internal CFD or proprietary engineering."
        )

    def classify_query(self, query: str) -> CommercialPublicityStatus:
        """Categorizes request into PUBLICLY_VERIFIED_INFORMATION or PROPRIETARY_UNAVAILABLE."""
        q = query.lower()
        if any(term in q for term in self.PROPRIETARY_TERMS):
            return CommercialPublicityStatus.PROPRIETARY_UNAVAILABLE
        return CommercialPublicityStatus.PUBLICLY_VERIFIED_INFORMATION

    def verify_request_is_public(self, query: str) -> Tuple[bool, str]:
        """Checks if a query requests confidential / proprietary commercial data."""
        status = self.classify_query(query)
        if status == CommercialPublicityStatus.PROPRIETARY_UNAVAILABLE:
            matched = [t for t in self.PROPRIETARY_TERMS if t in query.lower()][0]
            return False, f"AASI does not possess or claim access to proprietary commercial data ('{matched}'). Only officially published documents, user guides, and regulatory filings are indexed."
        return True, "Request is within public domain scope."

    def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Searches officially public commercial aerospace documents."""
        self.total_queries += 1
        is_pub, msg = self.verify_request_is_public(query)
        if not is_pub:
            self.last_status = "PROPRIETARY_REJECTED"
            return []

        q = query.lower()
        results = []
        for rep_id, item in self.PUBLIC_RELEASES.items():
            if q in rep_id.lower() or q in item["title"].lower() or q in item["summary"].lower():
                res = dict(item)
                res["source"] = "SPACEX_PUBLIC"
                res["commercial_status"] = CommercialPublicityStatus.PUBLICLY_VERIFIED_INFORMATION.value
                res["proprietary_warning"] = "Public data only. AASI maintains zero access to proprietary internal engineering databases."
                res["checksum"] = hashlib.sha256(f"{rep_id}:{item['title']}".encode()).hexdigest()
                results.append(res)
                if len(results) >= limit:
                    break
        return results

    def fetch(self, document_id: str) -> Optional[SourceDocument]:
        """Fetches SourceDocument representation for an officially released public document."""
        item = self.PUBLIC_RELEASES.get(document_id)
        if not item:
            return None
        doc = self._dict_to_source_document(item)
        doc.commercial_status = CommercialPublicityStatus.PUBLICLY_VERIFIED_INFORMATION
        return doc
