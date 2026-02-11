"""Shared test fixtures for ddmcp tests."""

import pytest
from unittest.mock import MagicMock, patch

from ddmcp.config import DDMCPConfig


@pytest.fixture
def mock_config():
    """Provide a mock DDMCPConfig instance for tests.

    Returns:
        DDMCPConfig with test credentials
    """
    return DDMCPConfig(
        api_key="test_api_key",
        app_key="test_app_key",
        site="https://api.datadoghq.com",
        max_results=50,
    )


@pytest.fixture
def mock_api_client():
    """Provide a mock Datadog API client.

    This fixture mocks the get_api_client context manager
    to return a MagicMock instance instead of a real API client.

    Yields:
        MagicMock configured as an API client
    """
    mock_client = MagicMock()

    # Mock the context manager behavior
    with patch("ddmcp.client.get_api_client") as mock_get_client:
        mock_get_client.return_value.__enter__.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_span():
    """Provide a sample span response object.

    Returns:
        Mock object representing a Datadog span
    """
    span = MagicMock()
    span.id = "test-span-id"
    span.type = "span"
    span.attributes = MagicMock()
    span.attributes.attributes = {
        "span_id": "1234567890",
        "trace_id": "0987654321",
        "service": "web-service",
        "resource": "GET /api/users",
        "operation_name": "http.request",
        "start": "2024-01-15T10:30:00.000Z",
        "duration": 125000000,  # 125ms in nanoseconds
        "status": "ok",
        "tags": ["env:prod", "version:1.2.3"],
    }
    return span


@pytest.fixture
def sample_error_span():
    """Provide a sample error span response object.

    Returns:
        Mock object representing a Datadog error span
    """
    span = MagicMock()
    span.id = "test-error-span-id"
    span.type = "span"
    span.attributes = MagicMock()
    span.attributes.attributes = {
        "span_id": "error123",
        "trace_id": "trace456",
        "service": "api-service",
        "resource": "POST /api/orders",
        "operation_name": "http.request",
        "start": "2024-01-15T10:35:00.000Z",
        "duration": 500000000,  # 500ms
        "status": "error",
        "error": True,
        "error.type": "ValueError",
        "error.message": "Invalid order amount",
        "error.stack": "Traceback...",
        "tags": ["env:prod"],
    }
    return span


@pytest.fixture
def sample_aggregation_bucket():
    """Provide a sample aggregation bucket.

    Returns:
        MagicMock representing an aggregation bucket
    """
    bucket = MagicMock()
    bucket.by = {"resource_name": "GET /api/products"}
    bucket.computes = {"c0": 1500000000}  # 1.5s in nanoseconds
    return bucket


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for configuration.

    Args:
        monkeypatch: pytest monkeypatch fixture
    """
    monkeypatch.setenv("DD_API_KEY", "test_api_key")
    monkeypatch.setenv("DD_APP_KEY", "test_app_key")
    monkeypatch.setenv("DD_SITE", "us1")
