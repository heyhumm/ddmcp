"""APM service catalog and statistics tools."""

from typing import Annotated

from datadog_api_client.v2.api.service_definition_api import ServiceDefinitionApi
from datadog_api_client.v2.api.spans_api import SpansApi
from pydantic import Field

from ddmcp.client import get_api_client
from ddmcp.config import DDMCPConfig
from ddmcp.formatting import format_duration, format_number, format_percentage


def list_services(
    config: DDMCPConfig,
    page_size: Annotated[
        int,
        Field(
            description="Number of services per page (max 100)",
            ge=1,
            le=100,
        ),
    ] = 25,
    page_number: Annotated[
        int,
        Field(
            description="Page number to retrieve (0-indexed)",
            ge=0,
        ),
    ] = 0,
) -> str:
    """List services from the APM service catalog.

    Returns a paginated list of services with basic metadata from the
    service definition catalog. Use this to discover available services
    in your Datadog APM environment.

    Args:
        config: DDMCPConfig instance
        page_size: Number of services to return per page (default: 25, max: 100)
        page_number: Which page to retrieve, 0-indexed (default: 0)

    Returns:
        Formatted markdown string with service list
    """
    with get_api_client(config) as api_client:
        api = ServiceDefinitionApi(api_client)

        try:
            response = api.list_service_definitions(
                page_size=page_size,
                page_number=page_number,
            )

            if not response.data:
                return "No services found in the service catalog."

            # Build markdown output
            lines = [
                f"# APM Services (Page {page_number + 1})",
                f"",
                f"Showing {len(response.data)} services:",
                f"",
            ]

            for service_def in response.data:
                service_name = service_def.attributes.meta.get("service-name", "unknown")
                schema_version = service_def.attributes.schema_version or "unknown"

                lines.append(f"## {service_name}")
                lines.append(f"- **Schema Version**: {schema_version}")

                # Add team/contacts if available
                if hasattr(service_def.attributes, "contact") and service_def.attributes.contact:
                    contact = service_def.attributes.contact
                    if hasattr(contact, "email") and contact.email:
                        lines.append(f"- **Contact**: {contact.email}")

                # Add tier if available
                if hasattr(service_def.attributes, "tier") and service_def.attributes.tier:
                    lines.append(f"- **Tier**: {service_def.attributes.tier}")

                lines.append("")

            # Add pagination info if there might be more pages
            if len(response.data) == page_size:
                lines.append(
                    f"*Tip: There may be more services. "
                    f"Use page_number={page_number + 1} to see the next page.*"
                )

            return "\n".join(lines)

        except Exception as e:
            return f"Error listing services: {str(e)}"


def get_service(
    config: DDMCPConfig,
    service_name: Annotated[
        str,
        Field(description="Name of the service to retrieve"),
    ],
    schema_version: Annotated[
        str,
        Field(description="Schema version of the service definition (e.g., 'v2.2')"),
    ] = "v2.2",
) -> str:
    """Get detailed definition and metadata for a specific service.

    Retrieves the full service definition including description, team ownership,
    links, tier, and other metadata from the service catalog.

    Args:
        config: DDMCPConfig instance
        service_name: Name of the service to retrieve
        schema_version: Schema version of the service definition (default: "v2.2")

    Returns:
        Formatted markdown string with service details
    """
    with get_api_client(config) as api_client:
        api = ServiceDefinitionApi(api_client)

        try:
            response = api.get_service_definition(
                service_name=service_name,
                schema_version=schema_version,
            )

            if not response.data:
                return f"Service '{service_name}' not found."

            service = response.data
            attrs = service.attributes

            # Build markdown output
            lines = [
                f"# Service: {service_name}",
                f"",
            ]

            # Description
            if hasattr(attrs, "description") and attrs.description:
                lines.append(f"**Description**: {attrs.description}")
                lines.append("")

            # Metadata section
            lines.append("## Metadata")
            lines.append(f"- **Schema Version**: {attrs.schema_version or 'unknown'}")

            if hasattr(attrs, "tier") and attrs.tier:
                lines.append(f"- **Tier**: {attrs.tier}")

            if hasattr(attrs, "lifecycle") and attrs.lifecycle:
                lines.append(f"- **Lifecycle**: {attrs.lifecycle}")

            if hasattr(attrs, "application") and attrs.application:
                lines.append(f"- **Application**: {attrs.application}")

            lines.append("")

            # Contact information
            if hasattr(attrs, "contact") and attrs.contact:
                contact = attrs.contact
                lines.append("## Contact")
                if hasattr(contact, "email") and contact.email:
                    lines.append(f"- **Email**: {contact.email}")
                if hasattr(contact, "slack") and contact.slack:
                    lines.append(f"- **Slack**: {contact.slack}")
                lines.append("")

            # Team
            if hasattr(attrs, "team") and attrs.team:
                lines.append(f"**Team**: {attrs.team}")
                lines.append("")

            # Links
            if hasattr(attrs, "links") and attrs.links:
                lines.append("## Links")
                for link in attrs.links:
                    link_name = link.get("name", "Link")
                    link_url = link.get("url", "")
                    link_type = link.get("type", "")
                    if link_url:
                        lines.append(f"- **{link_name}** ({link_type}): {link_url}")
                lines.append("")

            # Tags
            if hasattr(attrs, "tags") and attrs.tags:
                lines.append("## Tags")
                lines.append(", ".join(attrs.tags))
                lines.append("")

            return "\n".join(lines)

        except Exception as e:
            return f"Error retrieving service '{service_name}': {str(e)}"


