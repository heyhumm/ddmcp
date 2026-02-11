"""Datadog API client factory."""

from contextlib import contextmanager
from typing import Generator

from datadog_api_client import ApiClient, Configuration

from ddmcp.config import DDMCPConfig


@contextmanager
def get_api_client(config: DDMCPConfig) -> Generator[ApiClient, None, None]:
    """Create and configure a Datadog API client.

    This is a context manager that yields a configured ApiClient instance.
    The client is short-lived and should be created per tool call.

    Args:
        config: DDMCPConfig instance with API credentials and site

    Yields:
        Configured ApiClient instance

    Example:
        with get_api_client(config) as api_client:
            api_instance = SpansApi(api_client)
            response = api_instance.list_spans_get(...)
    """
    configuration = Configuration()

    # Set API credentials
    configuration.api_key["apiKeyAuth"] = config.api_key
    configuration.api_key["appKeyAuth"] = config.app_key

    # Set the Datadog site
    configuration.host = config.site

    # Create and yield the client
    with ApiClient(configuration) as api_client:
        yield api_client
