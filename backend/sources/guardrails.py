"""
AASI Scientific Citation & License Guardrails.

Prevents hallucinated or fabricated citations, validates data licenses,
and blocks unauthorized claims to proprietary corporate engineering data.
"""

from typing import Dict, Any, List, Optional
import re


class CitationGuardrail:
    """Validates citations to prevent fabricated reports or non-existent papers."""

    # Authoritative report prefixes recognized by scientific agencies
    KNOWN_REPORT_PATTERNS = [
        r"^NASA-[A-Z]{2,4}(?:-[A-Z0-9]+)*-\d+",  # NASA-TM-XXXX, NASA-TN-D-628, NASA-CR-XXXX, NASA-TP-XXXX
        r"^NACA-[A-Z]{2,4}(?:-[A-Z0-9]+)*-\d+",  # NACA-TR-XXXX, NACA-TN-XXXX, NACA-WR-XXXX
        r"^AGARD-[A-Z]{1,4}(?:-[A-Z0-9]+)*-\d+", # AGARD-AR-XXXX, AGARD-R-XXXX
        r"^ESA-[A-Z]{2,4}(?:-[A-Z0-9]+)*-\d+",   # ESA-SP-XXXX, ESA-STM-XXXX
        r"^ISRO-[A-Z0-9\-]+",                    # ISRO-VSSC-XXXX, ISRO-CHANDRAYAAN-3
        r"^arXiv:\d{4}\.\d{4,5}",                # arXiv:YYMM.NNNNN
        r"^AIAA-\d{4}-\d+",                      # AIAA-YYYY-XXXX
    ]


    ALLOWED_OPEN_LICENSES = [
        "Public Domain",
        "Public Domain (NASA Technical Report)",
        "CC0",
        "CC-BY",
        "CC-BY-4.0",
        "CC-BY-SA",
        "MIT",
        "Apache-2.0",
        "Open Data Commons",
    ]

    RESTRICTED_LICENSES = [
        "Proprietary",
        "ITAR-Controlled",
        "Export-Controlled",
        "Confidential",
        "Trade Secret",
    ]

    @classmethod
    def validate_report_identifier(cls, report_id: str) -> bool:
        """Checks if a report identifier matches authentic scientific agency naming syntax."""
        report_id = report_id.strip()
        for pattern in cls.KNOWN_REPORT_PATTERNS:
            if re.match(pattern, report_id, re.IGNORECASE):
                return True
        return False

    @classmethod
    def validate_license(cls, license_name: str) -> Dict[str, Any]:
        """Validates if dataset or literature license permits public computational use."""
        for allowed in cls.ALLOWED_OPEN_LICENSES:
            if allowed.lower() in license_name.lower():
                return {"valid": True, "open_access": True, "license": license_name}

        for restricted in cls.RESTRICTED_LICENSES:
            if restricted.lower() in license_name.lower():
                return {
                    "valid": False,
                    "open_access": False,
                    "error": f"Restricted license: '{license_name}'. Public computational ingestion blocked."
                }

        return {"valid": True, "open_access": False, "notice": f"Unclassified license: '{license_name}'. Requires manual review."}

    @classmethod
    def sanitize_corporate_claims(cls, claim_text: str) -> str:
        """Prevents agent from claiming access to internal proprietary databases (e.g. SpaceX internal CFD)."""
        prohibited_phrases = [
            "SpaceX internal CFD database",
            "proprietary SpaceX telemetry",
            "confidential SpaceX CAD",
            "SpaceX secret engineering data",
            "Boeing internal CFD database",
        ]
        sanitized = claim_text
        for phrase in prohibited_phrases:
            if phrase.lower() in sanitized.lower():
                sanitized = re.sub(phrase, "[UNAVAILABLE - PROPRIETARY INTERNAL DATA]", sanitized, flags=re.IGNORECASE)
        return sanitized
