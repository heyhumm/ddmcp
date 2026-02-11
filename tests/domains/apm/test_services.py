"""Tests for APM service catalog and statistics tools."""

import pytest
from unittest.mock import MagicMock, patch

from ddmcp.domains.apm.services import (
    list_services,
    get_service,
    get_service_stats,
)


class TestApmListServices:
    """Tests for list_services tool."""

    def test_list_services_basic(self, mock_config):
        """Test listing services with default parameters."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            # Create mock service definitions
            service1 = MagicMock()
            service1.attributes.meta = {"service-name": "web-service"}
            service1.attributes.schema_version = "v2.2"

            service2 = MagicMock()
            service2.attributes.meta = {"service-name": "api-service"}
            service2.attributes.schema_version = "v2.2"

            mock_response = MagicMock()
            mock_response.data = [service1, service2]
            mock_api.list_service_definitions.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = list_services(mock_config)

                assert "# APM Services" in result
                assert "web-service" in result
                assert "api-service" in result
                assert "v2.2" in result
                mock_api.list_service_definitions.assert_called_once_with(
                    page_size=25,
                    page_number=0,
                )

    def test_list_services_with_pagination(self, mock_config):
        """Test listing services with custom pagination."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            # Create mock service definition
            service = MagicMock()
            service.attributes.meta = {"service-name": "test-service"}
            service.attributes.schema_version = "v2.2"

            mock_response = MagicMock()
            mock_response.data = [service]
            mock_api.list_service_definitions.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = list_services(mock_config, page_size=50, page_number=2)

                mock_api.list_service_definitions.assert_called_once_with(
                    page_size=50,
                    page_number=2,
                )
                assert "Page 3" in result  # page_number 2 = page 3 (0-indexed)

    def test_list_services_empty(self, mock_config):
        """Test listing services when no services found."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_response = MagicMock()
            mock_response.data = []
            mock_api.list_service_definitions.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = list_services(mock_config)

                assert "No services found" in result

    def test_list_services_with_metadata(self, mock_config):
        """Test listing services with additional metadata."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            service = MagicMock()
            service.attributes.meta = {"service-name": "test-service"}
            service.attributes.schema_version = "v2.2"
            service.attributes.tier = "critical"

            # Add contact information
            contact = MagicMock()
            contact.email = "team@example.com"
            service.attributes.contact = contact

            mock_response = MagicMock()
            mock_response.data = [service]
            mock_api.list_service_definitions.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = list_services(mock_config)

                assert "test-service" in result
                assert "critical" in result
                assert "team@example.com" in result

    def test_list_services_pagination_hint(self, mock_config):
        """Test that pagination hint appears when more pages likely exist."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            # Create exactly page_size services to trigger pagination hint
            services = []
            for i in range(25):
                service = MagicMock()
                service.attributes.meta = {"service-name": f"service-{i}"}
                service.attributes.schema_version = "v2.2"
                services.append(service)

            mock_response = MagicMock()
            mock_response.data = services
            mock_api.list_service_definitions.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = list_services(mock_config, page_size=25)

                assert "There may be more services" in result
                assert "page_number=1" in result

    def test_list_services_handles_exception(self, mock_config):
        """Test that exceptions are handled gracefully."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_service_definitions.side_effect = Exception("API error")

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = list_services(mock_config)

                assert "Error listing services" in result
                assert "API error" in result


