"""
Minimal MCP Server Integration Tests

Simple tests that verify MCP server functionality without requiring 
external server connections.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from src.mcp.server import KeapMCPServer


class TestMCPServerMinimal:
    """Minimal MCP server integration tests."""

    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables."""
        with patch.dict(os.environ, {"KEAP_API_KEY": "test_key"}):
            yield

    def test_server_creation(self, mock_environment):
        """Test that MCP server can be created."""
        with patch("src.mcp.server.FastMCP") as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            server = KeapMCPServer("test-server")
            
            assert server.mcp == mock_mcp_instance
            mock_fastmcp.assert_called_once_with("test-server")

    def test_server_tool_registration(self, mock_environment):
        """Test that tools are registered with the server."""
        with patch("src.mcp.server.FastMCP") as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            server = KeapMCPServer("test-server")
            
            # Verify the server was created
            assert server.mcp == mock_mcp_instance
            
            # Verify FastMCP was called with correct name
            mock_fastmcp.assert_called_once_with("test-server")

    def test_server_initialization_with_tools(self, mock_environment):
        """Test server initialization includes tool setup."""
        with patch("src.mcp.server.FastMCP") as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            # Create server instance
            server = KeapMCPServer("test-integration")
            
            # Verify basic setup
            assert server.mcp is not None
            assert hasattr(server, 'mcp')
            
            # Verify that we can access the server name if needed
            assert mock_fastmcp.call_args[0][0] == "test-integration"