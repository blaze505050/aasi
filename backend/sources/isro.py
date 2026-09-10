"""
AASI ISRO Source Adapter & Public Registry.

Catalogs legitimate public ISRO material (ISRO Annual Reports, ISSDC science data,
MOSDAC meteorological datasets, and public mission documents).
Accurately declares machine accessibility; provides metadata and manual-import
support without fabricating non-existent REST APIs.
"""

import hashlib
from typing import Dict, Any, List, Optional
from backend.sources.models import SourceMetadata, KnowledgeType, AccessMethod, SourceStatus


class ISROSourceAdapter:
    """Registry and metadata catalog for public ISRO materials."""

    METADATA = SourceMetadata(
        source_id="ISRO_PUBLIC",
        organization="ISRO",
        name="Indian Space Research Organisation Public Archives",
        category="AEROSPACE",
        base_url="https://www.isro.gov.in",
        access_method=AccessMethod.METADATA_INGESTION,
        license="Open Government Data (OGD) India / Public Educational",
        update_frequency="Monthly / Mission Milestones",
        public_access=True,
        citation_policy="Cite ISRO, Government of India, mission/report identifier",
        content_types=[KnowledgeType.TECHNICAL_REPORT, KnowledgeType.MISSION, KnowledgeType.DATASET, KnowledgeType.DOCUMENT],
        status=SourceStatus.ACTIVE,
        notes="No unified public REST API. Uses metadata ingestion, portal registries (MOSDAC, ISSDC), and manual import."
    )

    PUBLIC_MISSION_RECORDS = {
        "ISRO-CHANDRAYAAN-3": {
            "title": "Chandrayaan-3 Mission Scientific Overview and Landing Payloads",
            "report_number": "ISRO-CHANDRAYAAN-3",
            "center": "ISRO Telemetry, Tracking and Command Network (ISTRAC)",
            "portal": "ISSDC (Indian Space Science Data Centre)",
            "portal_url": "https://www.issdc.gov.in",
            "machine_api_available": False,
            "access_method": "METADATA_REGISTRY_AND_MANUAL_DOWNLOAD",
            "year": 2023,
            "payloads": ["ChaSTE", "ILSA", "RAMBHA-LP", "APXS", "LIBS"],
            "summary": "In-situ thermophysical measurements of lunar regolith at south polar latitude (~69°S) and elemental composition."
        },
        "ISRO-ADITYA-L1": {
            "title": "Aditya-L1 Solar Observatory Instrumentation and Mission Orbit",
            "report_number": "ISRO-ADITYA-L1",
            "center": "U R Rao Satellite Centre (URSC)",
            "portal": "ISSDC",
            "portal_url": "https://www.issdc.gov.in",
            "machine_api_available": False,
            "access_method": "METADATA_REGISTRY_AND_MANUAL_DOWNLOAD",
            "year": 2023,
            "payloads": ["VELC", "SUIT", "ASPEX", "PAPA", "SoLEXS", "HEL1OS", "Magnetometer"],
            "summary": "Halo orbit around Sun-Earth Lagrangian point L1 (~1.5 million km from Earth) for continuous solar coronal imaging and particle detection."
        },
        "ISRO-MOSDAC-OCEANSAT": {
            "title": "MOSDAC Ocean Colour Monitor (OCM-3) Surface Reflectance and Aerosol Data",
            "report_number": "ISRO-MOSDAC-OCEANSAT",
            "center": "Space Applications Centre (SAC), Ahmedabad",
            "portal": "MOSDAC (Meteorological and Oceanographic Satellite Data Archival Centre)",
            "portal_url": "https://www.mosdac.gov.in",
            "machine_api_available": True,
            "access_method": "REGISTERED_PORTAL_API",
            "year": 2023,
            "summary": "Atmospheric, oceanographic, and meteorological satellite observations from EOS-06."
        },
        "ISRO-ANNUAL-REPORT-2023": {
            "title": "ISRO Annual Report 2023-2024: Launch Vehicle Developments, Propulsion Systems, and Future Missions",
            "report_number": "ISRO-AR-2023-24",
            "center": "ISRO Headquarters, Department of Space",
            "portal": "ISRO Official Portal Publications",
            "portal_url": "https://www.isro.gov.in/Annual_Report.html",
            "machine_api_available": False,
            "access_method": "DOCUMENT_METADATA",
            "year": 2024,
            "summary": "Official programmatic overview of LVM3, PSLV, SSLV, cryogenic stage (CE-20) qualifications, and Gaganyaan human spaceflight test vehicles."
        }
    }

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Searches cataloged ISRO public mission and dataset records."""
        q = query.lower()
        results = []
        for rep_id, item in self.PUBLIC_MISSION_RECORDS.items():
            if q in rep_id.lower() or q in item["title"].lower() or q in item["summary"].lower() or q in item.get("center", "").lower():
                res = dict(item)
                res["source"] = "ISRO_PUBLIC"
                res["checksum"] = hashlib.sha256(f"{rep_id}:{item['title']}".encode()).hexdigest()
                results.append(res)
        return results

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves verified metadata and access instructions for an ISRO record."""
        rec = self.PUBLIC_MISSION_RECORDS.get(record_id)
        if not rec:
            return None
        res = dict(rec)
        res["source"] = "ISRO_PUBLIC"
        res["checksum"] = hashlib.sha256(f"{record_id}:{rec['title']}".encode()).hexdigest()
        return res
