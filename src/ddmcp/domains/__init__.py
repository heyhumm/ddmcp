"""Domain registry for ddmcp.

This module provides the central registry for all domain sub-servers.
Each domain is registered explicitly and mounted with a namespace prefix.
"""

from fastmcp import FastMCP

from ddmcp.config import DDMCPConfig
from ddmcp.domains.apm import create_server as create_apm_server


def get_domain_servers(config: DDMCPConfig) -> list[tuple[str, FastMCP]]:
    """Get all registered domain sub-servers.

    Each domain is returned as a (namespace, server) tuple. The namespace
    is used as a prefix for all tools in that domain (e.g., "apm" → "apm_search_spans").

    Args:
        config: DDMCPConfig instance to pass to domain servers

    Returns:
        List of (namespace, FastMCP) tuples for all registered domains
    """
    return [
        ("apm", create_apm_server(config)),
    ]
