"""HTTP server mode for ddmcp MCP server.

This allows remote clients to connect over HTTP instead of stdio.
"""

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from ddmcp.server import create_server


async def health(request):
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "server": "ddmcp"})


def main() -> None:
    """Run the MCP server in HTTP mode."""
    try:
        server = create_server()

        # Get the MCP app
        mcp_app = server.http_app()

        # Create a new Starlette app that wraps the MCP app and adds health endpoint
        app = Starlette(
            routes=[
                Route("/health", health),
                Mount("/", mcp_app),
            ]
        )

        # Run with uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",  # Listen on all interfaces
            port=8000,
            log_level="info",
        )
    except ValueError as e:
        print(f"Configuration error: {e}")
        raise SystemExit(1) from e
    except Exception as e:
        print(f"Error starting ddmcp HTTP server: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
