"""
AASI ESA Source Adapter & Public Registry.

Catalogs legitimate public ESA materials (ESA Science Data Centre / ESAC,
Earth Online datasets, scientific publications, and technical reports).
Operates strictly via public access, metadata ingestion, and authenticated portals;
never attempts to bypass access controls.
"""

import hashlib
from typing import Dict, Any, List, Optional
from backend.sources.models import SourceMetadata, KnowledgeType, AccessMethod, SourceStatus


class ESASourceAdapter:
    """Registry and metadata connector for European Space Agency public scientific data."""

    METADATA = SourceMetadata(
        source_id="ESA_PUBLIC",
        organization="ESA",
        name="European Space Agency Public Scientific Archives",
        category="AEROSPACE",
        base_url="https://www.cosmos.esa.int",
        access_method=AccessMethod.URL_REGISTRY,
        license="ESA Open Access / Creative Commons CC-BY-SA 3.0 IGO",
        update_frequency="Monthly",
        public_access=True,
        citation_policy="Cite ESA, mission archive, and primary instrument PI publication",
        content_types=[KnowledgeType.TECHNICAL_REPORT, KnowledgeType.MISSION, KnowledgeType.DATASET, KnowledgeType.DOCUMENT],
        status=SourceStatus.ACTIVE,
        notes="Uses public Cosmos/ESAC archives and Copernicus Open Access Hub metadata."
    )

    PUBLIC_ESA_RECORDS = {
        "ESA-JUICE-001": {
            "title": "Jupiter Icy Moons Explorer (JUICE) Mission Design and Trajectory Profile",
            "report_number": "ESA-JUICE-001",
            "portal": "ESAC Science Data Centre",
            "portal_url": "https://www.cosmos.esa.int/web/juice",
            "access_method": "OPEN_ACCESS_WEB",
            "year": 2023,
            "summary": "Gravity assist trajectories (Lunar-Earth, Venus, Earth) to reach Jupiter system in 2031 for Ganymede, Callisto, and Europa characterization."
        },
        "ESA-GAIA-DR3": {
            "title": "Gaia Data Release 3 (DR3): Astrometric, Photometric, and Radial Velocity Catalog",
            "report_number": "ESA-GAIA-DR3",
            "portal": "Gaia Archive / ESAC",
            "portal_url": "https://gea.esac.esa.int/archive/",
            "access_method": "TAP_API_AND_WEB",
            "year": 2022,
            "summary": "High-precision astrometry for 1.8 billion celestial sources, radial velocities for 33 million stars, and astrophysical parameters."
        },
        "ESA-COPERNICUS-SENTINEL": {
            "title": "Copernicus Sentinel-1 / Sentinel-2 Earth Observation Science Data Repository",
            "report_number": "ESA-COPERNICUS-EO",
            "portal": "Copernicus Data Space Ecosystem",
            "portal_url": "https://dataspace.copernicus.eu",
            "access_method": "OData_REST_API",
            "year": 2024,
            "summary": "Open-access radar and multispectral optical Earth observation imagery for environmental and atmospheric monitoring."
        }
    }

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Searches cataloged ESA public science and mission records."""
        q = query.lower()
        results = []
        for rep_id, item in self.PUBLIC_ESA_RECORDS.items():
            if q in rep_id.lower() or q in item["title"].lower() or q in item["summary"].lower():
                res = dict(item)
                res["source"] = "ESA_PUBLIC"
                res["checksum"] = hashlib.sha256(f"{rep_id}:{item['title']}".encode()).hexdigest()
                results.append(res)
        return results

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves verified metadata and access instructions for an ESA record."""
        rec = self.PUBLIC_ESA_RECORDS.get(record_id)
        if not rec:
            return None
        res = dict(rec)
        res["source"] = "ESA_PUBLIC"
        res["checksum"] = hashlib.sha256(f"{record_id}:{rec['title']}".encode()).hexdigest()
        return res
