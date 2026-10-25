"""
AASI 2.0 System Capabilities — Tool & Capability Inventory.
"""

from __future__ import annotations

from typing import List, Dict, Any
from backend.harness.tool_bus import global_tool_bus


class ToolInventory:
    """Manages the catalog of registered scientific tools, solvers, and runtime capabilities."""

    @classmethod
    def get_registered_tools(cls) -> List[Dict[str, Any]]:
        return global_tool_bus.list_tools()

    @classmethod
    def get_tool_names(cls) -> List[str]:
        return [t["name"] for t in global_tool_bus.list_tools()]
