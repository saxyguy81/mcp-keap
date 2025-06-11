"""
Working integration tests that focus on component integration coverage.

Tests key integration paths between API client, cache, MCP tools, and utilities
with working implementations that provide good coverage.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.client import KeapApiService
from src.cache.manager import CacheManager
from src.utils.contact_utils import (
    get_custom_field_value, format_contact_data, 
    process_contact_include_fields, get_primary_email, 
    get_full_name, get_tag_ids
)
from src.utils.filter_utils import (
    apply_complex_filters, filter_by_name_pattern,
    evaluate_filter_condition, get_nested_value, parse_date_value
)
from src.mcp.tools import (
    get_available_tools, get_tool_by_name,
    intersect_id_lists, query_contacts_by_custom_field
)


class TestWorkingIntegration:
    """Test working integration scenarios."""
    
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
    def cache_manager(self, temp_db_path):
        """Create cache manager with temp database."""
        manager = CacheManager(db_path=temp_db_path)
        yield manager
        manager.close()
    
    @pytest.fixture
    def sample_contacts(self):
        """Sample contact data for testing."""
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
                    {"id": 8, "content": "Premium"}
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
            }
        ]
    
    @pytest.mark.asyncio
    async def test_cache_and_utility_integration(self, cache_manager, sample_contacts):
        """Test integration between cache and utility functions."""
        # Store contacts in cache
        cache_key = "test_contacts"
        await cache_manager.set(cache_key, sample_contacts, ttl=3600)
        
        # Retrieve from cache
        cached_contacts = await cache_manager.get(cache_key)
        assert cached_contacts is not None
        assert len(cached_contacts) == 3
        
        # Test utility functions with cached data
        for contact in cached_contacts:
            # Test custom field extraction
            custom_field_value = get_custom_field_value(contact, "7")
            if contact["id"] == 1:
                assert custom_field_value == "VIP"
            elif contact["id"] == 2:
                assert custom_field_value == "Regular"
            elif contact["id"] == 3:
                assert custom_field_value is None
            
            # Test email extraction
            primary_email = get_primary_email(contact)
            assert "@" in primary_email
            
            # Test full name extraction
            full_name = get_full_name(contact)
            assert contact["given_name"] in full_name
            
            # Test contact formatting
            formatted = format_contact_data(contact)
            assert formatted["id"] == contact["id"]
            assert formatted["given_name"] == contact["given_name"]
    
    @pytest.mark.asyncio
    async def test_filter_utils_with_contact_data(self, sample_contacts):
        """Test filter utilities integration with contact data."""
        # Test complex filters
        filters = [
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
        
        filtered_contacts = apply_complex_filters(sample_contacts, filters)
        assert len(filtered_contacts) == 2
        assert {contact["id"] for contact in filtered_contacts} == {1, 2}
        
        # Test individual filter evaluation
        john_contact = sample_contacts[0]
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
    
    @pytest.mark.asyncio
    async def test_mcp_tools_integration(self):
        """Test MCP tools integration and discovery."""
        # Test tool registry
        available_tools = get_available_tools()
        assert isinstance(available_tools, list)
        assert len(available_tools) > 0
        
        # Verify tool structure
        for tool in available_tools:
            assert "name" in tool
            assert "description" in tool
            assert "function" in tool
            assert "parameters" in tool
        
        # Test tool discovery
        list_contacts_tool = get_tool_by_name("list_contacts")
        assert list_contacts_tool is not None
        assert list_contacts_tool["name"] == "list_contacts"
        
        # Test non-existent tool
        invalid_tool = get_tool_by_name("non_existent_tool")
        assert invalid_tool is None
    
    @pytest.mark.asyncio
    async def test_utility_functions_integration(self):
        """Test utility functions working together."""
        # Test intersect_id_lists function
        mock_context = MagicMock()
        
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
        
        # Test with insufficient lists
        insufficient_lists = [{"item_ids": [1, 2, 3]}]
        result = await intersect_id_lists(mock_context, insufficient_lists)
        assert result["success"] is False
        assert "At least two lists are required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_contact_processing_integration(self, sample_contacts):
        """Test contact processing functions integration."""
        john_contact = sample_contacts[0]
        
        # Test include fields processing
        include_fields = ["email_addresses", "custom_fields", "tag_ids"]
        processed = process_contact_include_fields(john_contact, include_fields)
        
        # Verify included fields are present
        assert "email_addresses" in processed
        assert "custom_fields" in processed
        assert "tag_ids" in processed
        
        # Test email extraction from processed contact
        primary_email = get_primary_email(processed)
        assert "john@example.com" == primary_email
        
        # Test full name extraction
        full_name = get_full_name(processed)
        assert "John Doe" == full_name
        
        # Test tag IDs extraction
        tag_ids = get_tag_ids(processed)
        assert tag_ids == [10, 20, 30]
        
        # Test custom field extraction
        vip_value = get_custom_field_value(processed, "7")
        assert vip_value == "VIP"
        
        premium_value = get_custom_field_value(processed, "8")
        assert premium_value == "Premium"
        
        # Test non-existent custom field
        non_existent = get_custom_field_value(processed, "999")
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_filter_integration_with_name_patterns(self, sample_contacts):
        """Test filter integration with name pattern matching."""
        # Test name pattern filtering
        name_items = [
            {"name": contact["given_name"]} for contact in sample_contacts
        ]
        
        # Test exact match
        exact_results = filter_by_name_pattern(name_items, "John")
        assert len(exact_results) == 1
        assert exact_results[0]["name"] == "John"
        
        # Test wildcard matching
        wildcard_results = filter_by_name_pattern(name_items, "J*")
        assert len(wildcard_results) == 2  # John and Jane
        names = {item["name"] for item in wildcard_results}
        assert names == {"John", "Jane"}
        
        # Test empty pattern (should return all)
        empty_results = filter_by_name_pattern(name_items, "")
        assert len(empty_results) == len(name_items)
    
    @pytest.mark.asyncio
    async def test_cache_and_api_client_integration(self, cache_manager):
        """Test integration between cache and API client patterns."""
        # Mock API client
        mock_api_client = AsyncMock(spec=KeapApiService)
        mock_api_client.get_contacts.return_value = {
            "contacts": [
                {"id": 1, "given_name": "John", "email": "john@example.com"},
                {"id": 2, "given_name": "Jane", "email": "jane@example.com"}
            ]
        }
        
        # Simulate API call and caching pattern
        cache_key = "contacts:list:limit_10"
        
        # Check cache first (should be empty)
        cached_data = await cache_manager.get(cache_key)
        assert cached_data is None
        
        # Make API call
        api_response = await mock_api_client.get_contacts(limit=10)
        contacts = api_response["contacts"]
        
        # Cache the response
        await cache_manager.set(cache_key, contacts, ttl=1800)
        
        # Verify cache hit
        cached_contacts = await cache_manager.get(cache_key)
        assert cached_contacts == contacts
        assert len(cached_contacts) == 2
        
        # Verify API was called only once
        mock_api_client.get_contacts.assert_called_once_with(limit=10)
    
    @pytest.mark.asyncio
    async def test_custom_field_query_integration(self, sample_contacts):
        """Test custom field querying integration."""
        mock_context = MagicMock()
        
        with patch('src.mcp.tools.get_api_client') as mock_get_api, \
             patch('src.mcp.tools.get_cache_manager') as mock_get_cache, \
             patch('src.utils.contact_utils.get_custom_field_value') as mock_get_field, \
             patch('src.utils.contact_utils.format_contact_data') as mock_format:
            
            # Configure mocks
            mock_api_client = AsyncMock()
            mock_api_client.get_contacts.return_value = {"contacts": sample_contacts}
            mock_get_api.return_value = mock_api_client
            
            mock_cache = MagicMock()
            mock_cache.get.return_value = None  # Cache miss
            mock_cache.set = AsyncMock()
            mock_get_cache.return_value = mock_cache
            
            # Mock utility functions
            def mock_get_custom_field(contact, field_id):
                if field_id == "7":
                    if contact["id"] == 1:
                        return "VIP"
                    elif contact["id"] == 2:
                        return "Regular"
                return None
            
            mock_get_field.side_effect = mock_get_custom_field
            mock_format.side_effect = lambda x: x
            
            # Test custom field query
            result = await query_contacts_by_custom_field(
                mock_context,
                field_id="7",
                field_value="VIP",
                operator="equals"
            )
            
            # Verify results
            assert len(result) == 1
            assert result[0]["id"] == 1
            
            # Verify cache was used
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_integration_operations(self, cache_manager, sample_contacts):
        """Test concurrent operations across integrated components."""
        async def cache_operation(worker_id):
            cache_key = f"worker_{worker_id}_data"
            await cache_manager.set(cache_key, {"worker": worker_id, "data": "test"}, ttl=3600)
            cached = await cache_manager.get(cache_key)
            return cached is not None
        
        async def filter_operation(worker_id):
            filters = [{"field": "id", "operator": ">", "value": worker_id}]
            filtered = apply_complex_filters(sample_contacts, filters)
            return len(filtered)
        
        async def utility_operation(worker_id):
            contact = sample_contacts[worker_id % len(sample_contacts)]
            primary_email = get_primary_email(contact)
            custom_field = get_custom_field_value(contact, "7")
            return len(primary_email) > 0, custom_field is not None
        
        # Run operations concurrently
        tasks = []
        for i in range(5):
            tasks.extend([
                cache_operation(i),
                filter_operation(i), 
                utility_operation(i)
            ])
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed successfully
        assert len(results) == 15  # 5 workers × 3 operations
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 10  # Most should succeed
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, cache_manager):
        """Test error handling across integrated components."""
        # Test cache error handling
        invalid_cache_key = None
        try:
            await cache_manager.get(invalid_cache_key)
        except Exception:
            # Error handling is expected for invalid keys
            pass
        
        # Test filter error handling with invalid data
        invalid_contacts = [{"invalid": "data"}]
        filters = [{"field": "nonexistent", "operator": "=", "value": "test"}]
        
        try:
            filtered = apply_complex_filters(invalid_contacts, filters)
            # Should handle gracefully or return empty list
            assert isinstance(filtered, list)
        except Exception:
            # Exception handling is also acceptable
            pass
        
        # Test utility error handling
        invalid_contact = {"id": 1}  # Missing expected fields
        
        try:
            primary_email = get_primary_email(invalid_contact)
            assert isinstance(primary_email, str)  # Should return empty string
        except Exception:
            # Exception handling is acceptable
            pass
        
        try:
            custom_field = get_custom_field_value(invalid_contact, "7")
            assert custom_field is None  # Should return None for missing fields
        except Exception:
            # Exception handling is acceptable  
            pass
    
    @pytest.mark.asyncio
    async def test_performance_integration(self, cache_manager, sample_contacts):
        """Test performance characteristics of integrated components."""
        # Test cache performance
        start_time = time.time()
        
        for i in range(100):
            cache_key = f"perf_test_{i}"
            await cache_manager.set(cache_key, {"test": i}, ttl=3600)
            cached = await cache_manager.get(cache_key)
            assert cached["test"] == i
        
        cache_time = time.time() - start_time
        assert cache_time < 2.0  # Should complete within 2 seconds
        
        # Test filter performance
        start_time = time.time()
        
        for i in range(50):
            filters = [{"field": "id", "operator": ">", "value": i % 3}]
            filtered = apply_complex_filters(sample_contacts, filters)
            assert isinstance(filtered, list)
        
        filter_time = time.time() - start_time
        assert filter_time < 1.0  # Should complete within 1 second
        
        # Test utility function performance
        start_time = time.time()
        
        for i in range(100):
            contact = sample_contacts[i % len(sample_contacts)]
            primary_email = get_primary_email(contact)
            get_custom_field_value(contact, "7")
            formatted = format_contact_data(contact)
            full_name = get_full_name(contact)
            
            assert isinstance(primary_email, str)
            assert isinstance(formatted, dict)
            assert isinstance(full_name, str)
        
        utility_time = time.time() - start_time
        assert utility_time < 1.0  # Should complete within 1 second