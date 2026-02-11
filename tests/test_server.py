"""Tests for server composition and tool registration."""

import pytest
from unittest.mock import patch

from ddmcp.server import create_server, main


class TestServerCreation:
    """Test server creation and configuration."""

    def test_create_server_loads_config(self, mock_env_vars):
        """Test that create_server loads configuration from environment."""
        server = create_server()

        assert server is not None
        assert server.name == "ddmcp"

    def test_create_server_fails_without_api_key(self, monkeypatch):
        """Test that server creation fails when DD_API_KEY is missing."""
        monkeypatch.delenv("DD_API_KEY", raising=False)
        monkeypatch.setenv("DD_APP_KEY", "test_app_key")

        with pytest.raises(ValueError, match="DD_API_KEY environment variable is required"):
            create_server()

    def test_create_server_fails_without_app_key(self, monkeypatch):
        """Test that server creation fails when DD_APP_KEY is missing."""
        monkeypatch.setenv("DD_API_KEY", "test_api_key")
        monkeypatch.delenv("DD_APP_KEY", raising=False)

        with pytest.raises(ValueError, match="DD_APP_KEY environment variable is required"):
            create_server()

    def test_create_server_with_custom_site(self, monkeypatch):
        """Test that server creation accepts custom DD_SITE."""
        monkeypatch.setenv("DD_API_KEY", "test_api_key")
        monkeypatch.setenv("DD_APP_KEY", "test_app_key")
        monkeypatch.setenv("DD_SITE", "eu")

        server = create_server()
        assert server is not None

    def test_create_server_with_full_url_site(self, monkeypatch):
        """Test that server creation accepts full URL for DD_SITE."""
        monkeypatch.setenv("DD_API_KEY", "test_api_key")
        monkeypatch.setenv("DD_APP_KEY", "test_app_key")
        monkeypatch.setenv("DD_SITE", "https://api.custom.datadoghq.com")

        server = create_server()
        assert server is not None

    def test_create_server_with_partial_domain(self, monkeypatch):
        """Test that server creation handles partial domain format like 'us5.datadoghq.com'."""
        monkeypatch.setenv("DD_API_KEY", "test_api_key")
        monkeypatch.setenv("DD_APP_KEY", "test_app_key")
        monkeypatch.setenv("DD_SITE", "us5.datadoghq.com")

        server = create_server()
        assert server is not None


class TestToolRegistration:
    """Test that all expected tools are registered."""

    def test_apm_span_tools_registered(self, mock_env_vars):
        """Test that all APM span tools are registered with correct names."""
        server = create_server()

        # Get all registered tool names from mounted sub-servers
        tool_names = []
        for mounted_server in server._mounted_servers:
            sub_server = mounted_server.server
            tool_names.extend(sub_server._tool_manager._tools.keys())

        # Verify all span tools are registered (without prefix, since mounting adds it)
        expected_span_tools = [
            "search_spans",
            "get_slow_endpoints",
            "aggregate_spans",
            "get_span_by_id",
        ]

        for tool_name in expected_span_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered"

    def test_apm_service_tools_registered(self, mock_env_vars):
        """Test that all APM service tools are registered with correct names."""
        server = create_server()

        # Get all registered tool names from mounted sub-servers
        tool_names = []
        for mounted_server in server._mounted_servers:
            sub_server = mounted_server.server
            tool_names.extend(sub_server._tool_manager._tools.keys())

        # Verify all service tools are registered (without prefix, since mounting adds it)
        expected_service_tools = [
            "list_services",
            "get_service",
            "get_service_stats",
        ]

        for tool_name in expected_service_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not registered"

    def test_tool_count(self, mock_env_vars):
        """Test that the expected number of tools are registered."""
        server = create_server()

        # Count tools from all mounted sub-servers
        total_tools = 0
        for mounted_server in server._mounted_servers:
            sub_server = mounted_server.server
            total_tools += len(sub_server._tool_manager._tools)

        # Should have 4 span tools + 3 service tools = 7 total
        assert total_tools == 7, f"Expected 7 tools, got {total_tools}"

    def test_tool_schemas_have_descriptions(self, mock_env_vars):
        """Test that all tools have proper descriptions."""
        server = create_server()

        # Check tools from all mounted sub-servers
        for mounted_server in server._mounted_servers:
            sub_server = mounted_server.server
            tools = sub_server._tool_manager._tools

            for tool_name, tool in tools.items():
                assert tool.description, f"Tool {tool_name} missing description"
                assert len(tool.description) > 10, f"Tool {tool_name} description too short"


class TestMainEntryPoint:
    """Test the main CLI entry point."""

    def test_main_handles_config_error(self, monkeypatch):
        """Test that main() handles configuration errors gracefully."""
        monkeypatch.delenv("DD_API_KEY", raising=False)
        monkeypatch.setenv("DD_APP_KEY", "test_app_key")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_runs_server(self, mock_env_vars):
        """Test that main() creates and runs the server."""
        with patch("ddmcp.server.create_server") as mock_create:
            mock_server = mock_create.return_value
            mock_server.run.side_effect = KeyboardInterrupt()

            with pytest.raises(KeyboardInterrupt):
                main()

            mock_create.assert_called_once()
            mock_server.run.assert_called_once()

    def test_main_handles_unexpected_errors(self, mock_env_vars):
        """Test that main() handles unexpected errors."""
        with patch("ddmcp.server.create_server") as mock_create:
            mock_create.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
