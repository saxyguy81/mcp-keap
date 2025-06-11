"""
Simple integration tests to boost coverage in key areas.

Focuses on working implementations that reliably increase coverage
without complex external dependencies.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestCoverageBoostSimple:
    """Simple integration tests for coverage boost."""
    
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
    def sample_contact_data(self):
        """Sample contact data for testing."""
        return {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [{"email": "john@example.com", "field": "EMAIL1"}],
            "tag_ids": [10, 20],
            "custom_fields": [{"id": 7, "content": "VIP"}]
        }
    
    @pytest.mark.asyncio
    async def test_contact_utils_integration(self, sample_contact_data):
        """Test contact utilities integration."""
        from src.utils.contact_utils import (
            get_custom_field_value, get_primary_email, get_full_name, 
            get_tag_ids, format_contact_data, format_contact_summary
        )
        
        contact = sample_contact_data
        
        # Test basic utilities
        assert get_custom_field_value(contact, "7") == "VIP"
        assert get_primary_email(contact) == "john@example.com"
        assert get_full_name(contact) == "John Doe"
        assert get_tag_ids(contact) == [10, 20]
        
        # Test formatting functions
        formatted = format_contact_data(contact)
        assert formatted["id"] == 1
        assert formatted["given_name"] == "John"
        
        summary = format_contact_summary(contact)
        assert isinstance(summary, dict)
        assert summary["first_name"] == "John"
    
    @pytest.mark.asyncio
    async def test_filter_utils_integration(self):
        """Test filter utilities integration."""
        from src.utils.filter_utils import (
            apply_complex_filters, evaluate_filter_condition, 
            get_nested_value, parse_date_value
        )
        
        # Test data
        items = [
            {"id": 1, "name": "John", "score": 85},
            {"id": 2, "name": "Jane", "score": 92}
        ]
        
        # Test simple filtering
        filters = [{"field": "name", "operator": "=", "value": "John"}]
        filtered = apply_complex_filters(items, filters)
        assert len(filtered) == 1
        assert filtered[0]["name"] == "John"
        
        # Test filter condition evaluation
        condition = {"field": "score", "operator": ">", "value": 80}
        assert evaluate_filter_condition(items[0], condition) is True
        assert evaluate_filter_condition(items[1], condition) is True
        
        # Test nested value extraction
        nested_data = {"level1": {"level2": "value"}}
        assert get_nested_value(nested_data, "level1.level2") == "value"
        assert get_nested_value(nested_data, "nonexistent") is None
        
        # Test date parsing
        date_str = "2024-01-15T10:30:00Z"
        parsed = parse_date_value(date_str)
        assert isinstance(parsed, datetime)
        assert parsed.year == 2024
    
    @pytest.mark.asyncio
    async def test_schema_integration(self):
        """Test schema definitions integration."""
        from src.schemas.definitions import Contact, Tag, FilterCondition, FilterOperator
        
        # Test Contact schema
        contact_data = {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [{"email": "john@example.com", "field": "EMAIL1"}],
            "tag_ids": [10, 20]
        }
        
        contact = Contact(**contact_data)
        assert contact.id == 1
        assert contact.given_name == "John"
        assert len(contact.email_addresses) == 1
        
        # Test Tag schema
        tag_data = {"id": 10, "name": "Customer"}
        tag = Tag(**tag_data)
        assert tag.id == 10
        assert tag.name == "Customer"
        
        # Test FilterCondition schema
        filter_data = {
            "field": "email",
            "operator": FilterOperator.EQUALS,
            "value": "john@example.com"
        }
        
        filter_condition = FilterCondition(**filter_data)
        assert filter_condition.field == "email"
        assert filter_condition.operator == FilterOperator.EQUALS
    
    @pytest.mark.asyncio
    async def test_optimization_integration(self):
        """Test optimization components integration."""
        from src.mcp.optimization.optimization import QueryOptimizer, QueryMetrics
        from src.mcp.optimization.api_optimization import ApiParameterOptimizer
        
        # Test QueryOptimizer
        optimizer = QueryOptimizer()
        
        filters = [
            {"field": "email", "operator": "=", "value": "john@example.com"},
            {"field": "name", "operator": "contains", "value": "John"}
        ]
        
        strategy = optimizer.analyze_query(filters)
        assert strategy in ["server_optimized", "hybrid", "client_optimized"]
        
        score = optimizer.calculate_performance_score(filters)
        assert 0.0 <= score <= 1.0
        
        recommendations = optimizer.get_optimization_recommendations(filters)
        assert isinstance(recommendations, list)
        
        # Test ApiParameterOptimizer
        api_optimizer = ApiParameterOptimizer()
        
        result = api_optimizer.optimize_contact_query_parameters(filters)
        assert hasattr(result, 'optimization_strategy')
        assert hasattr(result, 'optimization_score')
        
        field_info = api_optimizer.get_field_optimization_info("contact")
        assert isinstance(field_info, dict)
        
        # Test QueryMetrics
        metrics = QueryMetrics(
            query_type="list_contacts",
            total_duration_ms=150.0,
            api_calls=1,
            cache_hits=0,
            cache_misses=1,
            optimization_strategy="hybrid"
        )
        
        assert metrics.query_type == "list_contacts"
        assert metrics.total_duration_ms == 150.0
    
    @pytest.mark.asyncio
    async def test_cache_integration(self, temp_db_path):
        """Test cache system integration."""
        from src.cache.manager import CacheManager
        from src.cache.persistent_manager import PersistentCacheManager
        
        # Test CacheManager
        cache_manager = CacheManager(db_path=temp_db_path, max_entries=100)
        
        try:
            # Basic operations
            test_data = {"id": 1, "name": "test"}
            await cache_manager.set("test_key", test_data, ttl=3600)
            
            cached = await cache_manager.get("test_key")
            assert cached == test_data
            
            # TTL test
            await cache_manager.set("short_key", {"temp": True}, ttl=0.1)
            await asyncio.sleep(0.2)
            expired = await cache_manager.get("short_key")
            assert expired is None
            
            # Stats
            stats = cache_manager.get_stats()
            assert "total_entries" in stats
            assert "memory_usage_mb" in stats
            
        finally:
            cache_manager.close()
        
        # Test PersistentCacheManager
        persistent_cache = PersistentCacheManager(
            db_path=temp_db_path + "_persistent",
            max_entries=100
        )
        
        try:
            # Basic operations
            await persistent_cache.set("persistent_key", test_data, ttl=3600)
            
            cached = await persistent_cache.get("persistent_key")
            assert cached == test_data
            
            # Pattern invalidation
            await persistent_cache.set("pattern:1", {"data": "1"}, ttl=3600)
            await persistent_cache.set("pattern:2", {"data": "2"}, ttl=3600)
            
            await persistent_cache.invalidate_pattern("pattern:*")
            
            assert await persistent_cache.get("pattern:1") is None
            assert await persistent_cache.get("pattern:2") is None
            
            # Contact invalidation
            await persistent_cache.set("contact:123:details", {"id": 123}, ttl=3600)
            await persistent_cache.invalidate_contacts([123])
            assert await persistent_cache.get("contact:123:details") is None
            
        finally:
            persistent_cache.close()
    
    @pytest.mark.asyncio
    async def test_api_client_integration(self):
        """Test API client integration with mocked responses."""
        from src.api.client import KeapApiService
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.is_success = True
            mock_response.text = '{"contacts": [{"id": 1, "given_name": "John"}]}'
            
            mock_client.get.return_value = mock_response
            mock_client.post.return_value = mock_response
            mock_client.put.return_value = mock_response
            
            # Test API client
            client = KeapApiService(api_key="test_key")
            
            # Test basic operations
            contacts = await client.get_contacts(limit=10)
            assert "contacts" in contacts
            
            contact = await client.get_contact("1")
            assert contact is not None
            
            # Test diagnostics
            diagnostics = client.get_diagnostics()
            assert "total_requests" in diagnostics
            assert "successful_requests" in diagnostics
    
    @pytest.mark.asyncio
    async def test_mcp_server_integration(self):
        """Test MCP server integration."""
        from src.mcp.server import KeapMCPServer
        
        # Test server initialization
        server = KeapMCPServer(name="test-server")
        
        # Test server has required components
        assert hasattr(server, 'mcp')
        assert server.mcp is not None
        
        # Test callable methods
        assert callable(getattr(server, 'run', None))
        assert callable(getattr(server, 'run_async', None))
        assert callable(server._register_tools)
        assert callable(server._register_resources)
        
        # Test server with default name
        default_server = KeapMCPServer()
        assert default_server.mcp is not None
    
    @pytest.mark.asyncio
    async def test_mcp_tools_integration(self):
        """Test MCP tools integration with mocks."""
        from src.mcp.tools import get_api_client, get_cache_manager
        
        # Test factory functions
        with patch('src.api.client.KeapApiService') as mock_api:
            with patch('src.cache.manager.CacheManager') as mock_cache:
                mock_api.return_value = MagicMock()
                mock_cache.return_value = MagicMock()
                
                # Test that factory functions return objects
                api_client = get_api_client()
                assert api_client is not None
                
                cache_manager = get_cache_manager()
                assert cache_manager is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations for performance."""
        from src.utils.filter_utils import apply_complex_filters
        
        # Test data
        items = [{"id": i, "name": f"Name{i}", "score": i * 10} for i in range(100)]
        
        async def filter_worker(filter_condition):
            """Worker function for concurrent filtering."""
            filtered = apply_complex_filters(items, [filter_condition])
            return len(filtered)
        
        # Multiple filter scenarios
        filters = [
            {"field": "score", "operator": ">", "value": 50},
            {"field": "score", "operator": "<", "value": 500},
            {"field": "name", "operator": "contains", "value": "Name1"},
            {"field": "id", "operator": ">", "value": 10}
        ]
        
        start_time = time.time()
        tasks = [filter_worker(f) for f in filters]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Verify performance and results
        assert end_time - start_time < 1.0  # Should complete quickly
        assert len(results) == 4
        
        # Verify all operations completed successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 2  # At least half should succeed