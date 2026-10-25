"""
AASI 2.0 Runtime Governor — Network Access Policy.
"""

from __future__ import annotations

import re
from typing import Tuple, List

PERMITTED_HOSTS = [
    r"^localhost$",
    r"^127\.0\.0\.1$",
    r"^0\.0\.0\.0$",
]


class NetworkPolicy:
    """Enforces strict outbound network boundary. Blocks SSRF and unauthorized internet requests."""

    @classmethod
    def validate_destination(cls, host: str, allow_external: bool = False) -> Tuple[bool, str]:
        if not host:
            return False, "Destination host is empty"

        for pat in PERMITTED_HOSTS:
            if re.match(pat, host, re.IGNORECASE):
                return True, ""

        if allow_external:
            return True, ""

        return False, f"Outbound external network connection to '{host}' blocked by safety policy"
