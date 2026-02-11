"""Tests for APM formatting utilities."""

import pytest
from unittest.mock import MagicMock

from ddmcp.domains.apm.formatting import (
    format_spans_response,
    format_aggregation_response,
    format_span_detail,
    _format_duration,
)


class TestFormatSpansResponse:
    """Tests for format_spans_response function."""

    def test_format_empty_spans(self):
        """Test formatting when no spans are found."""
        result = format_spans_response([], None)

        assert result == "No spans found matching the query."

    def test_format_single_span(self, sample_span):
        """Test formatting a single span."""
        result = format_spans_response([sample_span], 1)

        assert "# Span Search Results" in result
        assert "Showing 1 of 1 total spans" in result
        assert "web-service" in result
        assert "GET /api/users" in result
        assert "125ms" in result
        assert "ok" in result

    def test_format_multiple_spans(self, sample_span, sample_error_span):
        """Test formatting multiple spans."""
        result = format_spans_response([sample_span, sample_error_span], 2)

        assert "Showing 2 of 2 total spans" in result
        assert "web-service" in result
        assert "api-service" in result
        assert "ok" in result
        assert "error" in result

    def test_format_spans_without_total_count(self, sample_span):
        """Test formatting spans without total count metadata."""
        result = format_spans_response([sample_span], None)

        assert "# Span Search Results" in result
        assert "Showing" not in result  # No total count line
        assert "web-service" in result

    def test_format_spans_truncates_long_resources(self):
        """Test that long resource names are truncated."""
        span = MagicMock()
        span.id = "test"
        span.type = "span"
        span.attributes = MagicMock()
        span.attributes.attributes = {
            "service": "test-service",
            "resource": "GET /api/very/long/endpoint/path/that/should/be/truncated/to/fit",
            "start": "2024-01-15T10:30:00.000Z",
            "duration": 100000000,
            "status": "ok",
        }

        result = format_spans_response([span], 1)

        # Resource should be truncated to 40 chars + "..."
        assert len("GET /api/very/long/endpoint/path/that/should/be/truncated/to/fit") > 40
        assert "..." in result

    def test_format_spans_handles_missing_fields(self):
        """Test formatting spans with missing optional fields."""
        span = MagicMock()
        span.id = "test"
        span.type = "span"
        span.attributes = MagicMock()
        span.attributes.attributes = {
            # Only required fields
            "service": "test-service",
        }

        result = format_spans_response([span], 1)

        assert "N/A" in result
        assert "test-service" in result


class TestFormatAggregationResponse:
    """Tests for format_aggregation_response function."""

    def test_format_empty_buckets(self):
        """Test formatting when no aggregation results are found."""
        result = format_aggregation_response([], None)

        assert result == "No aggregation results found."

    def test_format_single_bucket(self, sample_aggregation_bucket):
        """Test formatting a single aggregation bucket."""
        result = format_aggregation_response([sample_aggregation_bucket], "resource_name")

        assert "# Span Aggregation Results" in result
        assert "Resource_Name" in result  # Title case header
        assert "GET /api/products" in result
        assert "1.50s" in result  # Duration formatted

    def test_format_multiple_buckets(self):
        """Test formatting multiple aggregation buckets."""
        bucket1 = MagicMock()
        bucket1.by = {"service": "web-service"}
        bucket1.computes = {"c0": 100, "c1": 2500000000}  # count and duration

        bucket2 = MagicMock()
        bucket2.by = {"service": "api-service"}
        bucket2.computes = {"c0": 200, "c1": 1500000000}

        result = format_aggregation_response([bucket1, bucket2], "service")

        assert "Service" in result
        assert "web-service" in result
        assert "api-service" in result
        assert "100" in result
        assert "200" in result

    def test_format_buckets_without_group_by(self):
        """Test formatting buckets without a group_by field."""
        bucket = MagicMock()
        bucket.by = {}
        bucket.computes = {"c0": 1500000000}

        result = format_aggregation_response([bucket], None)

        assert "# Span Aggregation Results" in result
        assert "Metric 1" in result

    def test_format_duration_values(self):
        """Test that large values are formatted as durations."""
        bucket = MagicMock()
        bucket.by = {"resource": "test"}
        bucket.computes = {"c0": 5000000000}  # 5s in nanoseconds

        result = format_aggregation_response([bucket], "resource")

        assert "5.00s" in result

    def test_format_small_count_values(self):
        """Test that small values are formatted as numbers, not durations."""
        bucket = MagicMock()
        bucket.by = {"resource": "test"}
        bucket.computes = {"c0": 42}  # Small count value

        result = format_aggregation_response([bucket], "resource")

        assert "42" in result
        assert "ns" not in result  # Should not be formatted as duration


