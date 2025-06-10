"""
Unit tests for MCP tools with comprehensive mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.server.fastmcp import Context

from src.mcp.tools import (
    get_api_client, get_cache_manager, list_contacts, search_contacts_by_email,
    search_contacts_by_name, get_tags, get_contacts_with_tag, get_contact_details,
    get_tag_details, apply_tags_to_contacts, remove_tags_from_contacts,
    create_tag, intersect_id_lists, query_contacts_by_custom_field,
    modify_tags, set_custom_field_values, get_api_diagnostics,
    _generate_performance_recommendations
)


class TestToolFactoryFunctions:
    """Test factory functions for shared components."""
    
    def test_get_api_client(self):
        """Test API client factory."""
        with patch('src.mcp.tools.KeapApiService') as mock_service:
            mock_instance = MagicMock()
            mock_service.return_value = mock_instance
            
            result = get_api_client()
            
            assert result == mock_instance
            mock_service.assert_called_once()
    
    def test_get_cache_manager(self):
        """Test cache manager factory."""
        with patch('src.mcp.tools.CacheManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            result = get_cache_manager()
            
            assert result == mock_instance
            mock_manager.assert_called_once()


class TestContactTools:
    """Test contact-related MCP tools."""
    
    @pytest.mark.asyncio
    async def test_list_contacts(self):
        """Test list_contacts tool."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                with patch('src.mcp.contact_tools.list_contacts', new_callable=AsyncMock) as mock_list:
                    mock_contacts = [{"id": 1, "name": "Test"}]
                    mock_list.return_value = mock_contacts
                    
                    result = await list_contacts(context, limit=50)
                    
                    assert result == mock_contacts
                    # Verify that dependencies are created via factory functions
                    mock_list.assert_called_once()
                    # The context doesn't get modified since we use ContextWithDeps internally
    
    @pytest.mark.asyncio
    async def test_search_contacts_by_email(self):
        """Test search_contacts_by_email tool."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                with patch('src.mcp.contact_tools.search_contacts_by_email', new_callable=AsyncMock) as mock_search:
                    mock_contacts = [{"id": 1, "email": "test@example.com"}]
                    mock_search.return_value = mock_contacts
                    
                    result = await search_contacts_by_email(context, "test@example.com")
                    
                    assert result == mock_contacts
                    mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_contacts_by_name(self):
        """Test search_contacts_by_name tool."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                with patch('src.mcp.contact_tools.search_contacts_by_name', new_callable=AsyncMock) as mock_search:
                    mock_contacts = [{"id": 1, "name": "John Doe"}]
                    mock_search.return_value = mock_contacts
                    
                    result = await search_contacts_by_name(context, "John")
                    
                    assert result == mock_contacts
    
    @pytest.mark.asyncio
    async def test_get_contact_details(self):
        """Test get_contact_details tool."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                with patch('src.mcp.contact_tools.get_contact_details', new_callable=AsyncMock) as mock_get:
                    mock_contact = {"id": 123, "name": "John Doe", "email": "john@example.com"}
                    mock_get.return_value = mock_contact
                    
                    result = await get_contact_details(context, "123")
                    
                    assert result == mock_contact


class TestTagTools:
    """Test tag-related MCP tools."""
    
    @pytest.mark.asyncio
    async def test_get_tags(self):
        """Test get_tags tool."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                with patch('src.mcp.tag_tools.get_tags', new_callable=AsyncMock) as mock_get:
                    mock_tags = [{"id": 1, "name": "VIP"}]
                    mock_get.return_value = mock_tags
                    
                    result = await get_tags(context, limit=100)
                    
                    assert result == mock_tags
    
    @pytest.mark.asyncio
    async def test_get_contacts_with_tag(self):
        """Test get_contacts_with_tag tool."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                with patch('src.mcp.tag_tools.get_contacts_with_tag', new_callable=AsyncMock) as mock_get:
                    mock_contacts = [{"id": 1, "name": "Tagged Contact"}]
                    mock_get.return_value = mock_contacts
                    
                    result = await get_contacts_with_tag(context, "123")
                    
                    assert result == mock_contacts
    
    @pytest.mark.asyncio
    async def test_get_tag_details(self):
        """Test get_tag_details tool."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                with patch('src.mcp.tag_tools.get_tag_details', new_callable=AsyncMock) as mock_get:
                    mock_tag = {"id": 123, "name": "VIP", "description": "VIP customers"}
                    mock_get.return_value = mock_tag
                    
                    result = await get_tag_details(context, "123")
                    
                    assert result == mock_tag
    
    @pytest.mark.asyncio
    async def test_apply_tags_to_contacts(self):
        """Test apply_tags_to_contacts tool."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                with patch('src.mcp.tag_tools.apply_tags_to_contacts', new_callable=AsyncMock) as mock_apply:
                    mock_result = {"success": True, "applied_count": 2}
                    mock_apply.return_value = mock_result
                    
                    result = await apply_tags_to_contacts(context, ["123"], ["456", "789"])
                    
                    assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_remove_tags_from_contacts(self):
        """Test remove_tags_from_contacts tool."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                with patch('src.mcp.tag_tools.remove_tags_from_contacts', new_callable=AsyncMock) as mock_remove:
                    mock_result = {"success": True, "removed_count": 2}
                    mock_remove.return_value = mock_result
                    
                    result = await remove_tags_from_contacts(context, ["123"], ["456", "789"])
                    
                    assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_create_tag(self):
        """Test create_tag tool."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                with patch('src.mcp.tag_tools.create_tag', new_callable=AsyncMock) as mock_create:
                    mock_tag = {"id": 123, "name": "New Tag"}
                    mock_create.return_value = mock_tag
                    
                    result = await create_tag(context, "New Tag", "Description")
                    
                    assert result == mock_tag


class TestModifyTags:
    """Test modify_tags functionality."""
    
    @pytest.mark.asyncio
    async def test_modify_tags_add_success(self):
        """Test successful tag addition."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_api_client.apply_tag_to_contacts.return_value = {"success": True}
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                result = await modify_tags(context, ["123"], ["456"], "add")
        
        assert result["success"] is True
        assert "Successfully added tags" in result["message"]
        mock_api_client.apply_tag_to_contacts.assert_called_once_with("456", ["123"])
    
    @pytest.mark.asyncio
    async def test_modify_tags_remove_success(self):
        """Test successful tag removal."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_api_client.remove_tag_from_contacts.return_value = {"success": True}
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                result = await modify_tags(context, ["123"], ["456"], "remove")
        
        assert result["success"] is True
        assert "Successfully removed tags" in result["message"]
        mock_api_client.remove_tag_from_contacts.assert_called_once_with("456", ["123"])
    
    @pytest.mark.asyncio
    async def test_modify_tags_add_failure(self):
        """Test tag addition failure."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_api_client.apply_tag_to_contacts.return_value = {"success": False}
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                result = await modify_tags(context, ["123"], ["456"], "add")
        
        assert result["success"] is False
        assert "Failed to apply tag 456" in result["error"]
    
    @pytest.mark.asyncio
    async def test_modify_tags_invalid_action(self):
        """Test invalid action."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                result = await modify_tags(context, ["123"], ["456"], "invalid")
        
        assert result["success"] is False
        assert "Invalid action: invalid" in result["error"]
    
    @pytest.mark.asyncio
    async def test_modify_tags_exception(self):
        """Test exception handling."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_api_client.apply_tag_to_contacts.side_effect = Exception("API Error")
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                result = await modify_tags(context, ["123"], ["456"], "add")
        
        assert result["success"] is False
        assert "API Error" in result["error"]


