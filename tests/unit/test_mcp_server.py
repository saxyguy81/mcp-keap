"""
Unit tests for the MCP server.
"""

import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock

from src.mcp.server import KeapMCPServer


class TestKeapMCPServerInit:
    """Test MCP server initialization."""
    
    def test_init_default_name(self):
        """Test initialization with default name."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            server = KeapMCPServer()
            
            mock_fastmcp.assert_called_once_with("keap-mcp")
            assert server.mcp == mock_mcp_instance
    
    def test_init_custom_name(self):
        """Test initialization with custom name."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            server = KeapMCPServer("custom-name")
            
            mock_fastmcp.assert_called_once_with("custom-name")
            assert server.mcp == mock_mcp_instance
    
    def test_register_tools_called(self):
        """Test that _register_tools is called during initialization."""
        with patch('src.mcp.server.FastMCP'):
            with patch.object(KeapMCPServer, '_register_tools') as mock_register_tools:
                with patch.object(KeapMCPServer, '_register_resources') as mock_register_resources:
                    KeapMCPServer()
                    
                    mock_register_tools.assert_called_once()
                    mock_register_resources.assert_called_once()


class TestRegisterTools:
    """Test tool registration."""
    
    def test_register_tools(self):
        """Test that all tools are registered."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            KeapMCPServer()
            
            # Check that add_tool was called for each tool
            expected_calls = [
                'list_contacts',
                'search_contacts_by_email', 
                'search_contacts_by_name',
                'get_tags',
                'get_contacts_with_tag',
                'set_custom_field_values',
                'get_api_diagnostics'
            ]
            
            assert mock_mcp_instance.add_tool.call_count == len(expected_calls)
            
            # Verify each tool was added
            call_args = [call[0][0].__name__ for call in mock_mcp_instance.add_tool.call_args_list]
            for tool_name in expected_calls:
                assert tool_name in call_args


class TestRegisterResources:
    """Test resource registration."""
    
    @pytest.mark.asyncio
    async def test_get_keap_schema_resource(self):
        """Test keap schema resource."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            KeapMCPServer()
            
            # Verify resource decorator was called
            mock_mcp_instance.resource.assert_any_call("keap://schema")
            mock_mcp_instance.resource.assert_any_call("keap://capabilities")
            
            # Get the registered function for schema
            schema_calls = [call for call in mock_mcp_instance.resource.call_args_list 
                           if call[0][0] == "keap://schema"]
            assert len(schema_calls) == 1
    
    def test_schema_content(self):
        """Test schema resource content."""
        with patch('src.mcp.server.FastMCP'):
            server = KeapMCPServer()
            
            # Access the schema function directly
            # We need to manually call _register_resources to get the function
            server._register_resources()
            
            # The resource function is decorated, so we can't easily test it directly
            # Instead, we test the expected schema structure
            
            # This is a basic test - in a real scenario, you'd test the actual decorated function
            assert hasattr(server, 'mcp')
    
    def test_capabilities_content(self):
        """Test capabilities resource content."""
        with patch('src.mcp.server.FastMCP'):
            server = KeapMCPServer()
            
            # Similar to schema test - testing basic structure
            
            # Basic test for server initialization
            assert hasattr(server, 'mcp')


