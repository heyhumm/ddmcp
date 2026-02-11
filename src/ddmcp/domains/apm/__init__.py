"""APM (Application Performance Monitoring) domain for ddmcp.

This module provides tools for querying APM spans, analyzing traces,
and working with service definitions.
"""

import inspect
from typing import Callable, get_type_hints

from fastmcp import FastMCP

from ddmcp.config import DDMCPConfig
from ddmcp.domains.apm import services, spans


def bind_config(func: Callable, config: DDMCPConfig) -> Callable:
    """Bind config to a tool function while preserving metadata.

    This creates a wrapper that injects config as the first argument,
    while preserving __name__, __doc__, and annotations for FastMCP.

    Args:
        func: The tool function that expects config as first parameter
        config: DDMCPConfig instance to bind

    Returns:
        Wrapper function with config bound and metadata preserved
    """
    # Get the original signature and remove the 'config' parameter
    sig = inspect.signature(func)
    params = [p for name, p in sig.parameters.items() if name != 'config']
    new_sig = sig.replace(parameters=params)

    # Create wrapper that injects config
    def wrapper(*args, **kwargs):
        return func(config, *args, **kwargs)

    # Copy metadata from original function
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__module__ = func.__module__
    wrapper.__qualname__ = func.__qualname__

    # Set annotations without 'config'
    try:
        type_hints = get_type_hints(func)
        wrapper.__annotations__ = {
            k: v for k, v in type_hints.items()
            if k != 'config'
        }
    except Exception:
        # Fallback to raw annotations if get_type_hints fails
        if hasattr(func, '__annotations__'):
            wrapper.__annotations__ = {
                k: v for k, v in func.__annotations__.items()
                if k != 'config'
            }

    # Set the new signature
    wrapper.__signature__ = new_sig

    return wrapper


def create_server(config: DDMCPConfig) -> FastMCP:
    """Create the APM sub-server with all APM tools.

    Args:
        config: DDMCPConfig instance

    Returns:
        FastMCP sub-server instance with APM tools registered
    """
    # Create the APM sub-server
    apm_server = FastMCP("APM")

    # Register span tools (bind config using wrapper)
    apm_server.tool()(bind_config(spans.search_spans, config))
    apm_server.tool()(bind_config(spans.get_slow_endpoints, config))
    apm_server.tool()(bind_config(spans.aggregate_spans, config))
    apm_server.tool()(bind_config(spans.get_span_by_id, config))

    # Register service tools (bind config using wrapper)
    apm_server.tool()(bind_config(services.list_services, config))
    apm_server.tool()(bind_config(services.get_service, config))
    apm_server.tool()(bind_config(services.get_service_stats, config))

    return apm_server
