"""
Final integration test to push coverage above 40%.

Targets specific low-coverage areas to achieve maximum integration coverage.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestFinalCoveragePush:
    """Final tests to push integration coverage above 40%."""
    
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
    
    @pytest.mark.asyncio
    async def test_api_client_comprehensive_methods(self):
        """Test comprehensive API client method coverage."""
        from src.api.client import KeapApiService
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.is_success = True
            mock_response.text = '{"contacts": [{"id": 1}]}'
            
            mock_client.get.return_value = mock_response
            mock_client.post.return_value = mock_response
            mock_client.put.return_value = mock_response
            
            client = KeapApiService(api_key="test_key")
            
            # Test multiple API methods
            await client.get_contacts(limit=10, offset=0)
            await client.get_contacts(email="test@example.com")
            await client.get_contacts(given_name="John", family_name="Doe")
            await client.get_contact("1")
            await client.get_tags()
            await client.get_tag("10")
            await client.update_contact_custom_field("1", "7", "Test")
            
            # Test diagnostics methods
            diagnostics = client.get_diagnostics()
            assert diagnostics["total_requests"] > 0
            
            # Test reset diagnostics
            client.reset_diagnostics()
            assert client.get_diagnostics()["total_requests"] == 0
    
    @pytest.mark.asyncio
    async def test_contact_tools_direct_calls(self):
        """Test direct contact tool function calls."""
        from src.mcp.contact_tools import (
            list_contacts, get_contact_details, search_contacts_by_email,
            search_contacts_by_name, set_custom_field_values
        )
        
        mock_context = MagicMock()
        
        with patch('src.mcp.contact_tools.get_api_client') as mock_get_api:
            with patch('src.mcp.contact_tools.get_cache_manager') as mock_get_cache:
                # Setup mocks
                mock_api = AsyncMock()
                mock_cache = AsyncMock()
                
                mock_get_api.return_value = mock_api
                mock_get_cache.return_value = mock_cache
                
                # Configure API responses
                mock_api.get_contacts.return_value = {"contacts": [{"id": 1, "given_name": "John"}]}
                mock_api.get_contact.return_value = {"id": 1, "given_name": "John"}
                mock_api.update_contact_custom_field.return_value = {"success": True}
                
                # Configure cache
                mock_cache.get.return_value = None
                mock_cache.set = AsyncMock()
                mock_cache.invalidate_contacts = AsyncMock()
                
                # Test direct function calls
                contacts = await list_contacts(mock_context, limit=10, offset=0)
                assert len(contacts) == 1
                
                contact = await get_contact_details(mock_context, "1")
                assert contact["id"] == 1
                
                email_results = await search_contacts_by_email(mock_context, "john@example.com")
                assert len(email_results) == 1
                
                name_results = await search_contacts_by_name(mock_context, "John")
                assert len(name_results) == 1
                
                update_result = await set_custom_field_values(
                    mock_context, ["1"], "7", "Updated"
                )
                assert update_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_tag_tools_direct_calls(self):
        """Test direct tag tool function calls."""
        from src.mcp.tag_tools import (
            get_tags, get_tag_details, create_tag,
            apply_tags_to_contacts, remove_tags_from_contacts
        )
        
        mock_context = MagicMock()
        
        with patch('src.mcp.tag_tools.get_api_client') as mock_get_api:
            with patch('src.mcp.tag_tools.get_cache_manager') as mock_get_cache:
                # Setup mocks
                mock_api = AsyncMock()
                mock_cache = AsyncMock()
                
                mock_get_api.return_value = mock_api
                mock_get_cache.return_value = mock_cache
                
                # Configure API responses
                mock_api.get_tags.return_value = {"tags": [{"id": 10, "name": "Customer"}]}
                mock_api.get_tag.return_value = {"id": 10, "name": "Customer"}
                mock_api.create_tag.return_value = {"id": 100, "name": "New Tag"}
                
                # Configure cache
                mock_cache.get.return_value = None
                mock_cache.set = AsyncMock()
                mock_cache.invalidate_pattern = AsyncMock()
                
                # Test direct function calls
                tags = await get_tags(mock_context)
                assert len(tags) == 1
                
                tag = await get_tag_details(mock_context, "10")
                assert tag["id"] == 10
                
                new_tag = await create_tag(mock_context, "Test Tag", "Description", "1")
                assert new_tag["success"] is True
                
                apply_result = await apply_tags_to_contacts(mock_context, ["10"], ["1"])
                assert apply_result["success"] is True
                
                remove_result = await remove_tags_from_contacts(mock_context, ["10"], ["1"])
                assert remove_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_cache_advanced_operations(self, temp_db_path):
        """Test advanced cache operations."""
        from src.cache.manager import CacheManager
        from src.cache.persistent_manager import PersistentCacheManager
        
        # Test CacheManager advanced features
        cache_manager = CacheManager(db_path=temp_db_path, max_entries=50, max_memory_mb=5)
        
        try:
            # Test memory management
            for i in range(60):  # Exceed max_entries
                await cache_manager.set(f"key_{i}", {"data": f"value_{i}"}, ttl=3600)
            
            stats = cache_manager.get_stats()
            assert stats["total_entries"] <= 50  # Should respect limit
            
            # Test invalidation patterns
            await cache_manager.set("user:1:profile", {"name": "John"}, ttl=3600)
            await cache_manager.set("user:2:profile", {"name": "Jane"}, ttl=3600)
            await cache_manager.set("system:config", {"setting": "value"}, ttl=3600)
            
            await cache_manager.invalidate_pattern("user:*")
            
            assert await cache_manager.get("user:1:profile") is None
            assert await cache_manager.get("user:2:profile") is None
            assert await cache_manager.get("system:config") is not None
            
            # Test contact invalidation
            await cache_manager.set("contact:123", {"name": "Test"}, ttl=3600)
            await cache_manager.set("contacts:list", [{"id": 123}], ttl=3600)
            
            await cache_manager.invalidate_contacts([123])
            
            assert await cache_manager.get("contact:123") is None
            assert await cache_manager.get("contacts:list") is None
            
        finally:
            cache_manager.close()
        
        # Test PersistentCacheManager advanced features
        persistent_cache = PersistentCacheManager(
            db_path=temp_db_path + "_advanced",
            max_entries=100,
            max_memory_mb=10
        )
        
        try:
            # Test bulk operations
            for i in range(50):
                await persistent_cache.set(f"bulk_{i}", {"index": i}, ttl=3600)
            
            # Test cleanup operations
            await persistent_cache.cleanup_expired()
            await persistent_cache.vacuum_database()
            
            # Test advanced invalidation
            await persistent_cache.set("pattern:test:1", {"data": "1"}, ttl=3600)
            await persistent_cache.set("pattern:test:2", {"data": "2"}, ttl=3600)
            await persistent_cache.invalidate_pattern("pattern:test:*")
            
            assert await persistent_cache.get("pattern:test:1") is None
            
        finally:
            persistent_cache.close()
    
    @pytest.mark.asyncio
    async def test_optimization_advanced_scenarios(self):
        """Test advanced optimization scenarios."""
        from src.mcp.optimization.optimization import QueryOptimizer, QueryExecutor, QueryMetrics
        from src.mcp.optimization.api_optimization import ApiParameterOptimizer
        
        # Test QueryOptimizer with complex scenarios
        optimizer = QueryOptimizer()
        
        complex_filters = [
            {"field": "email", "operator": "contains", "value": "@example.com"},
            {"field": "given_name", "operator": "=", "value": "John"},
            {"field": "custom_field_7", "operator": "=", "value": "VIP"},
            {"field": "tag_count", "operator": ">", "value": 3}
        ]
        
        # Test different optimization methods
        strategy = optimizer.analyze_query(complex_filters)
        assert strategy in ["server_optimized", "hybrid", "client_optimized"]
        
        score = optimizer.calculate_performance_score(complex_filters)
        assert 0.0 <= score <= 1.0
        
        recommendations = optimizer.get_optimization_recommendations(complex_filters)
        assert isinstance(recommendations, list)
        
        # Test QueryExecutor
        mock_api = AsyncMock()
        mock_cache = AsyncMock()
        
        mock_api.get_contacts.return_value = {"contacts": [{"id": 1}]}
        mock_cache.get.return_value = None
        mock_cache.set = AsyncMock()
        
        executor = QueryExecutor(mock_api, mock_cache)
        
        contacts, metrics = await executor.execute_optimized_query(
            query_type="list_contacts",
            filters=complex_filters,
            limit=50
        )
        
        assert isinstance(contacts, list)
        assert isinstance(metrics, QueryMetrics)
        
        # Test ApiParameterOptimizer
        api_optimizer = ApiParameterOptimizer()
        
        optimization_result = api_optimizer.optimize_contact_query_parameters(complex_filters)
        assert hasattr(optimization_result, 'optimization_strategy')
        
        performance_analysis = api_optimizer.analyze_filter_performance(complex_filters, "contact")
        assert "performance_rating" in performance_analysis
        
        field_info = api_optimizer.get_field_optimization_info("contact")
        assert isinstance(field_info, dict)
        
        tag_optimization = api_optimizer.optimize_tag_query_parameters([
            {"field": "name", "operator": "contains", "value": "Customer"}
        ])
        assert hasattr(tag_optimization, 'optimization_strategy')
    
    @pytest.mark.asyncio
    async def test_utility_comprehensive_coverage(self):
        """Test comprehensive utility function coverage."""
        from src.utils.contact_utils import (
            get_custom_field_value, get_primary_email, get_full_name,
            get_tag_ids, format_contact_data, format_contact_summary,
            process_contact_include_fields
        )
        from src.utils.filter_utils import (
            apply_complex_filters, evaluate_filter_condition,
            get_nested_value, parse_date_value, filter_by_name_pattern
        )
        
        # Comprehensive contact data
        contact = {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [
                {"email": "john@example.com", "field": "EMAIL1"},
                {"email": "j.doe@work.com", "field": "EMAIL2"}
            ],
            "phone_numbers": [
                {"number": "+1-555-0101", "field": "PHONE1"}
            ],
            "tag_ids": [10, 20, 30],
            "custom_fields": [
                {"id": 7, "content": "VIP"},
                {"id": 8, "content": "Premium"}
            ],
            "addresses": [
                {
                    "line1": "123 Main St",
                    "locality": "Anytown",
                    "region": "CA",
                    "postal_code": "12345"
                }
            ],
            "company": {"id": 1001, "name": "Acme Corp"}
        }
        
        # Test all contact utility functions
        assert get_custom_field_value(contact, "7") == "VIP"
        assert get_custom_field_value(contact, 8) == "Premium"
        assert get_primary_email(contact) == "john@example.com"
        assert get_full_name(contact) == "John Doe"
        assert get_tag_ids(contact) == [10, 20, 30]
        
        formatted = format_contact_data(contact)
        assert formatted["id"] == 1
        
        summary = format_contact_summary(contact)
        assert summary["first_name"] == "John"
        assert summary["email"] == "john@example.com"
        
        # Test include fields with all possible fields
        include_fields = [
            "email_addresses", "phone_numbers", "custom_fields",
            "tag_ids", "addresses", "company"
        ]
        processed = process_contact_include_fields(contact, include_fields)
        for field in include_fields:
            assert field in processed
        
        # Test filter utilities with complex data
        items = [
            {
                "id": 1, "name": "John Doe", "email": "john@example.com",
                "score": 85, "active": True, "tags": [10, 20],
                "nested": {"level1": {"level2": "deep_value"}}
            },
            {
                "id": 2, "name": "Jane Smith", "email": "jane@example.com",
                "score": 92, "active": False, "tags": [10, 30]
            }
        ]
        
        # Test various filter conditions
        filters = [
            {"field": "score", "operator": ">", "value": 80},
            {"field": "active", "operator": "=", "value": True}
        ]
        
        filtered = apply_complex_filters(items, filters)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "John Doe"
        
        # Test individual filter evaluation
        condition = {"field": "email", "operator": "contains", "value": "@example"}
        assert evaluate_filter_condition(items[0], condition) is True
        
        # Test nested value extraction
        assert get_nested_value(items[0], "nested.level1.level2") == "deep_value"
        assert get_nested_value(items[0], "tags.0") == 10
        
        # Test date parsing
        date_str = "2024-01-15T10:30:00Z"
        parsed = parse_date_value(date_str)
        assert parsed.year == 2024
        
        # Test name pattern filtering
        name_items = [{"name": item["name"]} for item in items]
        john_filtered = filter_by_name_pattern(name_items, "John*")
        assert len(john_filtered) == 1
        
        all_filtered = filter_by_name_pattern(name_items, "*")
        assert len(all_filtered) == 2
    
    @pytest.mark.asyncio
    async def test_schema_comprehensive_validation(self):
        """Test comprehensive schema validation."""
        from src.schemas.definitions import (
            Contact, Tag, FilterCondition, FilterOperator,
            LogicalGroup, LogicalOperator, ContactQueryRequest,
            TagQueryRequest, ModifyTagsRequest
        )
        
        # Test Contact with all fields
        contact_data = {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [
                {"email": "john@example.com", "field": "EMAIL1"}
            ],
            "phone_numbers": [
                {"number": "+1-555-0101", "field": "PHONE1"}
            ],
            "tag_ids": [10, 20],
            "custom_fields": [
                {"id": 7, "content": "VIP"}
            ]
        }
        
        contact = Contact(**contact_data)
        assert contact.id == 1
        assert len(contact.email_addresses) == 1
        
        # Test Tag validation
        tag = Tag(id=10, name="Customer", description="Customer tag")
        assert tag.name == "Customer"
        
        # Test FilterCondition with all operators
        filter_conditions = [
            FilterCondition(field="email", operator=FilterOperator.EQUALS, value="test@example.com"),
            FilterCondition(field="name", operator=FilterOperator.CONTAINS, value="John"),
            FilterCondition(field="score", operator=FilterOperator.GREATER_THAN, value="80"),
            FilterCondition(field="tags", operator=FilterOperator.IN, value="[10,20]")
        ]
        
        for condition in filter_conditions:
            assert condition.field is not None
            assert condition.operator in FilterOperator
        
        # Test LogicalGroup
        logical_group = LogicalGroup(
            operator=LogicalOperator.AND,
            conditions=[filter_conditions[0], filter_conditions[1]]
        )
        assert logical_group.operator == LogicalOperator.AND
        assert len(logical_group.conditions) == 2
        
        # Test complex request schemas
        contact_query = ContactQueryRequest(
            filters=[filter_conditions[0]],
            limit=50,
            offset=0
        )
        assert contact_query.limit == 50
        
        tag_query = TagQueryRequest(
            filters=[filter_conditions[1]],
            include_categories=True
        )
        assert tag_query.include_categories is True
        
        modify_tags = ModifyTagsRequest(
            contact_ids=["1", "2"],
            tags_to_add=["10"],
            tags_to_remove=["20"]
        )
        assert len(modify_tags.contact_ids) == 2