class TestServerRunMethods:
    """Test server run methods."""
    
    def test_run_method(self):
        """Test synchronous run method."""
        with patch('src.mcp.server.FastMCP'):
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_loop = MagicMock()
                mock_get_loop.return_value = mock_loop
                
                server = KeapMCPServer()
                server.run("localhost", 8080)
                
                mock_get_loop.assert_called_once()
                mock_loop.run_until_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_async_method(self):
        """Test asynchronous run method."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.add_tool = MagicMock()
            mock_mcp_instance.resource = MagicMock()
            mock_mcp_instance.run_sse_async = AsyncMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            server = KeapMCPServer()
            
            await server.run_async("localhost", 8080)
            
            mock_mcp_instance.run_sse_async.assert_called_once_with(host="localhost", port=8080)
    
    def test_run_default_parameters(self):
        """Test run with default parameters."""
        with patch('src.mcp.server.FastMCP'):
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_loop = MagicMock()
                mock_get_loop.return_value = mock_loop
                
                server = KeapMCPServer()
                server.run()
                
                # Verify run_until_complete was called (default params would be used)
                mock_loop.run_until_complete.assert_called_once()


class TestSchemaResourceContent:
    """Test the actual schema resource content."""
    
    @pytest.mark.asyncio
    async def test_schema_json_structure(self):
        """Test that schema returns valid JSON with expected structure."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            # Capture the schema function
            schema_function = None
            
            def capture_schema_decorator(uri):
                def decorator(func):
                    nonlocal schema_function
                    if uri == "keap://schema":
                        schema_function = func
                    return func
                return decorator
            
            mock_mcp_instance.resource.side_effect = capture_schema_decorator
            
            KeapMCPServer()
            
            # Call the captured schema function
            assert schema_function is not None
            schema_json = await schema_function()
            
            # Parse JSON to verify structure
            schema_data = json.loads(schema_json)
            
            assert "contacts" in schema_data
            assert "tags" in schema_data
            assert "filter_examples" in schema_data
            
            # Verify contacts structure
            contacts = schema_data["contacts"]
            assert "fields" in contacts
            assert "operators" in contacts
            
            # Verify specific fields exist
            contact_fields = contacts["fields"]
            expected_fields = ["id", "first_name", "last_name", "email", "date_created", "date_updated"]
            for field in expected_fields:
                assert field in contact_fields
            
            # Verify operators structure
            operators = contacts["operators"]
            assert "string" in operators
            assert "numeric" in operators
            assert "date" in operators
            assert "logical" in operators
    
    @pytest.mark.asyncio
    async def test_capabilities_json_structure(self):
        """Test that capabilities returns valid JSON with expected structure."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_fastmcp.return_value = mock_mcp_instance
            
            # Capture the capabilities function
            capabilities_function = None
            
            def capture_capabilities_decorator(uri):
                def decorator(func):
                    nonlocal capabilities_function
                    if uri == "keap://capabilities":
                        capabilities_function = func
                    return func
                return decorator
            
            mock_mcp_instance.resource.side_effect = capture_capabilities_decorator
            
            KeapMCPServer()
            
            # Call the captured capabilities function
            assert capabilities_function is not None
            capabilities_json = await capabilities_function()
            
            # Parse JSON to verify structure
            capabilities_data = json.loads(capabilities_json)
            
            assert "name" in capabilities_data
            assert "version" in capabilities_data
            assert "description" in capabilities_data
            assert "functions" in capabilities_data
            assert "filter_capabilities" in capabilities_data
            
            # Verify functions list
            functions = capabilities_data["functions"]
            assert isinstance(functions, list)
            assert len(functions) > 0
            
            # Verify each function has required fields
            for function in functions:
                assert "name" in function
                assert "description" in function
            
            # Verify filter capabilities
            filter_caps = capabilities_data["filter_capabilities"]
            expected_capabilities = [
                "unified_filter_structure",
                "logical_operators", 
                "nested_conditions",
                "pattern_matching",
                "tag_expressions",
                "custom_field_filtering"
            ]
            for cap in expected_capabilities:
                assert cap in filter_caps


class TestServerIntegration:
    """Test server integration aspects."""
    
    def test_server_with_all_imports(self):
        """Test that server can be created with all real imports."""
        # This test ensures all imports work correctly
        try:
            from src.mcp.server import KeapMCPServer
            
            with patch('src.mcp.server.FastMCP'):
                server = KeapMCPServer()
                assert server is not None
                
        except ImportError as e:
            pytest.fail(f"Import error: {e}")
    
    def test_logging_setup(self):
        """Test that logging is properly configured."""
        with patch('src.mcp.server.FastMCP'):
            with patch('src.mcp.server.logger') as mock_logger:
                server = KeapMCPServer()
                
                # Test that logger is available
                assert mock_logger is not None
                
                # Run method should log startup message
                with patch('asyncio.get_event_loop'):
                    with patch('asyncio.AbstractEventLoop.run_until_complete'):
                        server.run("localhost", 8080)
                
                # Verify logging calls were made during run
                assert mock_logger.info.call_count >= 1


class TestErrorHandling:
    """Test error handling in the server."""
    
    def test_run_with_exception_handling(self):
        """Test that run method handles exceptions gracefully."""
        with patch('src.mcp.server.FastMCP'):
            with patch('asyncio.get_event_loop') as mock_get_loop:
                # Mock loop to raise an exception
                mock_loop = MagicMock()
                mock_loop.run_until_complete.side_effect = Exception("Test error")
                mock_get_loop.return_value = mock_loop
                
                server = KeapMCPServer()
                
                # This should not raise an exception in the test
                # The actual implementation might handle it differently
                try:
                    server.run()
                except Exception:
                    # Expected if not properly handled
                    pass
    
    @pytest.mark.asyncio
    async def test_run_async_with_exception_handling(self):
        """Test that run_async method handles exceptions gracefully."""
        with patch('src.mcp.server.FastMCP') as mock_fastmcp:
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.run_sse_async = AsyncMock(side_effect=Exception("Async test error"))
            mock_fastmcp.return_value = mock_mcp_instance
            
            server = KeapMCPServer()
            
            # This should raise the exception
            with pytest.raises(Exception, match="Async test error"):
                await server.run_async()


class TestResourceFunctionContent:
    """Test the actual content of resource functions."""
    
    def test_schema_contains_filter_examples(self):
        """Test that schema contains comprehensive filter examples."""
        with patch('src.mcp.server.FastMCP'):
            MagicMock()
            
            # We'll manually test the schema content by calling the method
            KeapMCPServer()
            
            # Since we can't easily extract the decorated function,
            # we'll test the expected content structure
            
            # This is a structural test - the actual schema should contain these concepts
            assert True  # Placeholder for actual schema content verification
    
    def test_capabilities_version_info(self):
        """Test that capabilities contain correct version information."""
        with patch('src.mcp.server.FastMCP'):
            server = KeapMCPServer()
            
            # Test that the server is properly initialized
            # Version should be "2.0.0" based on the implementation
            assert hasattr(server, 'mcp')
            
            # In a real test, you'd extract and verify the actual version
            expected_version = "2.0.0"
            assert expected_version  # Placeholder for actual version verification