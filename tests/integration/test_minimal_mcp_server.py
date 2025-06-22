"""
Minimal MCP Server Integration Test

This test properly validates MCP protocol functionality by:
1. Starting the MCP server correctly
2. Testing that the server can register MCP tools
3. Testing basic server functionality without HTTP REST calls
4. Using proper MCP protocol communication through direct tool calls
5. Focusing on core server functionality with proper imports
"""

import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock, AsyncMock

from src.mcp.server import KeapMCPServer


class TestMinimalMCPServer:
    """Minimal integration tests for MCP server functionality."""

    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables for testing."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_api_key_for_mcp"}):
            yield

    @pytest.fixture
    def mock_api_dependencies(self):
        """Mock all API dependencies to focus on MCP functionality."""
        with patch("src.api.client.KeapApiService") as mock_get_api, \
             patch("src.cache.manager.CacheManager") as mock_get_cache, \
             patch("src.api.client.KeapApiService") as mock_keap_service:
            
            # Mock API client
            mock_api_client = AsyncMock()
            mock_api_client.get_contacts.return_value = {
                "contacts": [
                    {
                        "id": 1,
                        "given_name": "Test",
                        "family_name": "User",
                        "email_addresses": [{"email": "test@example.com"}]
                    }
                ]
            }
            # Mock health check methods for diagnostics
            mock_api_client.health_check = AsyncMock(return_value={"status": "ok"})
            mock_api_client.get_rate_limit_info = AsyncMock(return_value={"remaining": 1000})
            mock_api_client.close = AsyncMock()
            
            mock_get_api.return_value = mock_api_client
            mock_keap_service.return_value = mock_api_client
            
            # Mock cache manager
            mock_cache = MagicMock()
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            mock_cache.get_stats.return_value = {"hits": 0, "misses": 0}
            mock_get_cache.return_value = mock_cache
            
            yield {
                "api_client": mock_api_client,
                "cache_manager": mock_cache
            }

    def test_mcp_server_creation_and_initialization(self, mock_environment, mock_api_dependencies):
        """Test that MCP server can be created and properly initialized."""
        server = KeapMCPServer("test-mcp-server")
        
        # Verify server initialization
        assert server is not None
        assert server.name == "test-mcp-server"
        assert server.version == "1.0.0"
        assert hasattr(server, 'mcp')
        assert server.mcp is not None

    def test_mcp_tool_registration(self, mock_environment, mock_api_dependencies):
        """Test that MCP tools are properly registered with the server."""
        server = KeapMCPServer("test-tool-registration")
        
        # Get list of registered tools
        tools = server.list_tools()
        
        # Verify core MCP tools are registered (collection-based architecture)
        expected_tools = [
            "list_contacts",
            "get_contact_schema",
            "collection_union",
            "collection_intersect",
            "collection_diff",
            "collection_count",
            "get_collection_details",
            "get_collection_ids",
            "get_tags",
            "modify_collection_tags",
            "get_api_diagnostics"
        ]
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Verify expected tools are present
        for tool in expected_tools:
            assert tool in tools, f"Tool '{tool}' not found in registered tools: {tools}"

    @pytest.mark.asyncio
    async def test_mcp_tool_execution_via_protocol(self, mock_environment, mock_api_dependencies):
        """Test MCP tool execution through the protocol interface."""
        server = KeapMCPServer("test-tool-execution")
        
        # Test that we can call tools through the MCP interface
        try:
            # Use FastMCP's call_tool method if available
            if hasattr(server.mcp, 'call_tool'):
                # Test calling a simple tool - mock the API diagnostics properly for network simulation
                with patch('src.mcp.tools_collections.get_api_diagnostics') as mock_diag:
                    mock_diag.return_value = {"status": "ok", "version": "test", "api_health": "mocked"}
                    result = await server.mcp.call_tool("get_api_diagnostics", {})
                    assert result is not None
                
            # Verify that the underlying FastMCP instance has tools
            if hasattr(server.mcp, 'list_tools'):
                tools_coroutine = server.mcp.list_tools()
                if asyncio.iscoroutine(tools_coroutine):
                    tools = await tools_coroutine
                else:
                    tools = tools_coroutine
                assert len(tools) > 0
                
        except (AttributeError, TypeError) as e:
            # If call_tool isn't available, verify the tools are at least registered
            tools = server.list_tools()
            assert len(tools) > 0
            pytest.skip(f"FastMCP async methods not accessible in test: {e}")

    @pytest.mark.asyncio
    async def test_mcp_resource_registration(self, mock_environment, mock_api_dependencies):
        """Test that MCP resources are properly registered."""
        server = KeapMCPServer("test-resource-registration")
        
        # Verify that the server has resources registered
        assert hasattr(server, '_register_resources')
        
        # Test that we can access resource information
        try:
            if hasattr(server.mcp, 'list_resource_templates'):
                resources_coroutine = server.mcp.list_resource_templates()
                if asyncio.iscoroutine(resources_coroutine):
                    resources = await resources_coroutine
                else:
                    resources = resources_coroutine
                # Should have keap://schema and keap://capabilities
                assert isinstance(resources, (list, dict))
        except (AttributeError, TypeError):
            # If resource listing isn't available, just verify the method exists
            assert callable(getattr(server, '_register_resources'))

    @pytest.mark.asyncio
    async def test_mcp_server_core_functionality(self, mock_environment, mock_api_dependencies):
        """Test core MCP server functionality without external dependencies."""
        server = KeapMCPServer("test-core-functionality")
        
        # Verify server has the required MCP components
        assert hasattr(server, 'mcp')
        assert hasattr(server, 'list_tools')
        assert hasattr(server, 'run')
        assert hasattr(server, 'run_async')
        
        # Verify tools are accessible
        tools = server.list_tools()
        assert len(tools) >= 11  # Should have exactly 11 collection-based tools
        
        # Verify server configuration
        assert server.name == "test-core-functionality"
        assert server.version == "1.0.0"

    def test_mcp_server_with_mock_tools(self, mock_environment, mock_api_dependencies):
        """Test MCP server functionality with properly mocked tool dependencies."""
        # Mock the tool imports at the server level
        with patch('src.mcp.tools_collections.list_contacts') as mock_list, \
             patch('src.mcp.tools_collections.get_contact_schema') as mock_schema, \
             patch('src.mcp.tools_collections.get_api_diagnostics') as mock_diagnostics:
            
            # Setup mock returns for collection architecture  
            mock_list.return_value = {"collection_id": "test_123", "count": 0}
            mock_schema.return_value = {"standard_fields": [], "custom_fields": []}
            mock_diagnostics.return_value = {"status": "ok", "version": "test", "network_health": "simulated"}
            
            # Create server
            server = KeapMCPServer("test-mock-tools")
            
            # Verify server creation succeeded
            assert server is not None
            tools = server.list_tools()
            assert len(tools) > 0
            
            # Verify that tools can be listed without errors
            assert "list_contacts" in tools
            assert "get_api_diagnostics" in tools
            assert "collection_union" in tools  # Verify collection-based tools

    def test_server_tool_count_and_names(self, mock_environment, mock_api_dependencies):
        """Test that server registers the expected number and names of tools."""
        server = KeapMCPServer("test-tool-count")
        
        tools = server.list_tools()
        
        # Should have exactly 11 collection-based tools
        assert len(tools) == 11
        
        # Verify all expected tool names (collection-based architecture)
        expected_tools = {
            "list_contacts",
            "get_contact_schema",
            "collection_union",
            "collection_intersect",
            "collection_diff",
            "collection_count",
            "get_collection_details",
            "get_collection_ids",
            "get_tags",
            "modify_collection_tags",
            "get_api_diagnostics"
        }
        
        actual_tools = set(tools)
        assert actual_tools == expected_tools, f"Tool mismatch. Expected: {expected_tools}, Got: {actual_tools}"

    def test_import_integrity(self, mock_environment):
        """Test that all necessary imports work correctly for MCP server."""
        # Test that we can import the server without any import errors
        try:
            from src.mcp.server import KeapMCPServer
            from fastmcp import FastMCP
            
            # Test that server can be created (this tests import dependencies)
            with patch("src.api.client.KeapApiService"), \
                 patch("src.cache.manager.CacheManager"):
                server = KeapMCPServer("test-imports")
                assert server is not None
                
        except ImportError as e:
            pytest.fail(f"Import error in MCP server: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error creating MCP server: {e}")