class TestFormatSpanDetail:
    """Tests for format_span_detail function."""

    def test_format_basic_span_detail(self, sample_span):
        """Test formatting basic span details."""
        result = format_span_detail(sample_span)

        assert "# Span Details" in result
        assert "Span ID" in result
        assert "1234567890" in result
        assert "Trace ID" in result
        assert "0987654321" in result
        assert "Service" in result
        assert "web-service" in result
        assert "Resource" in result
        assert "GET /api/users" in result
        assert "Operation" in result
        assert "http.request" in result

    def test_format_span_timing_info(self, sample_span):
        """Test formatting timing information."""
        result = format_span_detail(sample_span)

        assert "## Timing" in result
        assert "Start" in result
        assert "2024-01-15T10:30:00.000Z" in result
        assert "Duration" in result
        assert "125ms" in result

    def test_format_span_status(self, sample_span):
        """Test formatting status."""
        result = format_span_detail(sample_span)

        assert "Status" in result
        assert "ok" in result

    def test_format_error_span_details(self, sample_error_span):
        """Test formatting error span with error details."""
        result = format_span_detail(sample_error_span)

        assert "## Error Details" in result
        assert "ValueError" in result
        assert "Invalid order amount" in result
        assert "Stack Trace" in result

    def test_format_span_tags(self, sample_span):
        """Test formatting span tags."""
        result = format_span_detail(sample_span)

        assert "## Tags" in result
        assert "env:prod" in result
        assert "version:1.2.3" in result

    def test_format_span_without_tags(self):
        """Test formatting span without tags."""
        span = MagicMock()
        span.id = "test"
        span.type = "span"
        span.attributes = MagicMock()
        span.attributes.attributes = {
            "span_id": "123",
            "trace_id": "456",
            "service": "test",
            "resource": "test",
            "operation_name": "test",
            "start": "2024-01-15T10:30:00.000Z",
            "duration": 100000000,
            "status": "ok",
            "tags": [],
        }

        result = format_span_detail(span)

        assert "# Span Details" in result
        assert "## Tags" not in result

    def test_format_span_custom_attributes(self):
        """Test formatting custom attributes starting with @."""
        span = MagicMock()
        span.id = "test"
        span.type = "span"
        span.attributes = MagicMock()
        span.attributes.attributes = {
            "span_id": "123",
            "trace_id": "456",
            "service": "test",
            "resource": "test",
            "operation_name": "test",
            "start": "2024-01-15T10:30:00.000Z",
            "duration": 100000000,
            "status": "ok",
            "@http.status_code": "200",
            "@http.method": "GET",
            "@custom.field": "value",
        }

        result = format_span_detail(span)

        assert "## Custom Attributes" in result
        assert "@http.method" in result
        assert "GET" in result
        assert "@http.status_code" in result
        assert "200" in result
        assert "@custom.field" in result
        assert "value" in result
        # @duration should be excluded
        assert "@duration" not in result or "## Timing" in result


class TestFormatDuration:
    """Tests for _format_duration function."""

    def test_format_duration_alias(self):
        """Test that _format_duration is an alias to format_duration."""
        # Test seconds
        assert _format_duration(1234567890) == "1.23s"

        # Test milliseconds
        assert _format_duration(456789000) == "457ms"

        # Test microseconds
        assert _format_duration(78900) == "78.9µs"

        # Test nanoseconds
        assert _format_duration(123) == "123ns"
