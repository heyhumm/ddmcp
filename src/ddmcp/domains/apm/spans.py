"""APM span search and query tools."""

from typing import Annotated, Literal

from datadog_api_client.v2.api.spans_api import SpansApi
from datadog_api_client.v2.model.spans_list_request import SpansListRequest
from datadog_api_client.v2.model.spans_query_filter import SpansQueryFilter
from datadog_api_client.v2.model.spans_list_request_page import SpansListRequestPage
from datadog_api_client.v2.model.spans_sort import SpansSort
from datadog_api_client.v2.model.spans_aggregate_request import SpansAggregateRequest
from datadog_api_client.v2.model.spans_group_by import SpansGroupBy
from datadog_api_client.v2.model.spans_compute import SpansCompute
from datadog_api_client.v2.model.spans_aggregate_sort import SpansAggregateSort
from datadog_api_client.v2.model.spans_aggregation_function import SpansAggregationFunction
from pydantic import Field

from ddmcp.client import get_api_client
from ddmcp.config import DDMCPConfig
from ddmcp.domains.apm.formatting import (
    format_aggregation_response,
    format_span_detail,
    format_spans_response,
)


def search_spans(
    config: DDMCPConfig,
    query: Annotated[
        str,
        Field(
            description="Datadog search query using DD syntax (e.g., 'service:web-store env:prod status:error')"
        ),
    ] = "",
    time_from: Annotated[
        str,
        Field(
            description="Start time - relative (e.g., 'now-1h', 'now-15m') or ISO8601 timestamp"
        ),
    ] = "now-1h",
    time_to: Annotated[
        str,
        Field(
            description="End time - relative (e.g., 'now') or ISO8601 timestamp"
        ),
    ] = "now",
    limit: Annotated[
        int,
        Field(
            description="Maximum number of spans to return",
            ge=1,
            le=50,
        ),
    ] = 25,
    sort: Annotated[
        Literal["timestamp_asc", "timestamp_desc"],
        Field(description="Sort order for results"),
    ] = "timestamp_desc",
) -> str:
    """Search for APM spans using Datadog query syntax.

    This tool queries the Datadog APM spans API to find traces matching your search criteria.
    Use DD query syntax to filter by service, environment, status, tags, and more.

    Args:
        config: DDMCPConfig instance
        query: Search query in Datadog syntax
        time_from: Start of time range
        time_to: End of time range
        limit: Max results to return (1-50)
        sort: Sort order by timestamp

    Returns:
        Formatted markdown string with span results
    """
    with get_api_client(config) as api_client:
        api = SpansApi(api_client)

        # Build the request in JSON:API format
        request_body = {
            "data": {
                "type": "search_request",
                "attributes": {
                    "filter": {
                        "query": query,
                        "from": time_from,
                        "to": time_to,
                    },
                    "sort": "timestamp" if sort == "timestamp_asc" else "-timestamp",
                    "page": {
                        "limit": limit,
                    },
                }
            }
        }

        # Execute the search
        response = api.list_spans(body=request_body)

        # Extract spans and metadata from model object
        spans = response.data if hasattr(response, 'data') else []
        meta = response.meta if hasattr(response, 'meta') else None
        total_count = None
        if meta and hasattr(meta, 'page') and meta.page:
            total_count = meta.page.total_count if hasattr(meta.page, 'total_count') else None

        return format_spans_response(spans, total_count)


def get_slow_endpoints(
    config: DDMCPConfig,
    service: Annotated[
        str,
        Field(description="Service name to search for slow endpoints"),
    ],
    min_duration_ms: Annotated[
        int,
        Field(
            description="Minimum duration threshold in milliseconds",
            ge=1,
        ),
    ] = 1000,
    env: Annotated[
        str | None,
        Field(description="Environment filter (e.g., 'prod', 'staging')"),
    ] = None,
    time_from: Annotated[
        str,
        Field(
            description="Start time - relative (e.g., 'now-1h') or ISO8601"
        ),
    ] = "now-1h",
    time_to: Annotated[
        str,
        Field(description="End time - relative (e.g., 'now') or ISO8601"),
    ] = "now",
    limit: Annotated[
        int,
        Field(description="Maximum number of spans to return", ge=1, le=50),
    ] = 25,
) -> str:
    """Find slow endpoints exceeding a duration threshold.

    This tool searches for spans from a specific service where the duration exceeds
    a given threshold. Useful for identifying performance bottlenecks.

    Args:
        config: DDMCPConfig instance
        service: Service name to query
        min_duration_ms: Minimum duration in milliseconds
        env: Optional environment filter
        time_from: Start of time range
        time_to: End of time range
        limit: Max results to return (1-50)

    Returns:
        Formatted markdown string with slow endpoint results
    """
    # Convert milliseconds to nanoseconds for the query
    min_duration_ns = min_duration_ms * 1_000_000

    # Build query parts
    query_parts = [f"service:{service}", f"@duration:>={min_duration_ns}"]

    if env:
        query_parts.append(f"env:{env}")

    query = " ".join(query_parts)

    with get_api_client(config) as api_client:
        api = SpansApi(api_client)

        # Build request in JSON:API format
        request_body = {
            "data": {
                "type": "search_request",
                "attributes": {
                    "filter": {
                        "query": query,
                        "from": time_from,
                        "to": time_to,
                    },
                    "sort": "-timestamp",  # Descending by default for slow queries
                    "page": {
                        "limit": limit,
                    },
                }
            }
        }

        response = api.list_spans(body=request_body)

        # Extract spans and metadata from model object
        spans = response.data if hasattr(response, 'data') else []
        meta = response.meta if hasattr(response, 'meta') else None
        total_count = None
        if meta and hasattr(meta, 'page') and meta.page:
            total_count = meta.page.total_count if hasattr(meta.page, 'total_count') else None

        return format_spans_response(spans, total_count)


