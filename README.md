# ddmcp

**Community-extensible MCP server for Datadog** - bringing APM, observability, and analytics to your AI workflows.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

`ddmcp` is an open-source Model Context Protocol (MCP) server that connects Claude and other AI assistants to your Datadog environment. Built with [FastMCP](https://github.com/jlowin/fastmcp) and the official Datadog API client, it enables natural language queries for APM traces, service performance analysis, and more.

**Key differentiator**: Unlike existing Datadog MCP servers, `ddmcp` provides **APM span search**, **slow endpoint detection**, and **trace analytics** - essential capabilities for debugging production issues and analyzing service performance.

### Features

- **APM Span Search**: Query traces with Datadog syntax, filter by service, environment, status, and tags
- **Performance Analysis**: Find slow endpoints, aggregate latency percentiles, identify bottlenecks
- **Service Catalog**: Browse services, view definitions, analyze request rates and error rates
- **Extensible Architecture**: Community-friendly domain pattern for adding logs, monitors, dashboards, and more
- **Type-Safe**: Built on the official `datadog-api-client` SDK with full type hints
- **Well-Tested**: 96% code coverage with comprehensive unit and integration tests

## Installation

### Quick Start with uvx (Recommended)

The fastest way to run `ddmcp` is with `uvx`, which handles installation automatically:

```bash
uvx ddmcp
```

### Install with uv

```bash
uv pip install ddmcp
```

### Install with pip

```bash
pip install ddmcp
```

### Install from Source

```bash
git clone https://github.com/yourusername/ddmcp.git
cd ddmcp
uv sync
```

## Configuration

`ddmcp` requires Datadog API credentials and optionally accepts a site configuration.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DD_API_KEY` | **Yes** | - | Your Datadog API key ([get one here](https://app.datadoghq.com/organization-settings/api-keys)) |
| `DD_APP_KEY` | **Yes** | - | Your Datadog Application key ([get one here](https://app.datadoghq.com/organization-settings/application-keys)) |
| `DD_SITE` | No | `us1` | Datadog site - use short code (`us1`, `us3`, `us5`, `eu`, `ap1`, `gov`) or full URL |
| `DDMCP_MAX_RESULTS` | No | `50` | Default page size cap for queries |

### Claude Desktop Configuration

Add `ddmcp` to your Claude Desktop config file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ddmcp": {
      "command": "uvx",
      "args": ["ddmcp"],
      "env": {
        "DD_API_KEY": "your-api-key-here",
        "DD_APP_KEY": "your-app-key-here",
        "DD_SITE": "us1"
      }
    }
  }
}
```

**For EU users**, change `DD_SITE` to `"eu"`. **For Gov Cloud**, use `"gov"`.

After updating the config, restart Claude Desktop. The tools will be available with the `apm_` prefix.

## Tools Reference

All tools use the `apm_` namespace prefix and return formatted markdown output optimized for LLM consumption.

### Span Search Tools

#### `apm_search_spans`

Search for APM spans using Datadog query syntax.

**Parameters:**
- `query` (string): Datadog search query (e.g., `"service:web-store env:prod status:error"`)
- `time_from` (string, default: `"now-1h"`): Start time - relative (e.g., `"now-1h"`, `"now-15m"`) or ISO8601 timestamp
- `time_to` (string, default: `"now"`): End time - relative or ISO8601 timestamp
- `limit` (int, default: 25, max: 50): Maximum number of spans to return
- `sort` (string, default: `"timestamp_desc"`): Sort order - `"timestamp_asc"` or `"timestamp_desc"`

**Example queries:**
```
service:api-gateway env:prod
service:checkout-service @http.status_code:500
service:user-service env:staging status:error
```

**Returns:** Formatted list of matching spans with service, resource, status, duration, and timestamp.

---

#### `apm_get_slow_endpoints`

Find endpoints exceeding a duration threshold - perfect for identifying performance bottlenecks.

**Parameters:**
- `service` (string, **required**): Service name to search
- `min_duration_ms` (int, default: 1000): Minimum duration threshold in milliseconds
- `env` (string, optional): Environment filter (e.g., `"prod"`, `"staging"`)
- `time_from` (string, default: `"now-1h"`): Start time
- `time_to` (string, default: `"now"`): End time
- `limit` (int, default: 25, max: 50): Maximum number of spans to return

**Example:**
```
Find slow endpoints in the checkout service over the last hour:
service: "checkout-service"
min_duration_ms: 2000
env: "prod"
```

**Returns:** List of slow spans sorted by duration (descending).

---

#### `apm_aggregate_spans`

Group spans by field and compute statistics like count, average duration, or percentiles.

**Parameters:**
- `query` (string): Datadog search query to filter spans
- `group_by` (string, default: `"resource_name"`): Field to group by (e.g., `"resource_name"`, `"service"`, `"@http.status_code"`)
- `compute_metric` (string, default: `"p95_duration"`): Metric to compute - one of:
  - `"count"`: Number of spans per group
  - `"avg_duration"`: Average duration
  - `"p50_duration"`, `"p75_duration"`, `"p90_duration"`, `"p95_duration"`, `"p99_duration"`: Duration percentiles
- `time_from` (string, default: `"now-1h"`): Start time
- `time_to` (string, default: `"now"`): End time
- `limit` (int, default: 25, max: 50): Maximum number of groups to return

**Example:**
```
Group checkout service endpoints by resource and compute p95 latency:
query: "service:checkout-service env:prod"
group_by: "resource_name"
compute_metric: "p95_duration"
```

**Returns:** Aggregated results grouped by the specified field with computed metrics.

---

#### `apm_get_span_by_id`

Retrieve full details of a specific span by ID.

**Parameters:**
- `span_id` (string, **required**): Span ID to retrieve
- `time_from` (string, default: `"now-24h"`): Start of time window to search
- `time_to` (string, default: `"now"`): End of time window to search

**Returns:** Full span details including all attributes, tags, and error information if present.

---

### Service Catalog Tools

#### `apm_list_services`

List services from the APM service catalog with pagination.

**Parameters:**
- `page_size` (int, default: 25, max: 100): Number of services per page
- `page_number` (int, default: 0): Page number (0-indexed)

**Returns:** List of services with schema version, contact info, tier, and other metadata.

---

#### `apm_get_service`

Get detailed definition and metadata for a specific service.

**Parameters:**
- `service_name` (string, **required**): Name of the service to retrieve
- `schema_version` (string, default: `"v2.2"`): Schema version of the service definition

**Returns:** Full service definition including description, team ownership, links, tags, tier, lifecycle, and contact information.

---

#### `apm_get_service_stats`

Get request rate, error rate, and latency statistics for a service.

**Parameters:**
- `service_name` (string, **required**): Name of the service to analyze
- `env` (string, optional): Environment to filter by (e.g., `"prod"`, `"staging"`)
- `time_from` (string, default: `"now-1h"`): Start time
- `time_to` (string, default: `"now"`): End time

**Returns:** Service performance metrics including:
- Total request count and error count
- Error rate percentage
- Latency percentiles (p50, p75, p95, p99)

---

## Usage Examples

### Example 1: Find errors in production

```
Show me errors in the checkout service in the last hour
```

Claude will call:
```
apm_search_spans(query="service:checkout-service env:prod status:error", time_from="now-1h")
```

### Example 2: Identify slow endpoints

```
Which endpoints in the api-gateway are taking over 2 seconds?
```

Claude will call:
```
apm_get_slow_endpoints(service="api-gateway", min_duration_ms=2000, env="prod")
```

### Example 3: Analyze service performance

```
What's the p95 latency for each endpoint in the user-service over the last 4 hours?
```

Claude will call:
```
apm_aggregate_spans(
    query="service:user-service env:prod",
    group_by="resource_name",
    compute_metric="p95_duration",
    time_from="now-4h"
)
```

### Example 4: Get service health overview

```
Show me the error rate and latency stats for the checkout-service in production
```

Claude will call:
```
apm_get_service_stats(service_name="checkout-service", env="prod")
```

---

## Architecture & Extensibility

`ddmcp` is designed for easy community contributions. The domain-based architecture makes it straightforward to add new capabilities without modifying core files.

### Project Structure

```
src/ddmcp/
├── __init__.py              # Package version
├── server.py                # Main FastMCP server
├── config.py                # Configuration from env vars
├── client.py                # Datadog API client factory
├── formatting.py            # Shared formatting helpers
└── domains/
    ├── __init__.py          # Domain registry
    └── apm/
        ├── __init__.py      # APM sub-server factory
        ├── spans.py         # Span search tools
        ├── services.py      # Service catalog tools
        └── formatting.py    # APM-specific formatters
```

### Adding a New Domain

Want to add logs, monitors, dashboards, or other Datadog capabilities? Here's how:

#### Step 1: Create the domain directory

```bash
mkdir -p src/ddmcp/domains/logs
touch src/ddmcp/domains/logs/__init__.py
```

#### Step 2: Implement your tools

Create tool files in your domain directory (e.g., `logs.py`, `search.py`):

```python
# src/ddmcp/domains/logs/search.py
from typing import Annotated
from pydantic import Field
from datadog_api_client.v2.api.logs_api import LogsApi
from ddmcp.client import get_api_client
from ddmcp.config import DDMCPConfig

def logs_search(
    config: DDMCPConfig,
    query: Annotated[str, Field(description="Log search query")],
    time_from: str = "now-1h",
    time_to: str = "now",
    limit: int = 25,
) -> str:
    """Search Datadog logs."""
    with get_api_client(config) as api_client:
        api = LogsApi(api_client)
        # ... implement search logic
        return formatted_output
```

#### Step 3: Create the domain sub-server

In `src/ddmcp/domains/logs/__init__.py`:

```python
from fastmcp import FastMCP
from ddmcp.config import DDMCPConfig
from ddmcp.domains.logs import search

def create_server(config: DDMCPConfig) -> FastMCP:
    """Create the Logs sub-server."""
    logs_server = FastMCP("Logs")

    # Register tools (bind config as needed)
    logs_server.tool()(lambda **kwargs: search.logs_search(config, **kwargs))

    return logs_server
```

#### Step 4: Register in the domain registry

Add one line to `src/ddmcp/domains/__init__.py`:

```python
from ddmcp.domains.logs import create_server as create_logs_server

def get_domain_servers(config: DDMCPConfig) -> list[tuple[str, FastMCP]]:
    return [
        ("apm", create_apm_server(config)),
        ("logs", create_logs_server(config)),  # Add this line
    ]
```

That's it! Your `logs_search` tool is now available as `logs_search` (with the `logs_` prefix automatically applied).

### Key Design Principles

1. **FastMCP `mount()` with namespaces**: Each domain is a separate FastMCP sub-server mounted with a namespace prefix (e.g., `apm_`, `logs_`)
2. **Official SDK only**: All API calls use `datadog-api-client` - no raw HTTP requests
3. **Markdown output**: Tools return formatted strings, not raw JSON - better for LLM consumption
4. **Explicit registration**: Domains are registered explicitly in `domains/__init__.py` - no magic imports
5. **Config injection**: Use the `bind_config()` pattern from `domains/apm/__init__.py` to inject configuration

---

## Development

### Setup Development Environment

```bash
git clone https://github.com/yourusername/ddmcp.git
cd ddmcp
uv sync --all-extras
```

### Run Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/domains/apm/test_spans.py

# Run with verbose output
pytest -v

# Run live tests (requires DD_API_KEY and DD_APP_KEY)
DDMCP_LIVE_TESTS=1 pytest
```

### Code Quality

```bash
# Lint and format
ruff check src/ tests/

# Type checking
mypy src/
```

### Project Stats

- **7 APM tools**: 4 span tools + 3 service tools
- **96% code coverage**: 65/65 tests passing
- **Clean linting**: Ruff + mypy compliance
- **Fast**: Synchronous tools with threadpool execution via FastMCP

---

## Roadmap

Current scope covers APM (Application Performance Monitoring). Future domains to add:

- **Logs**: Search, aggregation, live tail
- **Monitors**: List, create, update, mute/unmute
- **Dashboards**: Query, create, update
- **Metrics**: Query metrics, get metric metadata
- **Incidents**: List, create, update incident management
- **SLOs**: Query SLO status and error budgets
- **RUM**: Real User Monitoring queries

The Datadog API has 732 endpoints across 87 categories - plenty of room for community contributions!

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/logs-domain`
3. **Add your domain** following the extensibility pattern above
4. **Write tests** in `tests/domains/your-domain/`
5. **Ensure tests pass**: `pytest` (aim for high coverage)
6. **Lint your code**: `ruff check src/ tests/`
7. **Submit a pull request**

### Contribution Guidelines

- Follow the existing code style (Ruff configuration in `pyproject.toml`)
- Add tests for new functionality (maintain >90% coverage)
- Update README if adding new tools or domains
- Use type hints and docstrings
- Return formatted markdown from tools (not raw JSON)
- Keep tool names under 32 characters
- Add `tags` for tool discovery/grouping

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Credits

Built with:
- [FastMCP](https://github.com/jlowin/fastmcp) - Modern Python MCP server framework
- [datadog-api-client](https://github.com/DataDog/datadog-api-client-python) - Official Datadog API client
- [Model Context Protocol](https://modelcontextprotocol.io/) - Anthropic's protocol for AI-application integration

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ddmcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ddmcp/discussions)
- **Datadog API Docs**: [https://docs.datadoghq.com/api/](https://docs.datadoghq.com/api/)

---

**Happy querying!** If `ddmcp` helps you debug production issues faster, please star the repository and share with others!
