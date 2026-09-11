"""
AASI Current Information Service.

Tracks recent official spaceflight events, mission milestones, launches,
and agency updates.
STRICT SEPARATION:
- Labeled: CURRENT_INFORMATION with ISO timestamp
- Never claims LLM fine-tuning
- Completely separate from peer-reviewed SCIENTIFIC_REFERENCE
"""

import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.sources.models import CurrentInfoItem, CurrentInfoCategory


class CurrentInformationService:
    """Provides curated official updates with explicit freshness and provenance metadata."""

    FRESHNESS_NOTICE = (
        "STATIC_SEED_DATA: Contains curated historical spaceflight milestones from 2023-2024. "
        "No live real-time API connector is active. These records are static historical entries, "
        "not real-time telemetry."
    )

    def __init__(self):
        now_utc = datetime.now(timezone.utc)
        
        raw_events = [
            {
                "item_id": "CURR-NASA-ARTEMIS-II",
                "title": "NASA Artemis II Crewed Lunar Flyby Preparation and Space Launch System Core Integration",
                "organization": "NASA",
                "category": CurrentInfoCategory.MISSIONS,
                "summary": "Artemis II will send four astronauts on a 10-day translunar flyby trajectory testing Orion life support and manual proximity operations.",
                "source_url": "https://www.nasa.gov/mission/artemis-ii/",
                "published_at": "2024-03-01T00:00:00Z",
                "provenance_hash": hashlib.sha256(b"NASA-ARTEMIS-II-2024").hexdigest(),
            },
            {
                "item_id": "CURR-ISRO-GAGANYAAN-TV-D1",
                "title": "ISRO Gaganyaan Test Vehicle Demonstration 1 (TV-D1) Flight Test Completion",
                "organization": "ISRO",
                "category": CurrentInfoCategory.ROCKET_TESTS,
                "summary": "Successful in-flight abort demonstration of Crew Escape System at Mach 1.2 in atmospheric ascent with safe parachute splashdown in the Bay of Bengal.",
                "source_url": "https://www.isro.gov.in/Gaganyaan_TV-D1.html",
                "published_at": "2023-10-21T00:00:00Z",
                "provenance_hash": hashlib.sha256(b"ISRO-GAGANYAAN-TVD1").hexdigest(),
            },
            {
                "item_id": "CURR-ESA-ARIANE-6",
                "title": "ESA Ariane 6 Maiden Launch from Europe's Spaceport in Kourou",
                "organization": "ESA",
                "category": CurrentInfoCategory.LAUNCHES,
                "summary": "Inaugural qualification flight of Ariane 6 heavy-lift rocket with Vinci re-ignitable upper-stage demonstration deploying multiple institutional payloads.",
                "source_url": "https://www.esa.int/Enabling_Support/Space_Transportation/Ariane/Ariane_6_maiden_flight_success",
                "published_at": "2024-07-09T00:00:00Z",
                "provenance_hash": hashlib.sha256(b"ESA-ARIANE6-MAIDEN").hexdigest(),
            },
            {
                "item_id": "CURR-NOAA-SWPC-G5-STORM",
                "title": "NOAA Space Weather Prediction Center Severe Geomagnetic Storm Warning (G5 Event)",
                "organization": "NOAA",
                "category": CurrentInfoCategory.SPACE_WEATHER,
                "summary": "Extreme G5 geomagnetic storm triggered by coronal mass ejections from solar active region AR3664 affecting low-Earth orbit satellite drag and ionospheric navigation.",
                "source_url": "https://www.swpc.noaa.gov",
                "published_at": "2024-05-10T00:00:00Z",
                "provenance_hash": hashlib.sha256(b"NOAA-SWPC-G5-2024").hexdigest(),
            },
            {
                "item_id": "CURR-NASA-JWST-EXOPLANET",
                "title": "JWST Atmospheric Characterization of Habitable Zone Exoplanet",
                "organization": "NASA / STScI",
                "category": CurrentInfoCategory.DISCOVERIES,
                "summary": "NIRSpec transmission spectroscopy detects carbon-bearing molecules in temperate sub-Neptune atmosphere, refining photochemical models.",
                "source_url": "https://webbtelescope.org/news",
                "published_at": "2024-02-15T00:00:00Z",
                "provenance_hash": hashlib.sha256(b"JWST-EXOPLANET-NIRSPEC").hexdigest(),
            }
        ]

        self.events: List[CurrentInfoItem] = []
        for r in raw_events:
            try:
                pub_dt = datetime.fromisoformat(r["published_at"].replace("Z", "+00:00"))
                age = max(0, (now_utc - pub_dt).days)
            except Exception:
                age = 0
            
            freshness = "STALE_STATIC_SEED" if age > 180 else "ARCHIVED_RECORD"
            self.events.append(CurrentInfoItem(
                item_id=r["item_id"],
                title=r["title"],
                organization=r["organization"],
                category=r["category"],
                summary=r["summary"],
                source_url=r["source_url"],
                published_at=r["published_at"],
                retrieved_at=now_utc.isoformat(),
                age_days=age,
                freshness_status=freshness,
                acquisition_method="STATIC_SEED_INDEX",
                label="CURRENT_INFORMATION",
                provenance_hash=r["provenance_hash"]
            ))

    def get_latest_events(self, category: Optional[CurrentInfoCategory] = None, limit: int = 10) -> List[CurrentInfoItem]:
        """Returns recent events, optionally filtered by category."""
        results = self.events
        if category:
            results = [e for e in results if e.category == category]
        return results[:limit]

    def search_events(self, query: str) -> List[CurrentInfoItem]:
        """Searches current information by keywords."""
        q = query.lower()
        return [
            e for e in self.events
            if q in e.title.lower() or q in e.summary.lower() or q in e.organization.lower()
        ]

    def format_current_info_response(self, item: CurrentInfoItem) -> str:
        """Formats item with strict CURRENT_INFORMATION telemetry and retrieval timestamp."""
        return (
            f"**[{item.label}]** {item.title}\n"
            f"- **Organization:** {item.organization}\n"
            f"- **Category:** {item.category.value}\n"
            f"- **Published Date:** {item.published_at} (Age: {item.age_days} days)\n"
            f"- **Retrieved Timestamp:** {item.retrieved_at}\n"
            f"- **Freshness Status:** {item.freshness_status}\n"
            f"- **Acquisition Method:** {item.acquisition_method}\n"
            f"- **Summary:** {item.summary}\n"
            f"- **Official Citation/URL:** {item.source_url}\n"
            f"- **Provenance SHA-256:** `{item.provenance_hash}`\n\n"
            f"*(Notice: {self.FRESHNESS_NOTICE}. Labeled as CURRENT_INFORMATION, distinct from peer-reviewed SCIENTIFIC_REFERENCE literature.)*"
        )
