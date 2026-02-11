"""Tests for APM span tools."""

import pytest
from unittest.mock import MagicMock, patch

from ddmcp.domains.apm.spans import (
    search_spans,
    get_slow_endpoints,
    aggregate_spans,
    get_span_by_id,
)


class TestApmSearchSpans:
    """Tests for the search_spans tool."""

    def test_search_spans_with_query(self, mock_config):
        """Test searching spans with a query."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            # Create mock API response
            mock_api = MagicMock()
            span1 = MagicMock()
            span1.id = "span1"
            span1.type = "span"
            span1.attributes = MagicMock()
            span1.attributes.attributes = {
                "service": "web-service",
                "resource": "GET /api/users",
                "start": "2024-01-15T10:30:00.000Z",
                "duration": 125000000,
                "status": "ok",
            }

            mock_api.list_spans.return_value = {
                "data": [span1],
                "meta": {"page": {"total_count": 1}},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = search_spans(mock_config, query="service:web-service env:prod")

                assert "Span Search Results" in result
                assert "web-service" in result
                assert "GET /api/users" in result
                mock_api.list_spans.assert_called_once()

    def test_search_spans_with_time_range(self, mock_config):
        """Test searching spans with custom time range."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_spans.return_value = {
                "data": [],
                "meta": {"page": {"total_count": 0}},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = search_spans(
                    mock_config,
                    query="service:test",
                    time_from="now-2h",
                    time_to="now-1h",
                )

                assert "No spans found" in result
                mock_api.list_spans.assert_called_once()

                # Verify time range was passed correctly
                call_args = mock_api.list_spans.call_args
                request_body = call_args.kwargs["body"]
                assert request_body["filter"]["from"] == "now-2h"
                assert request_body["filter"]["to"] == "now-1h"

    def test_search_spans_with_limit(self, mock_config):
        """Test searching spans with custom limit."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_spans.return_value = {
                "data": [],
                "meta": {"page": {"total_count": 0}},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = search_spans(mock_config, query="service:test", limit=10)

                # Verify limit was passed correctly
                call_args = mock_api.list_spans.call_args
                request_body = call_args.kwargs["body"]
                assert request_body["page"]["limit"] == 10

    def test_search_spans_sort_ascending(self, mock_config):
        """Test searching spans with ascending sort order."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_spans.return_value = {
                "data": [],
                "meta": {"page": {"total_count": 0}},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = search_spans(mock_config, query="service:test", sort="timestamp_asc")

                # Verify sort order
                call_args = mock_api.list_spans.call_args
                request_body = call_args.kwargs["body"]
                assert "ascending" in str(request_body["sort"]).lower()