def get_service_stats(
    config: DDMCPConfig,
    service_name: Annotated[
        str,
        Field(description="Name of the service to analyze"),
    ],
    env: Annotated[
        str | None,
        Field(description="Environment to filter by (e.g., 'prod', 'staging')"),
    ] = None,
    time_from: Annotated[
        str,
        Field(
            description="Start time (relative like 'now-1h' or ISO8601 timestamp)",
        ),
    ] = "now-1h",
    time_to: Annotated[
        str,
        Field(
            description="End time (relative like 'now' or ISO8601 timestamp)",
        ),
    ] = "now",
) -> str:
    """Get request rate, error rate, and latency statistics for a service.

    Aggregates span data to compute key performance metrics:
    - Request count and rate
    - Error count and error rate percentage
    - Latency percentiles (p50, p75, p95, p99)

    Args:
        config: DDMCPConfig instance
        service_name: Name of the service to analyze
        env: Optional environment filter (e.g., 'prod', 'staging')
        time_from: Start time (default: "now-1h")
        time_to: End time (default: "now")

    Returns:
        Formatted markdown string with service statistics
    """
    with get_api_client(config) as api_client:
        api = SpansApi(api_client)

        # Build query filter
        query_parts = [f"service:{service_name}"]
        if env:
            query_parts.append(f"env:{env}")
        query = " ".join(query_parts)

        try:
            # Request 1: Get request count and error count
            count_request = {
                "filter": {
                    "query": query,
                    "from": time_from,
                    "to": time_to,
                },
                "group_by": [
                    {
                        "facet": "status",
                    },
                ],
            }

            count_response = api.aggregate_spans(body=count_request)

            # Request 2: Get latency percentiles
            latency_request = {
                "filter": {
                    "query": query,
                    "from": time_from,
                    "to": time_to,
                },
                "compute": [
                    {
                        "aggregation": "percentile",
                        "metric": "@duration",
                        "type": "total",
                        "interval": "50",
                    },
                    {
                        "aggregation": "percentile",
                        "metric": "@duration",
                        "type": "total",
                        "interval": "75",
                    },
                    {
                        "aggregation": "percentile",
                        "metric": "@duration",
                        "type": "total",
                        "interval": "95",
                    },
                    {
                        "aggregation": "percentile",
                        "metric": "@duration",
                        "type": "total",
                        "interval": "99",
                    },
                ],
            }

            latency_response = api.aggregate_spans(body=latency_request)

            # Parse count response
            total_requests = 0
            error_requests = 0

            if count_response.data and count_response.data.buckets:
                for bucket in count_response.data.buckets:
                    status = bucket.by.get("status", "")
                    count_value = bucket.computes.get("c0", 0)

                    total_requests += count_value
                    if status == "error":
                        error_requests += count_value

            # Calculate error rate
            error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0.0

            # Parse latency response
            p50 = p75 = p95 = p99 = None
            if latency_response.data and latency_response.data.buckets:
                bucket = latency_response.data.buckets[0]
                p50 = bucket.computes.get("c0")
                p75 = bucket.computes.get("c1")
                p95 = bucket.computes.get("c2")
                p99 = bucket.computes.get("c3")

            # Build markdown output
            lines = [
                f"# Service Statistics: {service_name}",
                f"",
            ]

            if env:
                lines.append(f"**Environment**: {env}")
            lines.append(f"**Time Range**: {time_from} to {time_to}")
            lines.append("")

            # Request metrics
            lines.append("## Request Metrics")
            lines.append(f"- **Total Requests**: {format_number(total_requests)}")
            lines.append(f"- **Error Requests**: {format_number(error_requests)}")
            lines.append(f"- **Error Rate**: {format_percentage(error_rate / 100)}")
            lines.append("")

            # Latency metrics
            if p50 is not None:
                lines.append("## Latency Percentiles")
                lines.append(f"- **p50**: {format_duration(int(p50))}")
                if p75 is not None:
                    lines.append(f"- **p75**: {format_duration(int(p75))}")
                if p95 is not None:
                    lines.append(f"- **p95**: {format_duration(int(p95))}")
                if p99 is not None:
                    lines.append(f"- **p99**: {format_duration(int(p99))}")
                lines.append("")

            if total_requests == 0:
                lines.append("*No requests found for this service in the specified time range.*")

            return "\n".join(lines)

        except Exception as e:
            return f"Error retrieving stats for service '{service_name}': {str(e)}"
