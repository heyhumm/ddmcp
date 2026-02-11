"""Main FastMCP server for ddmcp.

This module creates the main MCP server and mounts all domain sub-servers
with namespace prefixes.
"""

from fastmcp import FastMCP

from ddmcp.config import DDMCPConfig
from ddmcp.domains import get_domain_servers


def create_server() -> FastMCP:
    """Create and configure the main ddmcp server.

    This function:
    1. Loads configuration from environment variables
    2. Creates the main FastMCP server instance
    3. Mounts all domain sub-servers with namespace prefixes

    Returns:
        Configured FastMCP server instance

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    # Load configuration from environment
    config = DDMCPConfig.from_env()

    # Create main server
    mcp = FastMCP("ddmcp")

    # Get and mount all domain sub-servers
    domain_servers = get_domain_servers(config)

    for namespace, domain_server in domain_servers:
        # Mount each domain server with its namespace prefix
        # This automatically prefixes all tools (e.g., "search_spans" -> "apm_search_spans")
        mcp.mount(domain_server, prefix=namespace)

    return mcp


def main() -> None:
    """CLI entry point for ddmcp.

    This function is called when running `ddmcp` from the command line.
    It creates the server and runs it via FastMCP's built-in runner.
    """
    try:
        server = create_server()
        server.run()
    except ValueError as e:
        # Configuration errors are caught and displayed with helpful messages
        print(f"Configuration error: {e}")
        raise SystemExit(1) from e
    except Exception as e:
        # Unexpected errors
        print(f"Error starting ddmcp server: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