class TestApmGetSlowEndpoints:
    """Tests for the get_slow_endpoints tool."""

    def test_get_slow_endpoints_basic(self, mock_config):
        """Test finding slow endpoints."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            slow_span = MagicMock()
            slow_span.id = "slow1"
            slow_span.type = "span"
            slow_span.attributes = MagicMock()
            slow_span.attributes.attributes = {
                "service": "api-service",
                "resource": "POST /api/heavy-operation",
                "start": "2024-01-15T10:30:00.000Z",
                "duration": 5000000000,  # 5s
                "status": "ok",
            }

            mock_api.list_spans.return_value = {
                "data": [slow_span],
                "meta": {"page": {"total_count": 1}},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = get_slow_endpoints(
                    mock_config,
                    service="api-service",
                    min_duration_ms=1000,
                )

                assert "Span Search Results" in result
                assert "api-service" in result
                assert "5.00s" in result
                mock_api.list_spans.assert_called_once()

    def test_get_slow_endpoints_with_env_filter(self, mock_config):
        """Test finding slow endpoints with environment filter."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_spans.return_value = {
                "data": [],
                "meta": {"page": {"total_count": 0}},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = get_slow_endpoints(
                    mock_config,
                    service="test-service",
                    min_duration_ms=2000,
                    env="prod",
                )

                # Verify query includes both service and env
                call_args = mock_api.list_spans.call_args
                request_body = call_args.kwargs["body"]
                query = request_body["filter"]["query"]
                assert "service:test-service" in query
                assert "env:prod" in query
                assert "@duration:>=" in query

    def test_get_slow_endpoints_converts_duration(self, mock_config):
        """Test that milliseconds are converted to nanoseconds in query."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_spans.return_value = {
                "data": [],
                "meta": {"page": {"total_count": 0}},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = get_slow_endpoints(
                    mock_config,
                    service="test-service",
                    min_duration_ms=500,  # 500ms
                )

                call_args = mock_api.list_spans.call_args
                request_body = call_args.kwargs["body"]
                query = request_body["filter"]["query"]
                # 500ms = 500,000,000ns
                assert "500000000" in query


class TestApmAggregateSpans:
    """Tests for the aggregate_spans tool."""

    def test_aggregate_spans_by_resource(self, mock_config):
        """Test aggregating spans by resource name."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            bucket1 = MagicMock()
            bucket1.by = {"resource_name": "GET /api/users"}
            bucket1.computes = {"c0": 1500000000}

            mock_api.aggregate_spans.return_value = {
                "data": {"buckets": [bucket1]},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = aggregate_spans(
                    mock_config,
                    query="service:web-service",
                    group_by="resource_name",
                    compute_metric="p95_duration",
                )

                assert "Span Aggregation Results" in result
                assert "GET /api/users" in result
                mock_api.aggregate_spans.assert_called_once()

    def test_aggregate_spans_count_metric(self, mock_config):
        """Test aggregating spans with count metric."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.aggregate_spans.return_value = {
                "data": {"buckets": []},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = aggregate_spans(
                    mock_config,
                    query="service:test",
                    compute_metric="count",
                )

                # Verify count metric was used (count doesn't need compute field)
                call_args = mock_api.aggregate_spans.call_args
                request_body = call_args.kwargs["body"]
                assert request_body["compute"] == []

    def test_aggregate_spans_avg_duration_metric(self, mock_config):
        """Test aggregating spans with average duration metric."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.aggregate_spans.return_value = {
                "data": {"buckets": []},
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = aggregate_spans(
                    mock_config,
                    query="service:test",
                    compute_metric="avg_duration",
                )

                # Verify average aggregation was used
                call_args = mock_api.aggregate_spans.call_args
                request_body = call_args.kwargs["body"]
                assert len(request_body["compute"]) > 0

    def test_aggregate_spans_percentile_metrics(self, mock_config):
        """Test aggregating spans with various percentile metrics."""
        percentiles = ["p50_duration", "p75_duration", "p90_duration", "p95_duration", "p99_duration"]

        for percentile in percentiles:
            with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
                mock_api = MagicMock()
                mock_api.aggregate_spans.return_value = {
                    "data": {"buckets": []},
                }

                mock_client.return_value.__enter__.return_value = MagicMock()
                with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                    result = aggregate_spans(
                        mock_config,
                        query="service:test",
                        compute_metric=percentile,
                    )

                    # Verify percentile was used
                    call_args = mock_api.aggregate_spans.call_args
                    request_body = call_args.kwargs["body"]
                    assert len(request_body["compute"]) > 0


class TestApmGetSpanById:
    """Tests for the get_span_by_id tool."""

    def test_get_span_by_id_found(self, mock_config, sample_span):
        """Test retrieving a span by ID when found."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_spans.return_value = {
                "data": [sample_span],
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = get_span_by_id(mock_config, span_id="1234567890")

                assert "# Span Details" in result
                assert "1234567890" in result
                mock_api.list_spans.assert_called_once()

                # Verify query format
                call_args = mock_api.list_spans.call_args
                request_body = call_args.kwargs["body"]
                assert "@span_id:1234567890" in request_body["filter"]["query"]

    def test_get_span_by_id_not_found(self, mock_config):
        """Test retrieving a span by ID when not found."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_spans.return_value = {
                "data": [],
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = get_span_by_id(mock_config, span_id="nonexistent")

                assert "No span found with ID: nonexistent" in result
                assert "Try expanding the time window" in result

    def test_get_span_by_id_custom_time_window(self, mock_config, sample_span):
        """Test retrieving a span with custom time window."""
        with patch("ddmcp.domains.apm.spans.get_api_client") as mock_client:
            mock_api = MagicMock()
            mock_api.list_spans.return_value = {
                "data": [sample_span],
            }

            mock_client.return_value.__enter__.return_value = MagicMock()
            with patch("ddmcp.domains.apm.spans.SpansApi", return_value=mock_api):
                result = get_span_by_id(
                    mock_config,
                    span_id="1234567890",
                    time_from="now-48h",
                    time_to="now-24h",
                )

                # Verify custom time window
                call_args = mock_api.list_spans.call_args
                request_body = call_args.kwargs["body"]
                assert request_body["filter"]["from"] == "now-48h"
                assert request_body["filter"]["to"] == "now-24h"
