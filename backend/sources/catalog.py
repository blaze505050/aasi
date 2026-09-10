"""
AASI Scientific Source Catalog.

Central registry managing connectors and metadata for aerospace & scientific
repositories across 15 scientific disciplines.
"""

from typing import Dict, Any, List, Optional
from backend.sources.models import SourceMetadata, KnowledgeType, AccessMethod, SourceStatus
from backend.sources.nasa import NASASourceAdapter
from backend.sources.isro import ISROSourceAdapter
from backend.sources.esa import ESASourceAdapter
from backend.sources.spacex import SpaceXPublicSourceAdapter


class ScientificSourceCatalog:
    """Central catalog of scientific and aerospace literature & dataset sources."""

    CATEGORIES = [
        "AEROSPACE", "ASTRONOMY", "ASTROPHYSICS", "CFD",
        "ROCKET_PROPULSION", "ORBITAL_MECHANICS", "SPACECRAFT",
        "STRUCTURES", "THERMAL", "MATERIALS", "CONTROL",
        "ROBOTICS", "PLANETARY_SCIENCE", "EARTH_OBSERVATION", "SPACE_WEATHER"
    ]

    def __init__(self):
        self.sources: Dict[str, SourceMetadata] = {}
        self.nasa_adapter = NASASourceAdapter()
        self.isro_adapter = ISROSourceAdapter()
        self.esa_adapter = ESASourceAdapter()
        self.spacex_adapter = SpaceXPublicSourceAdapter()
        self._register_default_sources()

    def _register_default_sources(self):
        # 1. Primary Verified Sources
        self.sources["NASA_NTRS"] = self.nasa_adapter.METADATA
        self.sources["ISRO_PUBLIC"] = self.isro_adapter.METADATA
        self.sources["ESA_PUBLIC"] = self.esa_adapter.METADATA
        self.sources["SPACEX_PUBLIC"] = self.spacex_adapter.METADATA

        # 2. NACA Classic Archive
        self.sources["NACA_ARCHIVE"] = SourceMetadata(
            source_id="NACA_ARCHIVE",
            organization="NACA",
            name="National Advisory Committee for Aeronautics Classic Archive",
            category="AEROSPACE",
            base_url="https://ntrs.nasa.gov",
            access_method=AccessMethod.DIRECT_API,
            license="Public Domain",
            update_frequency="Static Archive",
            public_access=True,
            citation_policy="Cite NACA Technical Report / Note number",
            content_types=[KnowledgeType.TECHNICAL_REPORT, KnowledgeType.DATASET, KnowledgeType.EQUATION],
            status=SourceStatus.ACTIVE
        )

        # 3. arXiv (Physics / CFD / Aero)
        self.sources["ARXIV_AERO"] = SourceMetadata(
            source_id="ARXIV_AERO",
            organization="arXiv / Cornell University",
            name="arXiv Physics.Flu-Dyn and Aerodynamics Preprints",
            category="CFD",
            base_url="https://export.arxiv.org/api",
            access_method=AccessMethod.DIRECT_API,
            license="arXiv Non-exclusive Distribution / CC-BY",
            update_frequency="Daily",
            public_access=True,
            citation_policy="Cite arXiv identifier and author preprint",
            content_types=[KnowledgeType.PAPER, KnowledgeType.DOCUMENT],
            status=SourceStatus.ACTIVE
        )

        # 4. Open CFD Benchmarks
        self.sources["OPEN_CFD"] = SourceMetadata(
            source_id="OPEN_CFD",
            organization="OpenFOAM / ERCOFTAC / TMR",
            name="Turbulence Modeling Resource & Open CFD Benchmarks",
            category="CFD",
            base_url="https://turbmodels.larc.nasa.gov",
            access_method=AccessMethod.URL_REGISTRY,
            license="Public Domain / Open Access",
            update_frequency="Quarterly",
            public_access=True,
            citation_policy="Cite NASA TMR benchmark case and grid resolution",
            content_types=[KnowledgeType.CFD_RESULT, KnowledgeType.DATASET],
            status=SourceStatus.ACTIVE
        )

        # 5. Connectors Prepared for Future Expansion (Section 7)
        future_connectors = [
            ("NASA_ADS", "NASA Astrophysics Data System", "ASTRONOMY", "https://ui.adsabs.harvard.edu", AccessMethod.DIRECT_API),
            ("JPL_PDS", "Planetary Data System (JPL/NASA)", "PLANETARY_SCIENCE", "https://pds.nasa.gov", AccessMethod.URL_REGISTRY),
            ("NOAA_SWPC", "NOAA Space Weather Prediction Center", "SPACE_WEATHER", "https://www.swpc.noaa.gov", AccessMethod.DIRECT_API),
            ("COPERNICUS", "Copernicus Open Access Hub", "EARTH_OBSERVATION", "https://dataspace.copernicus.eu", AccessMethod.URL_REGISTRY),
            ("ZENODO_AERO", "Zenodo Open Research Repository", "AEROSPACE", "https://zenodo.org", AccessMethod.DIRECT_API),
            ("FIGSHARE_SCI", "Figshare Scientific Datasets", "MATERIALS", "https://figshare.com", AccessMethod.URL_REGISTRY),
            ("CERN_OPEN", "CERN Open Data Portal", "ASTROPHYSICS", "https://opendata.cern.ch", AccessMethod.URL_REGISTRY),
            ("USGS_AERO", "USGS Astrogeology Science Center", "PLANETARY_SCIENCE", "https://astrogeology.usgs.gov", AccessMethod.METADATA_INGESTION),
            ("KAGGLE_OPEN", "Kaggle Open Aerospace Datasets", "AEROSPACE", "https://www.kaggle.com/datasets", AccessMethod.MANUAL_IMPORT),
            ("GITHUB_SCI", "GitHub Curated Scientific Repositories", "SOFTWARE", "https://github.com", AccessMethod.URL_REGISTRY),
        ]

        for s_id, s_name, s_cat, s_url, s_access in future_connectors:
            self.sources[s_id] = SourceMetadata(
                source_id=s_id,
                organization=s_name.split()[0],
                name=s_name,
                category=s_cat,
                base_url=s_url,
                access_method=s_access,
                license="Open Access / Public Domain / Verified Open License",
                update_frequency="Continuous",
                public_access=True,
                citation_policy="Standard scholarly citation / Open DOI",
                content_types=[KnowledgeType.DOCUMENT, KnowledgeType.DATASET],
                status=SourceStatus.PLANNED
            )

    def list_sources(self, category: Optional[str] = None, active_only: bool = False) -> List[SourceMetadata]:
        """Returns registered sources matching category or status filters."""
        results = list(self.sources.values())
        if category:
            results = [s for s in results if s.category.upper() == category.upper()]
        if active_only:
            results = [s for s in results if s.status == SourceStatus.ACTIVE]
        return results

    def get_source(self, source_id: str) -> Optional[SourceMetadata]:
        """Looks up source by ID."""
        return self.sources.get(source_id)