class TestSetCustomFieldValues:
    """Test set_custom_field_values functionality."""
    
    @pytest.mark.asyncio
    async def test_set_custom_field_values_common_value_success(self):
        """Test successful common value setting."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_api_client.update_contact_custom_field.return_value = {"success": True}
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                result = await set_custom_field_values(
                    context, "7", contact_ids=["123", "456"], common_value="VIP"
                )
        
        assert result["success"] is True
        assert result["successful_updates"] == 2
        assert result["failed_updates"] == 0
        assert mock_api_client.update_contact_custom_field.call_count == 2
        assert mock_cache_manager.invalidate_pattern.call_count == 4  # 2 patterns × 2 contacts
    
    @pytest.mark.asyncio
    async def test_set_custom_field_values_individual_values_success(self):
        """Test successful individual value setting."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_api_client.update_contact_custom_field.return_value = {"success": True}
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                contact_values = {"123": "Gold", "456": "Silver"}
                
                result = await set_custom_field_values(
                    context, "7", contact_values=contact_values
                )
        
        assert result["success"] is True
        assert result["successful_updates"] == 2
        assert result["failed_updates"] == 0
    
    @pytest.mark.asyncio
    async def test_set_custom_field_values_validation_error(self):
        """Test validation error for conflicting parameters."""
        context = Context()
        
        result = await set_custom_field_values(
            context, "7", 
            contact_values={"123": "Value"}, 
            contact_ids=["123"], 
            common_value="Other"
        )
        
        assert result["success"] is False
        assert "Cannot specify both" in result["error"]
    
    @pytest.mark.asyncio
    async def test_set_custom_field_values_missing_parameters(self):
        """Test validation error for missing parameters."""
        context = Context()
        
        result = await set_custom_field_values(context, "7")
        
        assert result["success"] is False
        assert "Must specify either" in result["error"]
    
    @pytest.mark.asyncio
    async def test_set_custom_field_values_partial_failure(self):
        """Test partial failure scenario."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        # First call succeeds, second fails
        mock_api_client.update_contact_custom_field.side_effect = [
            {"success": True},
            {"success": False, "error": "Invalid field"}
        ]
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                result = await set_custom_field_values(
                    context, "7", contact_ids=["123", "456"], common_value="VIP"
                )
        
        assert result["success"] is False  # Overall failure due to partial failure
        assert result["successful_updates"] == 1
        assert result["failed_updates"] == 1
        assert "Partially successful" in result["message"]


class TestUtilityFunctions:
    """Test utility functions."""
    
    @pytest.mark.asyncio
    async def test_intersect_id_lists_success(self):
        """Test successful ID list intersection."""
        context = Context()
        
        lists = [
            {"item_ids": ["1", "2", "3"]},
            {"item_ids": ["2", "3", "4"]},
            {"item_ids": ["3", "4", "5"]}
        ]
        
        result = await intersect_id_lists(context, lists)
        
        assert result["success"] is True
        assert result["intersection"] == ["3"]
        assert result["count"] == 1
        assert result["lists_processed"] == 3
    
    @pytest.mark.asyncio
    async def test_intersect_id_lists_insufficient_lists(self):
        """Test intersection with insufficient lists."""
        context = Context()
        
        lists = [{"item_ids": ["1", "2"]}]
        
        result = await intersect_id_lists(context, lists)
        
        assert result["success"] is False
        assert "At least two lists are required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_intersect_id_lists_invalid_field(self):
        """Test intersection with invalid field type."""
        context = Context()
        
        lists = [
            {"item_ids": "not_a_list"},
            {"item_ids": ["2", "3"]}
        ]
        
        result = await intersect_id_lists(context, lists)
        
        assert result["success"] is False
        assert "must be a list" in result["error"]


class TestApiDiagnostics:
    """Test API diagnostics functionality."""
    
    @pytest.mark.asyncio
    async def test_get_api_diagnostics_success(self):
        """Test successful diagnostics retrieval."""
        context = Context()
        mock_api_client = MagicMock()
        mock_cache_manager = MagicMock()
        
        # Mock API diagnostics
        mock_api_diagnostics = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "retried_requests": 10,
            "rate_limited_requests": 2,
            "cache_hits": 50,
            "cache_misses": 10,
            "average_response_time": 0.5,
            "requests_per_hour": 3000,
            "last_request_time": 1234567890.0,
            "endpoints_called": {"/contacts": 80, "/tags": 20},
            "error_counts": {"HTTP_500": 3, "HTTP_429": 2}
        }
        
        mock_api_client.get_diagnostics.return_value = mock_api_diagnostics
        mock_cache_manager.get_diagnostics.return_value = {"cache_size": 1000}
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                with patch('platform.platform', return_value="macOS"):
                    with patch('platform.python_version', return_value="3.11.6"):
                        result = await get_api_diagnostics(context)
        
        assert "api_diagnostics" in result
        assert "cache_diagnostics" in result
        assert "system_info" in result
        assert "performance_metrics" in result
        assert "top_endpoints" in result
        assert "top_errors" in result
        assert "recommendations" in result
        
        # Check performance metrics calculation
        assert result["performance_metrics"]["success_rate"] == 95.0
        assert result["performance_metrics"]["retry_rate"] == 10.0
    
    @pytest.mark.asyncio
    async def test_get_api_diagnostics_exception(self):
        """Test diagnostics with exception."""
        context = Context()
        
        with patch('src.mcp.tools.get_api_client', side_effect=Exception("Client error")):
            result = await get_api_diagnostics(context)
        
        assert "error" in result
        assert "Client error" in result["error"]
        assert "timestamp" in result


class TestPerformanceRecommendations:
    """Test performance recommendation generation."""
    
    def test_generate_performance_recommendations_poor_success_rate(self):
        """Test recommendations for poor success rate."""
        api_diagnostics = {"average_response_time": 0.5, "requests_per_hour": 3000}
        performance_metrics = {
            "success_rate": 90.0,
            "retry_rate": 5.0,
            "rate_limit_hit_rate": 2.0,
            "cache_hit_rate": 80.0
        }
        
        recommendations = _generate_performance_recommendations(api_diagnostics, performance_metrics)
        
        assert any("Success rate is below 95%" in rec for rec in recommendations)
    
    def test_generate_performance_recommendations_high_retry_rate(self):
        """Test recommendations for high retry rate."""
        api_diagnostics = {"average_response_time": 0.5, "requests_per_hour": 3000}
        performance_metrics = {
            "success_rate": 97.0,
            "retry_rate": 15.0,
            "rate_limit_hit_rate": 2.0,
            "cache_hit_rate": 80.0
        }
        
        recommendations = _generate_performance_recommendations(api_diagnostics, performance_metrics)
        
        assert any("High retry rate detected" in rec for rec in recommendations)
    
    def test_generate_performance_recommendations_excellent_performance(self):
        """Test recommendations for excellent performance."""
        api_diagnostics = {"average_response_time": 0.3, "requests_per_hour": 3000}
        performance_metrics = {
            "success_rate": 99.0,
            "retry_rate": 2.0,
            "rate_limit_hit_rate": 1.0,
            "cache_hit_rate": 85.0
        }
        
        recommendations = _generate_performance_recommendations(api_diagnostics, performance_metrics)
        
        assert any("Performance looks good!" in rec for rec in recommendations)


class TestQueryContactsByCustomField:
    """Test custom field query functionality."""
    
    @pytest.mark.asyncio
    async def test_query_contacts_by_custom_field_success(self):
        """Test successful custom field query."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        # Mock API response
        mock_contacts = [
            {"id": 123, "custom_fields": [{"id": 7, "content": "Engineering"}]},
            {"id": 456, "custom_fields": [{"id": 7, "content": "Sales"}]}
        ]
        mock_api_client.get_contacts.return_value = {"contacts": mock_contacts}
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                with patch('src.utils.contact_utils.get_custom_field_value') as mock_get_field:
                    with patch('src.utils.contact_utils.format_contact_data') as mock_format:
                        # First contact matches, second doesn't
                        mock_get_field.side_effect = ["Engineering", "Sales"]
                        mock_format.side_effect = lambda x: x  # Identity function
                        
                        result = await query_contacts_by_custom_field(
                            context, "7", "Engineering", "equals", limit=200
                        )
                        
                        assert len(result) == 1
                        assert result[0]["id"] == 123
                        mock_cache_manager.set.assert_called_once()  # Result should be cached
    
    @pytest.mark.asyncio
    async def test_query_contacts_by_custom_field_exception(self):
        """Test custom field query with exception."""
        context = Context()
        mock_api_client = AsyncMock()
        mock_api_client.get_contacts.side_effect = Exception("API Error")
        mock_cache_manager = AsyncMock()
        
        # Ensure cache miss to force API call
        mock_cache_manager.get.return_value = None
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            with patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
                with pytest.raises(Exception, match="API Error"):
                    await query_contacts_by_custom_field(context, "7", "Test", "equals")