def aggregate_spans(
    config: DDMCPConfig,
    query: Annotated[
        str,
        Field(
            description="Datadog search query to filter spans for aggregation"
        ),
    ] = "",
    group_by: Annotated[
        str,
        Field(
            description="Field to group results by (e.g., 'resource_name', 'service', '@http.status_code')"
        ),
    ] = "resource_name",
    compute_metric: Annotated[
        Literal["count", "avg_duration", "p50_duration", "p75_duration", "p90_duration", "p95_duration", "p99_duration"],
        Field(description="Metric to compute for each group"),
    ] = "p95_duration",
    time_from: Annotated[
        str,
        Field(description="Start time - relative or ISO8601"),
    ] = "now-1h",
    time_to: Annotated[
        str,
        Field(description="End time - relative or ISO8601"),
    ] = "now",
    limit: Annotated[
        int,
        Field(description="Maximum number of groups to return", ge=1, le=50),
    ] = 25,
) -> str:
    """Aggregate spans by field with count and duration percentiles.

    This tool groups spans by a specified field and computes statistics like
    count, average duration, or duration percentiles for each group.

    Args:
        config: DDMCPConfig instance
        query: Search query to filter spans
        group_by: Field to group by
        compute_metric: Metric to compute (count or duration percentiles)
        time_from: Start of time range
        time_to: End of time range
        limit: Max groups to return (1-50)

    Returns:
        Formatted markdown string with aggregation results
    """
    with get_api_client(config) as api_client:
        api = SpansApi(api_client)

        # Build filter
        filter_dict = {
            "query": query,
            "from": time_from,
            "to": time_to,
        }

        # Configure group by
        group_by_dict = {
            "facet": group_by,
            "limit": limit,
        }

        # Configure compute based on metric
        compute_list = []
        if compute_metric == "count":
            # For count, we just use group_by without compute
            pass
        elif compute_metric == "avg_duration":
            compute_list.append({
                "aggregation": "avg",
                "metric": "@duration",
                "type": "total",
            })
        else:
            # Percentile metrics
            percentile_map = {
                "p50_duration": "50",
                "p75_duration": "75",
                "p90_duration": "90",
                "p95_duration": "95",
                "p99_duration": "99",
            }
            compute_list.append({
                "aggregation": "percentile",
                "metric": "@duration",
                "type": "total",
                "interval": percentile_map[compute_metric],
            })

        # Build request in JSON:API format
        request_body = {
            "data": {
                "type": "aggregate_request",
                "attributes": {
                    "filter": filter_dict,
                    "group_by": [group_by_dict],
                    "compute": compute_list,
                }
            }
        }

        # Execute aggregation
        response = api.aggregate_spans(body=request_body)

        # Extract buckets from model object
        # response.data is a list of buckets directly
        buckets = response.data if hasattr(response, 'data') else []

        return format_aggregation_response(buckets, group_by)


def get_span_by_id(
    config: DDMCPConfig,
    span_id: Annotated[
        str,
        Field(description="Span ID to retrieve"),
    ],
    time_from: Annotated[
        str,
        Field(description="Start time window - relative or ISO8601"),
    ] = "now-24h",
    time_to: Annotated[
        str,
        Field(description="End time window - relative or ISO8601"),
    ] = "now",
) -> str:
    """Get full details of a specific span by ID.

    This tool retrieves detailed information about a single span, including
    all attributes, tags, and error details if present.

    Args:
        config: DDMCPConfig instance
        span_id: The span ID to retrieve
        time_from: Start of time window to search
        time_to: End of time window to search

    Returns:
        Formatted markdown string with full span details
    """
    with get_api_client(config) as api_client:
        api = SpansApi(api_client)

        # Query for the specific span ID
        query = f"@span_id:{span_id}"

        # Build request in JSON:API format
        request_body = {
            "data": {
                "type": "search_request",
                "attributes": {
                    "filter": {
                        "query": query,
                        "from": time_from,
                        "to": time_to,
                    },
                    "page": {
                        "limit": 1,
                    },
                }
            }
        }

        response = api.list_spans(body=request_body)

        # Extract spans from model object
        spans = response.data if hasattr(response, 'data') else []

        if not spans:
            return f"No span found with ID: {span_id}\n\nTry expanding the time window or verify the span ID."

        return format_span_detail(spans[0])
