"""
Integration test to restore the 49%+ coverage we had before.

Uses the same approach as the working comprehensive integration tests
by importing directly from src.mcp.tools rather than individual modules.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Import from the main tools module like the working tests did
from src.mcp.tools import (
    list_contacts, get_tags, search_contacts_by_email, search_contacts_by_name,
    get_contact_details, apply_tags_to_contacts, remove_tags_from_contacts,
    query_contacts_optimized, analyze_query_performance, get_api_diagnostics,
    intersect_id_lists, query_contacts_by_custom_field, set_custom_field_values,
    create_tag, get_tag_details, modify_tags, get_available_tools, get_tool_by_name
)
from src.utils.contact_utils import (
    get_custom_field_value, format_contact_data, process_contact_include_fields,
    get_primary_email, get_full_name, get_tag_ids, format_contact_summary
)
from src.utils.filter_utils import (
    apply_complex_filters, filter_by_name_pattern, evaluate_filter_condition,
    get_nested_value, parse_date_value
)


class TestRestoreCoverage:
    """Integration tests to restore the 49%+ coverage."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        try:
            Path(db_path).unlink()
        except FileNotFoundError:
            pass
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context for tool execution."""
        return MagicMock()
    
    @pytest.fixture
    def comprehensive_contacts(self):
        """Comprehensive contact data for testing."""
        return [
            {
                "id": 1, "given_name": "John", "family_name": "Doe",
                "email_addresses": [
                    {"email": "john@example.com", "field": "EMAIL1"},
                    {"email": "j.doe@work.com", "field": "EMAIL2"}
                ],
                "tag_ids": [10, 20, 30],
                "custom_fields": [
                    {"id": 7, "content": "VIP"},
                    {"id": 8, "content": "Premium"},
                    {"id": 9, "content": "Gold"}
                ],
                "date_created": "2024-01-15T10:30:00Z",
                "last_updated": "2024-01-20T14:45:00Z"
            },
            {
                "id": 2, "given_name": "Jane", "family_name": "Smith",
                "email_addresses": [{"email": "jane@company.com", "field": "EMAIL1"}],
                "tag_ids": [10, 40],
                "custom_fields": [{"id": 7, "content": "Regular"}],
                "date_created": "2024-01-16T11:30:00Z",
                "last_updated": "2024-01-21T09:15:00Z"
            },
            {
                "id": 3, "given_name": "Bob", "family_name": "Johnson",
                "email_addresses": [{"email": "bob@personal.net", "field": "EMAIL1"}],
                "tag_ids": [20, 50],
                "custom_fields": [],
                "date_created": "2024-01-17T09:15:00Z",
                "last_updated": "2024-01-22T16:30:00Z"
            },
            {
                "id": 4, "given_name": "Alice", "family_name": "Wilson",
                "email_addresses": [{"email": "alice@startup.io", "field": "EMAIL1"}],
                "tag_ids": [30, 60],
                "custom_fields": [{"id": 8, "content": "Enterprise"}],
                "date_created": "2024-01-18T13:20:00Z",
                "last_updated": "2024-01-23T11:45:00Z"
            }
        ]
    
    @pytest.fixture
    def comprehensive_tags(self):
        """Comprehensive tag data for testing."""
        return [
            {"id": 10, "name": "Customer", "description": "Customer tag", "category": {"id": 1, "name": "Status"}},
            {"id": 20, "name": "VIP", "description": "VIP customer", "category": {"id": 1, "name": "Status"}},
            {"id": 30, "name": "Newsletter", "description": "Newsletter subscriber", "category": {"id": 2, "name": "Marketing"}},
            {"id": 40, "name": "Lead", "description": "Sales lead", "category": {"id": 3, "name": "Sales"}},
            {"id": 50, "name": "Partner", "description": "Business partner", "category": {"id": 4, "name": "Business"}},
            {"id": 60, "name": "Enterprise", "description": "Enterprise customer", "category": {"id": 1, "name": "Status"}}
        ]
    
    @pytest.mark.asyncio
    async def test_complete_contact_workflow_integration(self, mock_context, comprehensive_contacts):
        """Test complete contact workflow integration like the working test."""
        # Mock the get_api_client and get_cache_manager functions
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                # Setup API client mock
                mock_api = AsyncMock()
                mock_get_api.return_value = mock_api
                
                # Setup cache manager mock
                mock_cache = AsyncMock()
                mock_get_cache.return_value = mock_cache
                
                # Configure API responses
                mock_api.get_contacts.return_value = {"contacts": comprehensive_contacts}
                mock_api.get_contact.side_effect = lambda contact_id: next(
                    (c for c in comprehensive_contacts if c["id"] == int(contact_id)), None
                )
                mock_api.update_contact_custom_field.return_value = {"success": True}
                
                # Configure cache behavior
                mock_cache.get.return_value = None  # Always cache miss for full execution
                mock_cache.set = AsyncMock()
                mock_cache.invalidate_contacts = AsyncMock()
                
                # Test list_contacts
                contacts = await list_contacts(mock_context, limit=50, offset=0)
                assert len(contacts) == 4
                assert contacts[0]["given_name"] == "John"
                
                # Test search functions
                email_results = await search_contacts_by_email(mock_context, "john@example.com")
                assert len(email_results) == 4
                
                name_results = await search_contacts_by_name(mock_context, "Jane")
                assert len(name_results) == 4
                
                # Test get_contact_details
                contact_details = await get_contact_details(mock_context, "1")
                assert contact_details["id"] == 1
                assert contact_details["given_name"] == "John"
                
                # Test set_custom_field_values
                update_result = await set_custom_field_values(mock_context, ["1", "2"], "7", "Updated")
                assert update_result["success"] is True
                assert update_result["updated_count"] == 2
    
    @pytest.mark.asyncio 
    async def test_complete_tag_workflow_integration(self, mock_context, comprehensive_tags):
        """Test complete tag workflow integration."""
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                # Setup mocks
                mock_api = AsyncMock()
                mock_cache = AsyncMock()
                mock_get_api.return_value = mock_api
                mock_get_cache.return_value = mock_cache
                
                # Configure API responses
                mock_api.get_tags.return_value = {"tags": comprehensive_tags}
                mock_api.get_tag.side_effect = lambda tag_id: next(
                    (t for t in comprehensive_tags if t["id"] == int(tag_id)), None
                )
                mock_api.create_tag.return_value = {"id": 70, "name": "Special Offer", "description": "Special offer tag"}
                
                # Configure cache
                mock_cache.get.return_value = None
                mock_cache.set = AsyncMock()
                mock_cache.invalidate_pattern = AsyncMock()
                
                # Test get_tags
                tags = await get_tags(mock_context, include_categories=True)
                assert len(tags) == 6
                assert tags[0]["name"] == "Customer"
                
                # Test get_tag_details
                tag_details = await get_tag_details(mock_context, "10")
                assert tag_details["id"] == 10
                assert tag_details["name"] == "Customer"
                
                # Test create_tag
                new_tag = await create_tag(mock_context, "Special Offer", "Special offer tag", "2")
                assert new_tag["success"] is True
                assert new_tag["tag"]["id"] == 70
                
                # Test apply_tags_to_contacts
                apply_result = await apply_tags_to_contacts(mock_context, ["10", "20"], ["1", "2", "3"])
                assert apply_result["success"] is True
                
                # Test remove_tags_from_contacts
                remove_result = await remove_tags_from_contacts(mock_context, ["30"], ["1", "2"])
                assert remove_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_advanced_filtering_integration(self, comprehensive_contacts):
        """Test advanced filtering integration."""
        # Test filter utilities with comprehensive data
        filters = [
            {"field": "given_name", "operator": "contains", "value": "o"},
            {"field": "tag_ids", "operator": "contains", "value": 10}
        ]
        
        filtered_contacts = apply_complex_filters(comprehensive_contacts, filters)
        assert len(filtered_contacts) == 2  # John and Bob have 'o' in name, John has tag 10
        
        # Test name pattern filtering
        name_items = [{"name": f"{c['given_name']} {c['family_name']}"} for c in comprehensive_contacts]
        pattern_results = filter_by_name_pattern(name_items, "*o*")
        assert len(pattern_results) == 3  # John Doe, Bob Johnson, Alice Wilson
        
        # Test nested value extraction
        first_contact = comprehensive_contacts[0]
        email = get_nested_value(first_contact, "email_addresses.0.email")
        assert email == "john@example.com"
        
        tag_id = get_nested_value(first_contact, "tag_ids.0")
        assert tag_id == 10
        
        # Test date parsing
        date_str = "2024-01-15T10:30:00Z"
        parsed_date = parse_date_value(date_str)
        assert parsed_date.year == 2024
        assert parsed_date.month == 1
        assert parsed_date.day == 15
    
    @pytest.mark.asyncio
    async def test_custom_field_operations_integration(self, mock_context, comprehensive_contacts):
        """Test custom field operations integration."""
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                # Setup mocks
                mock_api = AsyncMock()
                mock_cache = AsyncMock()
                mock_get_api.return_value = mock_api
                mock_get_cache.return_value = mock_cache
                
                # Configure responses for custom field queries
                vip_contacts = [c for c in comprehensive_contacts if 
                              any(cf.get("content") == "VIP" for cf in c.get("custom_fields", []))]
                
                mock_api.get_contacts.return_value = {"contacts": vip_contacts}
                mock_cache.get.return_value = None
                mock_cache.set = AsyncMock()
                
                # Test query_contacts_by_custom_field
                results = await query_contacts_by_custom_field(mock_context, "7", "VIP")
                assert results["success"] is True
                assert len(results["contacts"]) == 1
                assert results["contacts"][0]["given_name"] == "John"
    
    @pytest.mark.asyncio
    async def test_performance_analysis_integration(self, mock_context):
        """Test performance analysis integration."""
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                mock_api = AsyncMock()
                mock_cache = AsyncMock()
                mock_get_api.return_value = mock_api
                mock_get_cache.return_value = mock_cache
                
                # Test analyze_query_performance
                filters = [
                    {"field": "email", "operator": "=", "value": "john@example.com"},
                    {"field": "given_name", "operator": "contains", "value": "John"},
                    {"field": "custom_field_7", "operator": "=", "value": "VIP"}
                ]
                
                analysis = await analyze_query_performance(mock_context, filters, "contact")
                assert analysis["success"] is True
                assert "performance_rating" in analysis
                assert "estimated_response_time_ms" in analysis
                assert "optimization_strategy" in analysis
    
    @pytest.mark.asyncio
    async def test_diagnostics_and_monitoring_integration(self, mock_context):
        """Test diagnostics and monitoring integration."""
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                mock_api = AsyncMock()
                mock_cache = AsyncMock()
                mock_get_api.return_value = mock_api
                mock_get_cache.return_value = mock_cache
                
                # Configure API diagnostics
                mock_api.get_diagnostics.return_value = {
                    "total_requests": 25,
                    "successful_requests": 23,
                    "failed_requests": 2,
                    "average_response_time_ms": 150.5
                }
                
                # Configure cache stats
                mock_cache.get_stats.return_value = {
                    "total_entries": 50,
                    "memory_usage_mb": 2.5,
                    "hit_count": 30,
                    "miss_count": 20,
                    "hit_rate": 0.6
                }
                
                # Test get_api_diagnostics
                diagnostics = await get_api_diagnostics(mock_context)
                assert diagnostics["success"] is True
                assert "api_metrics" in diagnostics
                assert "cache_metrics" in diagnostics
                assert diagnostics["api_metrics"]["total_requests"] == 25
                assert diagnostics["cache_metrics"]["total_entries"] == 50
    
    def test_utility_functions_comprehensive_integration(self, comprehensive_contacts):
        """Test utility functions comprehensive integration."""
        # Test contact utilities with all contacts
        for contact in comprehensive_contacts:
            # Test custom field extraction
            if contact.get("custom_fields"):
                for field in contact["custom_fields"]:
                    value = get_custom_field_value(contact, str(field["id"]))
                    assert value == field["content"]
            
            # Test primary email extraction
            email = get_primary_email(contact)
            if contact.get("email_addresses"):
                assert email == contact["email_addresses"][0]["email"]
            else:
                assert email == ""
            
            # Test full name construction
            full_name = get_full_name(contact)
            expected_name = f"{contact['given_name']} {contact['family_name']}"
            assert full_name == expected_name
            
            # Test tag IDs
            tag_ids = get_tag_ids(contact)
            assert tag_ids == contact.get("tag_ids", [])
            
            # Test contact formatting
            formatted = format_contact_data(contact)
            assert formatted["id"] == contact["id"]
            assert formatted["given_name"] == contact["given_name"]
            
            # Test contact summary
            summary = format_contact_summary(contact)
            assert isinstance(summary, str)
            assert contact["given_name"] in summary
            
            # Test include fields processing
            include_fields = ["email_addresses", "custom_fields", "tag_ids"]
            processed = process_contact_include_fields(contact, include_fields)
            for field in include_fields:
                if field in contact:
                    assert field in processed
                    assert processed[field] == contact[field]
    
    def test_tools_module_integration(self):
        """Test tools module integration."""
        # Test get_available_tools
        tools = get_available_tools()
        assert isinstance(tools, list)
        assert len(tools) > 10
        
        # Verify tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert "parameters" in tool
            assert callable(tool["function"])
        
        # Test get_tool_by_name
        if tools:
            first_tool = tools[0]
            found_tool = get_tool_by_name(first_tool["name"])
            assert found_tool is not None
            assert found_tool["name"] == first_tool["name"]
        
        # Test with non-existent tool
        assert get_tool_by_name("nonexistent_tool") is None
    
    @pytest.mark.asyncio
    async def test_optimized_queries_integration(self, mock_context, comprehensive_contacts):
        """Test optimized queries integration."""
        with patch('src.mcp.tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tools.get_cache_manager') as mock_get_cache:
                mock_api = AsyncMock()
                mock_cache = AsyncMock()
                mock_get_api.return_value = mock_api
                mock_get_cache.return_value = mock_cache
                
                # Configure responses
                mock_api.get_contacts.return_value = {"contacts": comprehensive_contacts}
                mock_cache.get.return_value = None
                mock_cache.set = AsyncMock()
                
                # Test query_contacts_optimized
                filters = [{"field": "given_name", "operator": "=", "value": "John"}]
                
                result = await query_contacts_optimized(mock_context, filters, limit=50)
                assert result["success"] is True
                assert "contacts" in result
                assert "query_metrics" in result
                assert len(result["contacts"]) == 4
    
    @pytest.mark.asyncio
    async def test_intersect_id_lists_integration(self, mock_context):
        """Test intersect_id_lists integration."""
        # Test with overlapping lists
        list1 = ["1", "2", "3", "4"]
        list2 = ["2", "3", "4", "5"]
        list3 = ["3", "4", "5", "6"]
        
        result = await intersect_id_lists(mock_context, [list1, list2, list3])
        assert result["success"] is True
        assert result["common_ids"] == ["3", "4"]
        assert result["total_lists"] == 3
        assert result["common_count"] == 2
        
        # Test with no overlap
        list_a = ["1", "2"]
        list_b = ["3", "4"]
        
        result_empty = await intersect_id_lists(mock_context, [list_a, list_b])
        assert result_empty["success"] is True
        assert result_empty["common_ids"] == []
        assert result_empty["common_count"] == 0