class TestApmGetService:
    """Tests for get_service tool."""

    def test_get_service_basic(self, mock_config):
        """Test getting a service with basic information."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            service = MagicMock()
            service.attributes.schema_version = "v2.2"
            service.attributes.description = "Main web service"
            service.attributes.tier = "critical"

            mock_response = MagicMock()
            mock_response.data = service
            mock_api.get_service_definition.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = get_service(mock_config, service_name="web-service")

                assert "# Service: web-service" in result
                assert "Main web service" in result
                assert "v2.2" in result
                assert "critical" in result
                mock_api.get_service_definition.assert_called_once_with(
                    service_name="web-service",
                    schema_version="v2.2",
                )

    def test_get_service_with_custom_schema_version(self, mock_config):
        """Test getting a service with custom schema version."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_response = MagicMock()
            mock_response.data = MagicMock(attributes=MagicMock(schema_version="v2.1"))
            mock_api.get_service_definition.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = get_service(mock_config, service_name="test", schema_version="v2.1")

                mock_api.get_service_definition.assert_called_once_with(
                    service_name="test",
                    schema_version="v2.1",
                )

    def test_get_service_with_contact_info(self, mock_config):
        """Test getting a service with contact information."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            service = MagicMock()
            service.attributes.schema_version = "v2.2"

            contact = MagicMock()
            contact.email = "platform-team@example.com"
            contact.slack = "#platform-alerts"
            service.attributes.contact = contact

            mock_response = MagicMock()
            mock_response.data = service
            mock_api.get_service_definition.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = get_service(mock_config, service_name="test")

                assert "## Contact" in result
                assert "platform-team@example.com" in result
                assert "#platform-alerts" in result

    def test_get_service_with_links(self, mock_config):
        """Test getting a service with links."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            service = MagicMock()
            service.attributes.schema_version = "v2.2"
            service.attributes.links = [
                {"name": "Runbook", "url": "https://wiki.example.com/runbook", "type": "doc"},
                {"name": "Dashboard", "url": "https://app.datadoghq.com/dashboard", "type": "dashboard"},
            ]

            mock_response = MagicMock()
            mock_response.data = service
            mock_api.get_service_definition.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = get_service(mock_config, service_name="test")

                assert "## Links" in result
                assert "Runbook" in result
                assert "https://wiki.example.com/runbook" in result
                assert "Dashboard" in result

    def test_get_service_with_tags(self, mock_config):
        """Test getting a service with tags."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            service = MagicMock()
            service.attributes.schema_version = "v2.2"
            service.attributes.tags = ["team:platform", "language:python", "framework:flask"]

            mock_response = MagicMock()
            mock_response.data = service
            mock_api.get_service_definition.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = get_service(mock_config, service_name="test")

                assert "## Tags" in result
                assert "team:platform" in result
                assert "language:python" in result
                assert "framework:flask" in result

    def test_get_service_not_found(self, mock_config):
        """Test getting a service that doesn't exist."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_response = MagicMock()
            mock_response.data = None
            mock_api.get_service_definition.return_value = mock_response

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = get_service(mock_config, service_name="nonexistent")

                assert "Service 'nonexistent' not found" in result

    def test_get_service_handles_exception(self, mock_config):
        """Test that exceptions are handled gracefully."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.get_service_definition.side_effect = Exception("API error")

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.ServiceDefinitionApi", return_value=mock_api):
                result = get_service(mock_config, service_name="test")

                assert "Error retrieving service 'test'" in result
                assert "API error" in result


class TestApmGetServiceStats:
    """Tests for get_service_stats tool."""

    def test_get_service_stats_basic(self, mock_config):
        """Test getting basic service statistics."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            # Mock count response
            count_bucket = MagicMock()
            count_bucket.by = {"status": "ok"}
            count_bucket.computes = {"c0": 1000}

            count_response = MagicMock()
            count_response.get.return_value = {"buckets": [count_bucket]}
            count_response.data = MagicMock()
            count_response.data.buckets = [count_bucket]

            # Second call for latency
            latency_bucket = MagicMock()
            latency_bucket.computes = {
                "c0": 50000000,   # p50: 50ms
                "c1": 100000000,  # p75: 100ms
                "c2": 200000000,  # p95: 200ms
                "c3": 500000000,  # p99: 500ms
            }

            latency_response = MagicMock()
            latency_response.data = MagicMock()
            latency_response.data.buckets = [latency_bucket]

            # Configure side_effect to return different responses
            mock_api.aggregate_spans.side_effect = [count_response, latency_response]

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.SpansApi", return_value=mock_api):
                result = get_service_stats(mock_config, service_name="web-service")

                assert "# Service Statistics: web-service" in result
                assert "## Request Metrics" in result
                assert "1,000" in result
                assert "## Latency Percentiles" in result
                assert "50ms" in result
                assert "100ms" in result
                assert "200ms" in result
                assert "500ms" in result

    def test_get_service_stats_with_errors(self, mock_config):
        """Test getting service statistics with error counts."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            # Mock count response with errors
            ok_bucket = MagicMock()
            ok_bucket.by = {"status": "ok"}
            ok_bucket.computes = {"c0": 900}

            error_bucket = MagicMock()
            error_bucket.by = {"status": "error"}
            error_bucket.computes = {"c0": 100}

            count_response = MagicMock()
            count_response.data.buckets = [ok_bucket, error_bucket]

            latency_response = MagicMock()
            latency_response.data.buckets = [MagicMock(computes={"c0": 100000000})]

            mock_api.aggregate_spans.side_effect = [count_response, latency_response]

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.SpansApi", return_value=mock_api):
                result = get_service_stats(mock_config, service_name="api-service")

                assert "1,000" in result  # Total: 900 + 100
                assert "100" in result    # Error count
                assert "10.0%" in result  # Error rate

    def test_get_service_stats_with_env_filter(self, mock_config):
        """Test getting service statistics with environment filter."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            count_response = MagicMock()
            count_response.data.buckets = []
            latency_response = MagicMock()
            latency_response.data.buckets = []

            mock_api.aggregate_spans.side_effect = [count_response, latency_response]

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.SpansApi", return_value=mock_api):
                result = get_service_stats(
                    mock_config,
                    service_name="test-service",
                    env="prod",
                )

                assert "Environment**: prod" in result
                # Verify query includes env filter
                call_args = mock_api.aggregate_spans.call_args_list[0]
                request_body = call_args.kwargs["body"]
                query = request_body["filter"]["query"]
                assert "env:prod" in query

    def test_get_service_stats_custom_time_range(self, mock_config):
        """Test getting service statistics with custom time range."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            count_response = MagicMock()
            count_response.data.buckets = []
            latency_response = MagicMock()
            latency_response.data.buckets = []

            mock_api.aggregate_spans.side_effect = [count_response, latency_response]

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.SpansApi", return_value=mock_api):
                result = get_service_stats(
                    mock_config,
                    service_name="test",
                    time_from="now-24h",
                    time_to="now-12h",
                )

                assert "now-24h to now-12h" in result

    def test_get_service_stats_no_requests(self, mock_config):
        """Test getting service statistics when no requests found."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()

            count_response = MagicMock()
            count_response.data.buckets = []
            latency_response = MagicMock()
            latency_response.data.buckets = []

            mock_api.aggregate_spans.side_effect = [count_response, latency_response]

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.SpansApi", return_value=mock_api):
                result = get_service_stats(mock_config, service_name="test")

                assert "Total Requests**: 0" in result
                assert "No requests found" in result

    def test_get_service_stats_handles_exception(self, mock_config):
        """Test that exceptions are handled gracefully."""
        with patch("ddmcp.domains.apm.services.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.aggregate_spans.side_effect = Exception("API error")

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.services.SpansApi", return_value=mock_api):
                result = get_service_stats(mock_config, service_name="test")

                assert "Error retrieving stats for service 'test'" in result
                assert "API error" in result
