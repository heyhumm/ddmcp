# Plan: ddmcp - Datadog MCP Server

## Context

We're building an open-source, community-extensible MCP server for Datadog using FastMCP (Python) and the official `datadog-api-client` SDK. The first milestone is APM trace search - finding slow endpoints, querying spans, analyzing service performance. The server should be structured so community contributors can easily add new domain modules (logs, monitors, dashboards, etc.).

**Key gaps in existing DD MCP servers**: No existing server (shelfio/datadog-mcp, GeLi2001/datadog-mcp-server, or Datadog's official Bits AI MCP) provides APM span search, slow endpoint detection, or trace analytics. This is our differentiator.

**Scope**: The Datadog API has 732 endpoints across 87 categories (confirmed via Postman collection). We start with APM (3 Spans endpoints + 4 Service Definition endpoints) and the architecture makes it straightforward to add more domains over time.

---

## Architecture

### Project Structure

```
src/ddmcp/
├── __init__.py                  # Package version
├── server.py                    # Main FastMCP server, mounts domain sub-servers
├── config.py                    # DDMCPConfig from env vars (DD_API_KEY, DD_APP_KEY, DD_SITE)
├── client.py                    # Datadog ApiClient factory (context manager)
├── formatting.py                # Shared formatting helpers (duration, truncation)
└── domains/
    ├── __init__.py              # Domain registry - returns list of (namespace, server) tuples
    └── apm/
        ├── __init__.py          # create_server(config) -> FastMCP sub-server
        ├── spans.py             # Span search/query tools
        ├── services.py          # Service catalog tools
        └── formatting.py        # APM-specific output formatters
tests/
├── conftest.py                  # Shared fixtures (mock config, mock API client)
├── test_server.py               # Server composition + tool schema tests
└── domains/apm/
    ├── test_spans.py
    ├── test_services.py
    └── test_formatting.py
pyproject.toml                   # hatchling build, deps, `ddmcp` CLI entry point
```

### Core Design Decisions

1. **FastMCP `mount()` with namespaces**: Each domain is a FastMCP sub-server mounted with a namespace prefix. APM tools get `apm_` prefix automatically (e.g., `search_spans` -> `apm_search_spans`).

2. **Official SDK (`datadog-api-client`)**: All API calls go through the typed SDK - no raw HTTP. Auth reads `DD_API_KEY`/`DD_APP_KEY` env vars automatically.

3. **Markdown output**: Tools return formatted markdown strings (not raw JSON). LLMs work better with pre-formatted output, and it keeps response sizes bounded.

4. **Sync tools**: The DD SDK is synchronous. FastMCP auto-runs sync tools in a threadpool, so no async wrapper needed.

5. **Tool discovery ready**: All tools get `tags` for grouping and descriptive names under 32 chars. Designed for Anthropic's `defer_loading` / tool search pattern as tool count grows.

---

## Implementation Steps

### Step 1: Project scaffolding
- **`pyproject.toml`**: hatchling build, deps (`fastmcp>=2.14`, `datadog-api-client>=2.50.0`), `ddmcp` CLI entry point, dev deps (pytest, ruff, mypy)
- **`src/ddmcp/__init__.py`**: version string

### Step 2: Core infrastructure
- **`config.py`**: `DDMCPConfig` dataclass loaded from env vars. Supports DD_SITE short codes (us1, eu, ap1, gov) mapped to full URLs. Fails fast with clear error if keys missing.
- **`client.py`**: `get_api_client(config)` context manager yielding a configured `ApiClient`. Short-lived per tool call.
- **`formatting.py`**: `format_duration(ns)` helper, generic truncation utilities.

### Step 3: Domain registry
- **`domains/__init__.py`**: `get_domain_servers(config)` returns `list[tuple[str, FastMCP]]`. Explicit registration (not auto-discovery) - one import line per domain.

### Step 4: APM domain - spans tools
- **`domains/apm/__init__.py`**: `create_server(config)` creates sub-server, registers span + service tools.
- **`domains/apm/spans.py`**: 4 tools:

| Tool (namespaced) | Purpose | DD API Endpoint |
|---|---|---|
| `apm_search_spans` | Search spans with DD query syntax (service:x env:y) | `POST /api/v2/spans/events/search` |
| `apm_get_slow_endpoints` | Find endpoints exceeding a duration threshold | `POST /api/v2/spans/events/search` with duration filter |
| `apm_aggregate_spans` | Group spans by field, compute count/duration percentiles | `POST /api/v2/spans/analytics/aggregate` |
| `apm_get_span_by_id` | Get full details of a specific span | `GET /api/v2/spans/events` with span_id filter |

- **`domains/apm/formatting.py`**: `format_spans_response()`, `format_aggregation_response()`, `_format_duration()`

### Step 5: APM domain - service tools
- **`domains/apm/services.py`**: 3 tools:

| Tool (namespaced) | Purpose | DD API Endpoint |
|---|---|---|
| `apm_list_services` | List services from service catalog | `GET /api/v2/services/definitions` |
| `apm_get_service` | Get a single service definition with metadata | `GET /api/v2/services/definitions/:service_name` |
| `apm_get_service_stats` | Request rate, error rate, latency percentiles for a service | `POST /api/v2/spans/analytics/aggregate` (composed) |

### Step 6: Server composition
- **`server.py`**: `create_server()` validates config, creates main FastMCP, mounts domain sub-servers. `main()` is the CLI entry point.

### Step 7: Tests
- Mock-based unit tests for each tool (mock `ApiClient` at boundary)
- Pure unit tests for formatters
- Integration test: server creates correctly, all tools registered with correct names/schemas
- Optional live tests gated by `DDMCP_LIVE_TESTS=1` env var

### Step 8: README + docs
- Update README with installation, quickstart, Claude Desktop config example
- Document the domain module pattern for contributors

---

## Tool Parameter Conventions

All tools follow these patterns:
- **`query`**: DD search syntax (`service:web-store env:prod status:error`)
- **`time_from` / `time_to`**: Relative (`now-1h`, `now-15m`) or ISO8601 timestamps. Default: `now-1h` / `now`
- **`limit`**: Max results, default 25, max 50
- **`sort`**: `timestamp_asc` or `timestamp_desc`
- All params use `Annotated[type, Field(description=...)]` for rich schemas

---

## Configuration

| Env Var | Required | Default | Notes |
|---|---|---|---|
| `DD_API_KEY` | Yes | - | Datadog API key |
| `DD_APP_KEY` | Yes | - | Datadog Application key |
| `DD_SITE` | No | `us1` | Short code or full URL |
| `DDMCP_MAX_RESULTS` | No | `50` | Default page size cap |

Claude Desktop config:
```json
{
  "mcpServers": {
    "ddmcp": {
      "command": "uvx",
      "args": ["ddmcp"],
      "env": {
        "DD_API_KEY": "your-api-key",
        "DD_APP_KEY": "your-app-key",
        "DD_SITE": "us1"
      }
    }
  }
}
```

---

## Community Extensibility Pattern

Adding a new domain (e.g., `logs`) requires:
1. Create `src/ddmcp/domains/logs/` with `__init__.py` + tool modules
2. Implement `create_server(config) -> FastMCP` following the template
3. Add one line to `domains/__init__.py` to register it
4. Add tests in `tests/domains/logs/`

No core files need modification beyond the single registration line.

---

## Verification

1. `uv sync` installs cleanly
2. `pytest` passes (all mock-based tests)
3. `ddmcp` starts without error (with valid DD keys)
4. In Claude Desktop: `apm_search_spans` with query `service:<a-real-service> env:prod` returns formatted span results
5. `apm_get_slow_endpoints` with a service name surfaces high-latency requests
6. `ruff check src/ tests/` passes clean
