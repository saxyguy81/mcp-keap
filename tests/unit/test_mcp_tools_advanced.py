"""
Advanced unit tests for MCP Tools - focusing on uncovered functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.server.fastmcp import Context

from src.mcp.tools import (
    intersect_id_lists,
    query_contacts_by_custom_field,
    query_contacts_optimized,
    analyze_query_performance,
    set_custom_field_values,
    get_api_diagnostics,
    modify_tags,
    get_available_tools,
    get_tool_by_name
)


class TestAdvancedMCPTools:
    """Test advanced MCP tools functionality"""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock context"""
        context = MagicMock(spec=Context)
        context.api_client = AsyncMock()
        context.cache_manager = MagicMock()
        return context
    
    @pytest.mark.asyncio
    async def test_intersect_id_lists_success(self, mock_context):
        """Test successful ID list intersection"""
        lists = [
            {"item_ids": [1, 2, 3, 4]},
            {"item_ids": [2, 3, 4, 5]},
            {"item_ids": [3, 4, 5, 6]}
        ]
        
        result = await intersect_id_lists(mock_context, lists)
        
        assert result["success"] is True
        assert set(result["intersection"]) == {3, 4}
        assert result["count"] == 2
        assert result["lists_processed"] == 3
    
    @pytest.mark.asyncio
    async def test_intersect_id_lists_insufficient_lists(self, mock_context):
        """Test ID list intersection with insufficient lists"""
        lists = [{"item_ids": [1, 2, 3]}]
        
        result = await intersect_id_lists(mock_context, lists)
        
        assert result["success"] is False
        assert "At least two lists are required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_intersect_id_lists_invalid_field(self, mock_context):
        """Test ID list intersection with invalid field"""
        lists = [
            {"item_ids": [1, 2, 3]},
            {"wrong_field": "not a list"}
        ]
        
        result = await intersect_id_lists(mock_context, lists, id_field="item_ids")
        
        assert result["success"] is False
        assert "must be a list" in result["error"]
    
    @pytest.mark.asyncio
    async def test_query_contacts_by_custom_field_basic(self, mock_context):
        """Test querying contacts by custom field"""
        mock_contacts = [
            {"id": 1, "custom_fields": [{"id": 7, "content": "VIP"}]},
            {"id": 2, "custom_fields": [{"id": 7, "content": "Regular"}]}
        ]
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api, \
             patch('src.mcp.tools.get_cache_manager') as mock_get_cache, \
             patch('src.utils.contact_utils.get_custom_field_value') as mock_get_field, \
             patch('src.utils.contact_utils.format_contact_data') as mock_format:
            
            mock_api_client = AsyncMock()
            mock_api_client.get_contacts.return_value = {"contacts": mock_contacts}
            mock_get_api.return_value = mock_api_client
            
            mock_cache = MagicMock()
            mock_cache.get.return_value = None  # Cache miss
            mock_cache.set = AsyncMock()
            mock_get_cache.return_value = mock_cache
            
            # Mock custom field value extraction
            mock_get_field.side_effect = lambda contact, field_id: "VIP" if contact["id"] == 1 else "Regular"
            
            # Mock contact formatting
            mock_format.side_effect = lambda x: x
            
            result = await query_contacts_by_custom_field(
                mock_context,
                field_id="7",
                field_value="VIP",
                operator="equals"
            )
            
            assert len(result) == 1
            assert result[0]["id"] == 1
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_contacts_optimized_basic(self, mock_context):
        """Test optimized contact query"""
        mock_contacts = [{"id": 1, "name": "John Doe"}]
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api, \
             patch('src.mcp.tools.get_cache_manager') as mock_get_cache, \
             patch('src.mcp.contact_tools.list_contacts', return_value=mock_contacts) as mock_list:
            
            result = await query_contacts_optimized(
                mock_context,
                filters=[{"field": "name", "operator": "=", "value": "John"}],
                enable_optimization=False
            )
            
            assert result["contacts"] == mock_contacts
            assert result["count"] == 1
            assert "performance_metrics" not in result
            
            mock_list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_query_performance_basic(self, mock_context):
        """Test basic query performance analysis"""
        filters = [
            {"field": "email", "operator": "=", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"}
        ]
        
        # Mock optimization results
        mock_optimization_result = MagicMock()
        mock_optimization_result.optimization_strategy = "highly_optimized"
        mock_optimization_result.optimization_score = 0.9
        mock_optimization_result.estimated_data_reduction_ratio = 0.8
        mock_optimization_result.server_side_filters = [filters[0]]
        mock_optimization_result.client_side_filters = [filters[1]]
        
        mock_performance_analysis = {
            "performance_rating": "excellent"
        }
        
        with patch('src.mcp.optimization.api_optimization.ApiParameterOptimizer') as mock_api_opt, \
             patch('src.mcp.optimization.optimization.QueryOptimizer') as mock_query_opt:
            
            mock_api_optimizer = mock_api_opt.return_value
            mock_api_optimizer.optimize_contact_query_parameters.return_value = mock_optimization_result
            mock_api_optimizer.analyze_filter_performance.return_value = mock_performance_analysis
            mock_api_optimizer.get_field_optimization_info.return_value = {"email": "high_performance"}
            
            mock_query_optimizer = mock_query_opt.return_value
            mock_query_optimizer.analyze_query.return_value = "server_optimized"
            
            result = await analyze_query_performance(
                mock_context,
                filters,
                query_type="contact"
            )
            
            assert "query_analysis" in result
            assert "filter_breakdown" in result
            assert "optimization_suggestions" in result
    
    @pytest.mark.asyncio
    async def test_set_custom_field_values_common_value_mode(self, mock_context):
        """Test setting custom field values with common value parameter"""
        contact_ids = ["1", "2", "3"]
        common_value = "Premium"
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api, \
             patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
            
            mock_api_client = AsyncMock()
            mock_api_client.update_contact_custom_field.return_value = {"success": True}
            mock_get_api.return_value = mock_api_client
            
            mock_cache = MagicMock()
            mock_cache.invalidate_pattern = AsyncMock()
            mock_get_cache.return_value = mock_cache
            
            result = await set_custom_field_values(
                mock_context,
                field_id="7",
                contact_ids=contact_ids,
                common_value=common_value
            )
            
            assert result["success"] is True
            assert result["successful_updates"] == 3
            assert result["field_id"] == "7"
    
    @pytest.mark.asyncio
    async def test_set_custom_field_values_invalid_params(self, mock_context):
        """Test setting custom field values with invalid parameters"""
        # Test conflicting parameters
        result = await set_custom_field_values(
            mock_context,
            field_id="7",
            contact_values={"1": "test"},
            contact_ids=["1"],
            common_value="test"
        )
        
        assert result["success"] is False
        assert "Cannot specify both" in result["error"]
        
        # Test missing parameters
        result = await set_custom_field_values(
            mock_context,
            field_id="7"
        )
        
        assert result["success"] is False
        assert "Must specify either" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_api_diagnostics_success(self, mock_context):
        """Test successful API diagnostics retrieval"""
        mock_api_diagnostics = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "retried_requests": 10,
            "rate_limited_requests": 2,
            "cache_hits": 50,
            "cache_misses": 50,
            "average_response_time": 1.5,
            "requests_per_hour": 3000,
            "endpoints_called": {"contacts": 60, "tags": 40},
            "error_counts": {"401": 3, "429": 2},
            "last_request_time": "2024-01-01T12:00:00Z"
        }
        
        mock_cache_diagnostics = {"cache_size": "10MB"}
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api, \
             patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
            
            mock_api_client = MagicMock()
            mock_api_client.get_diagnostics.return_value = mock_api_diagnostics
            mock_get_api.return_value = mock_api_client
            
            mock_cache = MagicMock()
            mock_cache.get_diagnostics.return_value = mock_cache_diagnostics
            mock_get_cache.return_value = mock_cache
            
            result = await get_api_diagnostics(mock_context)
            
            assert result["api_diagnostics"] == mock_api_diagnostics
            assert result["cache_diagnostics"] == mock_cache_diagnostics
            assert "performance_metrics" in result
            assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_modify_tags_add_action(self, mock_context):
        """Test adding tags to contacts"""
        contact_ids = ["1", "2"]
        tag_ids = ["10", "20"]
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api, \
             patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
            
            mock_api_client = AsyncMock()
            mock_api_client.apply_tag_to_contacts.return_value = {"success": True}
            mock_get_api.return_value = mock_api_client
            
            result = await modify_tags(
                mock_context,
                contact_ids=contact_ids,
                tag_ids=tag_ids,
                action="add"
            )
            
            assert result["success"] is True
            assert "Successfully added tags" in result["message"]
            assert mock_api_client.apply_tag_to_contacts.call_count == 2
    
    @pytest.mark.asyncio
    async def test_modify_tags_remove_action(self, mock_context):
        """Test removing tags from contacts"""
        contact_ids = ["1", "2"]
        tag_ids = ["10"]
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api, \
             patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
            
            mock_api_client = AsyncMock()
            mock_api_client.remove_tag_from_contacts.return_value = {"success": True}
            mock_get_api.return_value = mock_api_client
            
            result = await modify_tags(
                mock_context,
                contact_ids=contact_ids,
                tag_ids=tag_ids,
                action="remove"
            )
            
            assert result["success"] is True
            assert "Successfully removed tags" in result["message"]
            mock_api_client.remove_tag_from_contacts.assert_called_once_with("10", contact_ids)
    
    @pytest.mark.asyncio
    async def test_modify_tags_invalid_action(self, mock_context):
        """Test modify tags with invalid action"""
        result = await modify_tags(
            mock_context,
            contact_ids=["1"],
            tag_ids=["10"],
            action="invalid"
        )
        
        assert result["success"] is False
        assert "Invalid action" in result["error"]
    
    def test_get_available_tools(self):
        """Test getting list of available tools"""
        tools = get_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check that tools have required structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert "parameters" in tool
    
    def test_get_tool_by_name_existing(self):
        """Test getting tool by existing name"""
        tool = get_tool_by_name("list_contacts")
        
        assert tool is not None
        assert tool["name"] == "list_contacts"
        assert "description" in tool
    
    def test_get_tool_by_name_nonexistent(self):
        """Test getting tool by non-existent name"""
        tool = get_tool_by_name("nonexistent_tool")
        
        assert tool is None