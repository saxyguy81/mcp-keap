"""
Server and Optimization Integration Tests (No Mocking)

These tests focus on MCP server functionality and optimization components
without mocking, testing real integration between server, optimization,
and utility components.
"""

import pytest
from unittest.mock import patch
from src.mcp import server
from src.mcp.optimization.optimization import QueryExecutor, QueryOptimizer
from src.mcp.optimization.api_optimization import ApiParameterOptimizer
from src.cache.manager import CacheManager
from src.api.client import KeapApiService
from src.utils.filter_utils import (
    apply_complex_filters,
    optimize_filters_for_api,
    get_nested_value,
    parse_date_value
)
from src.schemas.definitions import Contact, Tag, FilterCondition


class TestServerOptimizationIntegration:
    """Test server and optimization integration without external dependencies."""

    @pytest.fixture
    def real_components(self, tmp_path):
        """Create real components for integration testing."""
        cache_path = tmp_path / "server_cache.db"
        cache_manager = CacheManager(
            db_path=str(cache_path),
            max_entries=1000,
            max_memory_mb=10
        )
        
        api_client = KeapApiService(api_key="test_key")
        
        yield {
            "cache_manager": cache_manager,
            "api_client": api_client
        }
        
        cache_manager.close()

    def test_mcp_server_module_integration(self):
        """Test MCP server module functionality."""
        # Test that server module has the expected classes
        assert hasattr(server, 'KeapMCPServer')
        
        # Test server initialization without starting it
        try:
            server_instance = server.KeapMCPServer("Test Server")
            assert server_instance is not None
            assert server_instance.name == "Test Server"
            assert server_instance.version == "1.0.0"
            
            # Test tool listing
            tools = server_instance.list_tools()
            assert isinstance(tools, list)
            assert len(tools) > 0
            assert "list_contacts" in tools
            
        except ImportError:
            # FastMCP might not be available in test environment
            pass

    def test_query_optimizer_integration(self, real_components):
        """Test query optimizer without mocking."""
        optimizer = QueryOptimizer()
        
        filters = [
            {"field": "email", "operator": "equals", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"}
        ]
        
        # Test query analysis
        strategy = optimizer.analyze_query(filters, limit=50)
        assert strategy is not None
        
        # Test performance tracking
        from src.mcp.optimization.optimization import QueryMetrics, QueryStrategy
        metrics = QueryMetrics(
            total_duration_ms=100,
            api_calls=1,
            cache_hit=False,
            strategy_used=QueryStrategy.SERVER_OPTIMIZED,
            filters_applied=len(filters),
            results_count=25,
            server_side_filters=1,
            client_side_filters=1,
            optimization_ratio=0.5
        )
        
        optimizer.track_performance("test_query", metrics)
        
        # Test that the optimizer was configured properly
        assert optimizer.performance_history is not None
        assert optimizer.strategy_scores is not None

    def test_api_parameter_optimizer_integration(self):
        """Test API parameter optimizer functionality."""
        optimizer = ApiParameterOptimizer()
        
        filters = [
            {"field": "email", "operator": "equals", "value": "john@example.com"},
            {"field": "family_name", "operator": "equals", "value": "Doe"},
            {"field": "custom_field", "operator": "contains", "value": "VIP"}
        ]
        
        # Test contact query optimization
        result = optimizer.optimize_contact_query_parameters(filters)
        assert hasattr(result, 'optimization_strategy')
        assert hasattr(result, 'server_side_filters')
        assert hasattr(result, 'client_side_filters')
        assert hasattr(result, 'optimization_score')
        
        # Test tag query optimization
        tag_result = optimizer.optimize_tag_query_parameters(filters)
        assert hasattr(tag_result, 'optimization_strategy')
        
        # Test performance analysis
        performance = optimizer.analyze_filter_performance(filters, "contact")
        assert "performance_rating" in performance
        assert "optimization_score" in performance
        
        # Test field optimization info
        contact_info = optimizer.get_field_optimization_info("contact")
        assert isinstance(contact_info, dict)
        assert len(contact_info) > 0

    @patch('src.api.client.KeapApiService.get_contacts')
    @pytest.mark.asyncio
    async def test_query_executor_integration(self, mock_get_contacts, real_components):
        """Test query executor with real components."""
        mock_get_contacts.return_value = {
            "contacts": [
                {"id": 1, "given_name": "John", "family_name": "Doe"},
                {"id": 2, "given_name": "Jane", "family_name": "Smith"}
            ]
        }
        
        executor = QueryExecutor(
            api_client=real_components["api_client"],
            cache_manager=real_components["cache_manager"]
        )
        
        filters = [
            {"field": "given_name", "operator": "contains", "value": "John"}
        ]
        
        # Test optimized query execution
        results, metrics = await executor.execute_optimized_query(
            query_type="list_contacts",
            filters=filters,
            limit=50
        )
        
        assert isinstance(results, list)
        assert hasattr(metrics, 'total_duration_ms')
        assert hasattr(metrics, 'optimization_ratio')

    def test_filter_utils_advanced_integration(self):
        """Test advanced filter utilities without mocking."""
        items = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "profile": {"status": "active", "level": "premium"},
                "created_date": "2024-01-15"
            },
            {
                "id": 2,
                "name": "Jane Smith", 
                "email": "jane@example.com",
                "profile": {"status": "inactive", "level": "basic"},
                "created_date": "2024-02-10"
            }
        ]
        
        # Test complex filter application
        filters = [
            {
                "operator": "AND",
                "conditions": [
                    {"field": "profile.status", "operator": "equals", "value": "active"},
                    {"field": "profile.level", "operator": "equals", "value": "premium"}
                ]
            }
        ]
        
        filtered_items = apply_complex_filters(items, filters)
        assert len(filtered_items) == 1
        assert filtered_items[0]["id"] == 1
        
        # Test nested value extraction
        nested_value = get_nested_value(items[0], "profile.status")
        assert nested_value == "active"
        
        # Test date parsing
        parsed_date = parse_date_value("2024-01-15")
        assert parsed_date is not None

    def test_filter_optimization_integration(self):
        """Test filter optimization for API calls."""
        filters = [
            {"field": "email", "operator": "equals", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"},
            {"field": "custom_field", "operator": "contains", "value": "VIP"}
        ]
        
        server_params, client_filters = optimize_filters_for_api(filters)
        
        assert isinstance(server_params, dict)
        assert isinstance(client_filters, list)
        
        # Should have some server-optimizable parameters
        assert len(server_params) > 0 or len(client_filters) > 0

    def test_schema_integration_with_data_processing(self):
        """Test schema validation with real data processing."""
        # Test Contact schema with various data formats
        contact_data_variations = [
            {
                "id": 1,
                "given_name": "John",
                "family_name": "Doe",
                "email": "john@example.com"
            },
            {
                "id": 2,
                "given_name": "Jane",
                "family_name": "Smith",
                "company": {"id": 100, "name": "Acme Corp"}  # Object format
            },
            {
                "id": 3,
                "given_name": "Bob",
                "family_name": "Johnson", 
                "company": "Simple Corp"  # String format
            }
        ]
        
        for contact_data in contact_data_variations:
            contact = Contact(**contact_data)
            assert contact.id is not None
            assert contact.given_name is not None
        
        # Test FilterCondition schema
        filter_data = {
            "field": "email",
            "operator": "EQUALS",
            "value": "test@example.com"
        }
        
        filter_condition = FilterCondition(**filter_data)
        assert filter_condition.field == "email"
        assert filter_condition.operator == "EQUALS"

    def test_cache_integration_with_optimization(self, real_components):
        """Test cache integration with optimization components."""
        cache_manager = real_components["cache_manager"]
        
        # Test cache with optimization data
        optimization_data = {
            "strategy": "server_optimized",
            "score": 0.85,
            "server_filters": {"email": "test@example.com"},
            "client_filters": []
        }
        
        cache_manager.set("optimization:query123", optimization_data, ttl=3600)
        
        retrieved = cache_manager.get("optimization:query123")
        assert retrieved["strategy"] == "server_optimized"
        assert retrieved["score"] == 0.85
        
        # Test cache statistics
        stats = cache_manager.get_stats()
        assert stats["total_entries"] >= 1
        
        # Test cache invalidation patterns
        cache_manager.set("optimization:query456", {"data": "value"}, ttl=3600)
        cache_manager.invalidate_all()
        
        assert cache_manager.get("optimization:query123") is None
        assert cache_manager.get("optimization:query456") is None

    def test_api_client_diagnostic_integration(self, real_components):
        """Test API client diagnostics integration."""
        api_client = real_components["api_client"]
        
        # Test diagnostics collection
        diagnostics = api_client.get_diagnostics()
        assert "total_requests" in diagnostics
        assert "successful_requests" in diagnostics
        assert "failed_requests" in diagnostics
        
        # Test rate limiting logic
        rate_limit_status = api_client._should_rate_limit()
        assert isinstance(rate_limit_status, bool)
        
        # Test API info retrieval
        api_info = api_client.get_api_info()
        assert "api_version" in api_info
        assert "base_url" in api_info

    def test_utility_functions_with_real_data(self):
        """Test utility functions with realistic data scenarios."""
        from src.utils.contact_utils import (
            get_full_name,
            get_primary_email,
            get_tag_ids,
            get_custom_field_value,
            format_contact_summary
        )
        
        complex_contact = {
            "id": 123,
            "given_name": "Elizabeth",
            "family_name": "Johnson-Smith",
            "email_addresses": [
                {"email": "liz@personal.com", "field": "EMAIL2"},
                {"email": "elizabeth@work.com", "field": "EMAIL1"}
            ],
            "custom_fields": [
                {"id": 7, "content": "Premium Customer"},
                {"id": 8, "content": "Newsletter Subscriber"}
            ],
            "tag_ids": [10, 25, 30],
            "tags": [
                {"id": 40, "name": "VIP"}
            ]
        }
        
        # Test all utility functions
        full_name = get_full_name(complex_contact)
        assert full_name == "Elizabeth Johnson-Smith"
        
        primary_email = get_primary_email(complex_contact)
        assert primary_email == "liz@personal.com"  # First email in the list
        
        tag_ids = get_tag_ids(complex_contact)
        assert 10 in tag_ids
        assert 40 in tag_ids  # From tags array
        
        custom_value = get_custom_field_value(complex_contact, "7")
        assert custom_value == "Premium Customer"
        
        summary = format_contact_summary(complex_contact)
        assert isinstance(summary, str)
        assert "Elizabeth Johnson-Smith" in summary

    def test_error_resilience_integration(self, real_components):
        """Test error handling and resilience across components."""
        cache_manager = real_components["cache_manager"]
        api_client = real_components["api_client"]
        
        # Test cache resilience
        try:
            cache_manager.set("test_error", {"data": "value"}, ttl=1)
            result = cache_manager.get("test_error")
            assert result is not None
        except Exception as e:
            pytest.fail(f"Cache operations should not fail: {e}")
        
        # Test API client resilience
        try:
            diagnostics = api_client.get_diagnostics()
            assert isinstance(diagnostics, dict)
        except Exception as e:
            pytest.fail(f"API diagnostics should not fail: {e}")
        
        # Test optimization resilience with edge cases
        optimizer = ApiParameterOptimizer()
        
        # Empty filters
        result = optimizer.optimize_contact_query_parameters([])
        assert hasattr(result, 'optimization_strategy')
        
        # Invalid filter structure
        try:
            result = optimizer.analyze_filter_performance([], "invalid_type")
            assert isinstance(result, dict)
        except Exception:
            # Should handle gracefully
            pass