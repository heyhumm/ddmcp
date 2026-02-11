"""APM-specific output formatting utilities."""

from typing import Any

from ddmcp.formatting import format_duration, truncate_text


def format_spans_response(spans: list[Any], total_count: int | None = None) -> str:
    """Format a list of spans into a markdown table.

    Args:
        spans: List of span objects from the Datadog API
        total_count: Optional total count of matching spans (for pagination info)

    Returns:
        Formatted markdown string with span table
    """
    if not spans:
        return "No spans found matching the query."

    lines = [
        "# Span Search Results",
        "",
    ]

    if total_count is not None:
        lines.append(f"Showing {len(spans)} of {total_count:,} total spans")
        lines.append("")

    lines.extend([
        "| Timestamp | Service | Resource | Duration | Status |",
        "|-----------|---------|----------|----------|--------|",
    ])

    for span in spans:
        attrs = span.attributes

        # Extract key fields from model object or dict
        if hasattr(attrs, 'custom'):
            # New model-based format
            custom = attrs.custom if isinstance(attrs.custom, dict) else (attrs.custom.to_dict() if hasattr(attrs.custom, 'to_dict') else {})
            timestamp = str(attrs.start_timestamp)[:19] if hasattr(attrs, 'start_timestamp') else "N/A"
            service = custom.get("service") or attrs.service if hasattr(attrs, 'service') else "N/A"
            resource = truncate_text(attrs.resource_name if hasattr(attrs, 'resource_name') else "N/A", 40)
            duration_ns = custom.get("duration", 0)
            duration = format_duration(duration_ns) if duration_ns else "N/A"
            status = attrs.status if hasattr(attrs, 'status') else "N/A"
        else:
            # Legacy dict format
            timestamp = attrs.get("start", "")[:19] if attrs.get("start") else "N/A"
            service = attrs.get("service", "N/A")
            resource = truncate_text(attrs.get("resource", "N/A"), 40)
            duration_ns = attrs.get("duration", 0)
            duration = format_duration(duration_ns) if duration_ns else "N/A"
            status = attrs.get("status", "N/A")

        lines.append(f"| {timestamp} | {service} | {resource} | {duration} | {status} |")

    lines.append("")
    return "\n".join(lines)


def format_aggregation_response(buckets: list[Any], group_by: str | None = None) -> str:
    """Format span aggregation results into a markdown table.

    Args:
        buckets: List of aggregation buckets from the Datadog API
        group_by: Optional field name used for grouping

    Returns:
        Formatted markdown string with aggregation table
    """
    if not buckets:
        return "No aggregation results found."

    lines = [
        "# Span Aggregation Results",
        "",
    ]

    # Determine columns based on first bucket
    first_bucket = buckets[0]
    compute_keys = list(first_bucket.computes.keys()) if hasattr(first_bucket, "computes") else []

    # Build table header
    headers = []
    if group_by:
        headers.append(group_by.title())

    for idx, key in enumerate(compute_keys):
        headers.append(f"Metric {idx + 1}")

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")

    # Build table rows
    for bucket in buckets:
        row = []

        # Add group by value if present
        if group_by and hasattr(bucket, "by"):
            group_value = bucket.by.get(group_by, "N/A")
            row.append(str(group_value))

        # Add computed values
        if hasattr(bucket, "computes"):
            for key in compute_keys:
                value = bucket.computes.get(key, 0)
                # Format durations if the value looks like nanoseconds
                if isinstance(value, (int, float)) and value > 1_000_000:
                    formatted = format_duration(int(value))
                else:
                    formatted = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
                row.append(formatted)

        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    return "\n".join(lines)


def format_span_detail(span: Any) -> str:
    """Format detailed information about a single span.

    Args:
        span: Span object from the Datadog API

    Returns:
        Formatted markdown string with full span details
    """
    attrs = span.attributes

    lines = [
        "# Span Details",
        "",
    ]

    # Basic information
    span_id = attrs.attributes.get("span_id", "N/A")
    trace_id = attrs.attributes.get("trace_id", "N/A")
    service = attrs.attributes.get("service", "N/A")
    resource = attrs.attributes.get("resource", "N/A")
    operation_name = attrs.attributes.get("operation_name", "N/A")

    lines.append(f"**Span ID**: `{span_id}`")
    lines.append(f"**Trace ID**: `{trace_id}`")
    lines.append(f"**Service**: {service}")
    lines.append(f"**Resource**: {resource}")
    lines.append(f"**Operation**: {operation_name}")
    lines.append("")

    # Timing information
    start = attrs.attributes.get("start", "")
    duration_ns = attrs.attributes.get("duration", 0)
    lines.append("## Timing")
    lines.append(f"- **Start**: {start}")
    lines.append(f"- **Duration**: {format_duration(duration_ns) if duration_ns else 'N/A'}")
    lines.append("")

    # Status
    status = attrs.attributes.get("status", "N/A")
    lines.append(f"**Status**: {status}")
    lines.append("")

    # Error information if present
    if attrs.attributes.get("error"):
        lines.append("## Error Details")
        error_type = attrs.attributes.get("error.type", "N/A")
        error_msg = attrs.attributes.get("error.message", "N/A")
        error_stack = attrs.attributes.get("error.stack", "N/A")

        lines.append(f"- **Type**: {error_type}")
        lines.append(f"- **Message**: {error_msg}")
        if error_stack != "N/A":
            lines.append(f"- **Stack Trace**: ```\n{error_stack}\n```")
        lines.append("")

    # Tags
    tags = attrs.attributes.get("tags", [])
    if tags:
        lines.append("## Tags")
        for tag in tags:
            lines.append(f"- {tag}")
        lines.append("")

    # Custom attributes
    custom_attrs = {k: v for k, v in attrs.attributes.items()
                    if k.startswith("@") and k != "@duration"}
    if custom_attrs:
        lines.append("## Custom Attributes")
        for key, value in sorted(custom_attrs.items()):
            lines.append(f"- **{key}**: {value}")
        lines.append("")

    return "\n".join(lines)


def _format_duration(nanoseconds: int) -> str:
    """Format duration from nanoseconds.

    This is an alias to the shared format_duration for backwards compatibility.

    Args:
        nanoseconds: Duration in nanoseconds

    Returns:
        Formatted duration string
    """
    return format_duration(nanoseconds)
