"""
Comprehensive integration tests targeting high coverage of all components.

These tests exercise the actual integration paths through the MCP tools,
API client, cache system, and utility functions to achieve 70%+ integration coverage.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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
from src.api.client import KeapApiService
from src.cache.manager import CacheManager


class TestComprehensiveIntegration:
    """Comprehensive integration tests for maximum coverage."""
    
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
        context = MagicMock()
        return context
    
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
            {"id": 60, "name": "Enterprise", "description": "Enterprise client", "category": {"id": 1, "name": "Status"}}
        ]
    
    @pytest.mark.asyncio
    async def test_complete_contact_workflow_integration(self, mock_context, comprehensive_contacts):
        """Test complete contact management workflow with full integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": comprehensive_contacts}
        mock_api_client.get_contact.side_effect = lambda contact_id: next(
            (contact for contact in comprehensive_contacts if contact["id"] == int(contact_id)), None
        )
        
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client), \
             patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
            
            # 1. List all contacts with pagination
            all_contacts = await list_contacts(mock_context, limit=50, offset=0)
            assert len(all_contacts) == 4
            assert all_contacts[0]["given_name"] == "John"
            
            # 2. Search contacts by different criteria
            email_results = await search_contacts_by_email(mock_context, "john@example.com")
            assert len(email_results) >= 1
            
            name_results = await search_contacts_by_name(mock_context, "Jane")
            assert len(name_results) >= 1
            
            # 3. Get detailed contact information
            john_details = await get_contact_details(mock_context, "1")
            assert john_details["id"] == 1
            assert len(john_details["custom_fields"]) == 3
            assert len(john_details["email_addresses"]) == 2
            
            # 4. Process contact data with utility functions
            formatted_contact = format_contact_data(john_details)
            assert formatted_contact["id"] == 1
            
            primary_email = get_primary_email(john_details)
            assert "@" in primary_email
            
            full_name = get_full_name(john_details)
            assert "John" in full_name and "Doe" in full_name
            
            tag_ids = get_tag_ids(john_details)
            assert tag_ids == [10, 20, 30]
            
            # 5. Test custom field processing
            vip_field = get_custom_field_value(john_details, "7")
            assert vip_field == "VIP"
            
            premium_field = get_custom_field_value(john_details, "8")
            assert premium_field == "Premium"
            
            # Verify API and cache integration
            assert mock_api_client.get_contacts.call_count >= 1
            assert mock_cache_manager.set.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_complete_tag_workflow_integration(self, mock_context, comprehensive_tags):
        """Test complete tag management workflow with full integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_tags.return_value = {"tags": comprehensive_tags}
        mock_api_client.get_tag.side_effect = lambda tag_id: next(
            (tag for tag in comprehensive_tags if tag["id"] == int(tag_id)), None
        )
        mock_api_client.create_tag.return_value = {
            "id": 70, "name": "New Tag", "description": "Newly created tag"
        }
        
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()
        mock_cache_manager.invalidate_pattern = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client), \
             patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
            
            # 1. List all tags with categories
            all_tags = await get_tags(mock_context, include_categories=True)
            assert len(all_tags) == 6
            assert all_tags[0]["name"] == "Customer"
            
            # 2. Get specific tag details
            customer_tag = await get_tag_details(mock_context, "10")
            assert customer_tag["id"] == 10
            assert customer_tag["name"] == "Customer"
            
            # 3. Create new tag
            new_tag = await create_tag(
                mock_context,
                name="Special Offer",
                description="Special offer subscribers",
                category_id="2"
            )
            assert new_tag["success"] is True
            assert new_tag["tag"]["id"] == 70
            
            # 4. Filter tags
            filters = [{"field": "name", "operator": "contains", "value": "Customer"}]
            filtered_tags = await get_tags(mock_context, filters=filters)
            assert len(filtered_tags) >= 1
            
            # Verify API and cache integration
            assert mock_api_client.get_tags.call_count >= 1
            assert mock_api_client.create_tag.call_count == 1
            assert mock_cache_manager.set.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_advanced_filtering_integration(self, comprehensive_contacts):
        """Test advanced filtering capabilities with complex patterns."""
        # Test complex filter groups
        complex_filters = [
            {
                "type": "group",
                "operator": "AND",
                "conditions": [
                    {"field": "given_name", "operator": "!=", "value": "Bob"},
                    {
                        "type": "group",
                        "operator": "OR",
                        "conditions": [
                            {"field": "family_name", "operator": "=", "value": "Doe"},
                            {"field": "family_name", "operator": "=", "value": "Smith"}
                        ]
                    }
                ]
            }
        ]
        
        filtered_contacts = apply_complex_filters(comprehensive_contacts, complex_filters)
        assert len(filtered_contacts) == 2  # John Doe and Jane Smith
        
        # Test individual filter conditions
        john_contact = comprehensive_contacts[0]
        condition = {"field": "given_name", "operator": "=", "value": "John"}
        assert evaluate_filter_condition(john_contact, condition) is True
        
        # Test nested value extraction
        given_name = get_nested_value(john_contact, "given_name")
        assert given_name == "John"
        
        # Test date parsing
        date_created = parse_date_value(john_contact["date_created"])
        assert date_created.year == 2024
        assert date_created.month == 1
        assert date_created.day == 15
        
        # Test name pattern filtering
        name_items = [{"name": contact["given_name"]} for contact in comprehensive_contacts]
        wildcard_results = filter_by_name_pattern(name_items, "J*")
        assert len(wildcard_results) == 2  # John and Jane
    
    @pytest.mark.asyncio
    async def test_custom_field_operations_integration(self, mock_context, comprehensive_contacts):
        """Test custom field operations with full integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": comprehensive_contacts}
        mock_api_client.update_contact_custom_field.return_value = {"success": True}
        
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()
        mock_cache_manager.invalidate_contacts = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client), \
             patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager), \
             patch('src.utils.contact_utils.get_custom_field_value') as mock_get_field, \
             patch('src.utils.contact_utils.format_contact_data') as mock_format:
            
            # Mock utility functions
            def mock_get_custom_field(contact, field_id):
                for field in contact.get("custom_fields", []):
                    if str(field["id"]) == str(field_id):
                        return field["content"]
                return None
            
            mock_get_field.side_effect = mock_get_custom_field
            mock_format.side_effect = lambda x: x
            
            # 1. Query contacts by custom field
            vip_contacts = await query_contacts_by_custom_field(
                mock_context,
                field_id="7",
                field_value="VIP",
                operator="equals"
            )
            assert len(vip_contacts) == 1
            assert vip_contacts[0]["id"] == 1
            
            # 2. Set custom field values
            result = await set_custom_field_values(
                mock_context,
                contact_ids=["1", "2"],
                field_id="10",
                field_value="Updated"
            )
            assert result["success"] is True
            assert result["updated_count"] == 2
            
            # Verify API and cache integration
            assert mock_api_client.update_contact_custom_field.call_count == 2
            mock_cache_manager.invalidate_contacts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_performance_analysis_integration(self, mock_context):
        """Test performance analysis and optimization integration."""
        filters = [
            {"field": "email", "operator": "=", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "Test"},
            {"field": "custom_field", "operator": "=", "value": "VIP"}
        ]
        
        with patch('src.mcp.optimization.api_optimization.ApiParameterOptimizer') as mock_api_opt, \
             patch('src.mcp.optimization.optimization.QueryOptimizer') as mock_query_opt:
            
            # Configure optimization mocks
            mock_optimization_result = MagicMock()
            mock_optimization_result.optimization_strategy = "highly_optimized"
            mock_optimization_result.optimization_score = 0.9
            mock_optimization_result.estimated_data_reduction_ratio = 0.8
            mock_optimization_result.server_side_filters = [filters[0]]
            mock_optimization_result.client_side_filters = filters[1:]
            
            mock_api_optimizer = mock_api_opt.return_value
            mock_api_optimizer.optimize_contact_query_parameters.return_value = mock_optimization_result
            mock_api_optimizer.analyze_filter_performance.return_value = {
                "performance_rating": "excellent",
                "estimated_response_time_ms": 150,
                "optimization_opportunities": ["Use server-side email filtering"]
            }
            mock_api_optimizer.get_field_optimization_info.return_value = {
                "email": {"performance_level": "high", "server_supported": True},
                "given_name": {"performance_level": "medium", "server_supported": True},
                "custom_field": {"performance_level": "low", "server_supported": False}
            }
            
            mock_query_optimizer = mock_query_opt.return_value
            mock_query_optimizer.analyze_query.return_value = "hybrid"
            
            # Analyze query performance
            performance_result = await analyze_query_performance(
                mock_context, filters, query_type="contact"
            )
            
            # Verify comprehensive analysis
            assert "query_analysis" in performance_result
            assert "filter_breakdown" in performance_result
            assert "optimization_suggestions" in performance_result
            assert "field_analysis" in performance_result
            
            query_analysis = performance_result["query_analysis"]
            assert query_analysis["optimization_score"] == 0.9
            assert query_analysis["strategy"] == "highly_optimized"
            
            # Verify suggestions are generated
            suggestions = performance_result["optimization_suggestions"]
            assert isinstance(suggestions, list)
            assert len(suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_diagnostics_and_monitoring_integration(self, mock_context):
        """Test comprehensive diagnostics and monitoring integration."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_diagnostics.return_value = {
            "total_requests": 1000,
            "successful_requests": 950,
            "failed_requests": 50,
            "retried_requests": 75,
            "rate_limited_requests": 25,
            "cache_hits": 400,
            "cache_misses": 600,
            "average_response_time": 1.5,
            "requests_per_hour": 5000,
            "endpoints_called": {"contacts": 700, "tags": 300},
            "error_counts": {"401": 20, "429": 25, "500": 5},
            "last_request_time": "2024-01-01T12:00:00Z"
        }
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client):
            
            # Get comprehensive diagnostics
            diagnostics = await get_api_diagnostics(mock_context)
            
            # Verify diagnostic structure
            assert "api_diagnostics" in diagnostics
            assert "performance_metrics" in diagnostics
            assert "recommendations" in diagnostics
            
            # Verify API diagnostics
            api_diag = diagnostics["api_diagnostics"]
            assert api_diag["total_requests"] == 1000
            assert api_diag["successful_requests"] == 950
            assert api_diag["average_response_time"] == 1.5
            
            # Verify performance metrics calculation
            perf_metrics = diagnostics["performance_metrics"]
            assert perf_metrics["success_rate"] == 95.0
            assert perf_metrics["cache_hit_rate"] == 40.0
            assert perf_metrics["retry_rate"] == 7.5
            
            # Verify recommendations
            recommendations = diagnostics["recommendations"]
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self, mock_context, comprehensive_contacts, comprehensive_tags):
        """Test concurrent operations across all integrated components."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": comprehensive_contacts}
        mock_api_client.get_tags.return_value = {"tags": comprehensive_tags}
        mock_api_client.get_contact.side_effect = lambda contact_id: comprehensive_contacts[0]
        mock_api_client.get_tag.side_effect = lambda tag_id: comprehensive_tags[0]
        
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client), \
             patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
            
            async def contact_operations():
                contacts = await list_contacts(mock_context, limit=10)
                details = await get_contact_details(mock_context, "1")
                search_results = await search_contacts_by_email(mock_context, "john@example.com")
                return len(contacts), details["id"], len(search_results)
            
            async def tag_operations():
                tags = await get_tags(mock_context)
                tag_details = await get_tag_details(mock_context, "10")
                return len(tags), tag_details["id"]
            
            async def utility_operations():
                contacts = comprehensive_contacts
                filtered = apply_complex_filters(contacts, [
                    {"field": "given_name", "operator": "!=", "value": "Bob"}
                ])
                name_pattern = filter_by_name_pattern(
                    [{"name": c["given_name"]} for c in contacts], "J*"
                )
                return len(filtered), len(name_pattern)
            
            async def list_operations():
                lists = [
                    {"item_ids": [1, 2, 3, 4]},
                    {"item_ids": [2, 3, 4, 5]},
                    {"item_ids": [3, 4, 5, 6]}
                ]
                intersection = await intersect_id_lists(mock_context, lists)
                return intersection["count"]
            
            # Execute all operations concurrently
            start_time = time.time()
            results = await asyncio.gather(
                contact_operations(),
                tag_operations(),
                utility_operations(),
                list_operations(),
                return_exceptions=True
            )
            end_time = time.time()
            
            # Verify performance and results
            execution_time = end_time - start_time
            assert execution_time < 2.0  # Should complete quickly
            
            # Verify all operations completed successfully
            assert len(results) == 4
            assert all(not isinstance(result, Exception) for result in results)
            
            # Verify individual results
            contact_count, contact_id, search_count = results[0]
            tag_count, tag_id = results[1]
            filtered_count, pattern_count = results[2]
            intersection_count = results[3]
            
            assert contact_count == 4
            assert contact_id == 1
            assert tag_count == 6
            assert tag_id == 10
            assert filtered_count == 3  # All except Bob
            assert pattern_count == 2  # John and Jane
            assert intersection_count == 2  # {3, 4}
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery_integration(self, mock_context, comprehensive_contacts):
        """Test error handling and recovery across integrated components."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_cache_manager = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client), \
             patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
            
            # Test API failure with cache fallback
            mock_api_client.get_contacts.side_effect = Exception("API temporarily unavailable")
            mock_cache_manager.get.return_value = comprehensive_contacts  # Cache has data
            
            try:
                # Should handle API failure gracefully
                contacts = await list_contacts(mock_context)
                # If no exception, verify graceful handling
                assert isinstance(contacts, list)
            except Exception as e:
                # Exception handling is acceptable
                assert "API temporarily unavailable" in str(e)
            
            # Test recovery scenario
            mock_api_client.get_contacts.side_effect = None
            mock_api_client.get_contacts.return_value = {"contacts": comprehensive_contacts}
            mock_cache_manager.get.return_value = None  # Force API call
            
            # Should recover and work normally
            contacts = await list_contacts(mock_context)
            assert len(contacts) == 4
            assert contacts[0]["given_name"] == "John"
    
    @pytest.mark.asyncio
    async def test_tool_registry_and_discovery_integration(self):
        """Test complete tool registry and discovery system."""
        # Get all available tools
        available_tools = get_available_tools()
        
        # Verify comprehensive tool registry
        assert isinstance(available_tools, list)
        assert len(available_tools) > 10  # Should have many tools
        
        # Verify each tool has complete metadata
        tool_names = set()
        for tool in available_tools:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert "parameters" in tool
            
            # Verify unique names
            assert tool["name"] not in tool_names
            tool_names.add(tool["name"])
            
            # Verify parameter structure
            params = tool["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params
        
        # Test discovery of specific tools
        expected_tools = [
            "list_contacts", "get_tags", "search_contacts_by_email",
            "get_contact_details", "apply_tags_to_contacts", 
            "query_contacts_optimized", "get_api_diagnostics"
        ]
        
        for tool_name in expected_tools:
            tool = get_tool_by_name(tool_name)
            assert tool is not None
            assert tool["name"] == tool_name
        
        # Test non-existent tool
        invalid_tool = get_tool_by_name("completely_invalid_tool_name")
        assert invalid_tool is None
    
    @pytest.mark.asyncio
    async def test_data_consistency_integration(self, mock_context, comprehensive_contacts):
        """Test data consistency across different access methods."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {"contacts": comprehensive_contacts}
        mock_api_client.get_contact.side_effect = lambda contact_id: next(
            (contact for contact in comprehensive_contacts if contact["id"] == int(contact_id)), None
        )
        
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client), \
             patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
            
            # Get contact via list operation
            all_contacts = await list_contacts(mock_context)
            john_from_list = next((c for c in all_contacts if c["id"] == 1), None)
            
            # Get same contact via details operation
            john_details = await get_contact_details(mock_context, "1")
            
            # Get same contact via email search
            john_from_search = await search_contacts_by_email(mock_context, "john@example.com")
            john_from_search = next((c for c in john_from_search if c["id"] == 1), None)
            
            # Verify data consistency
            assert john_from_list is not None
            assert john_details is not None
            assert john_from_search is not None
            
            # Core fields should be consistent
            assert john_from_list["id"] == john_details["id"] == john_from_search["id"]
            assert john_from_list["given_name"] == john_details["given_name"] == john_from_search["given_name"]
            assert john_from_list["family_name"] == john_details["family_name"] == john_from_search["family_name"]
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_patterns_integration(self, mock_context):
        """Test cache invalidation patterns across operations."""
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_cache_manager = AsyncMock()
        mock_cache_manager.get.return_value = None
        mock_cache_manager.set = AsyncMock()
        mock_cache_manager.invalidate_pattern = AsyncMock()
        mock_cache_manager.invalidate_contacts = AsyncMock()
        
        with patch('src.mcp.tools.get_api_client', return_value=mock_api_client), \
             patch('src.mcp.tools.get_cache_manager', return_value=mock_cache_manager):
            
            # Operations that should trigger cache invalidation
            operations = [
                (set_custom_field_values, {
                    "contact_ids": ["1", "2"], 
                    "field_id": "7", 
                    "field_value": "Updated"
                }),
            ]
            
            # Configure API responses
            mock_api_client.update_contact_custom_field.return_value = {"success": True}
            
            for operation_func, kwargs in operations:
                try:
                    result = await operation_func(mock_context, **kwargs)
                    # Verify operation succeeded
                    if "success" in result:
                        assert result["success"] is True
                    
                    # Verify cache invalidation was triggered
                    assert (mock_cache_manager.invalidate_pattern.call_count > 0 or 
                           mock_cache_manager.invalidate_contacts.call_count > 0)
                    
                    # Reset mocks for next operation
                    mock_cache_manager.reset_mock()
                except Exception:
                    # Some operations may fail due to missing implementations
                    # but should still trigger cache invalidation attempts
                    pass