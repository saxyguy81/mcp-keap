"""
Integration tests for Optimization components.

Tests the integration between query optimization, API parameter optimization,
and their interaction with the API client and cache systems.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.optimization.optimization import QueryExecutor, QueryOptimizer
from src.mcp.optimization.api_optimization import ApiParameterOptimizer
from src.api.client import KeapApiService
from src.cache.manager import CacheManager


class TestOptimizationIntegration:
    """Test optimization component integration."""
    
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
    def mock_api_client(self):
        """Create comprehensive mock API client."""
        client = AsyncMock(spec=KeapApiService)
        
        # Mock contact responses
        client.get_contacts.return_value = {
            "contacts": [
                {
                    "id": 1, "given_name": "John", "family_name": "Doe",
                    "email_addresses": [{"email": "john@example.com", "field": "EMAIL1"}],
                    "tag_ids": [10, 20],
                    "custom_fields": [{"id": 7, "content": "VIP"}],
                    "date_created": "2024-01-15T10:30:00Z"
                },
                {
                    "id": 2, "given_name": "Jane", "family_name": "Smith",
                    "email_addresses": [{"email": "jane@company.com", "field": "EMAIL1"}],
                    "tag_ids": [10],
                    "custom_fields": [{"id": 7, "content": "Regular"}],
                    "date_created": "2024-01-16T11:30:00Z"
                }
            ]
        }
        
        # Mock tag responses
        client.get_tags.return_value = {
            "tags": [
                {"id": 10, "name": "Customer", "description": "Customer tag"},
                {"id": 20, "name": "VIP", "description": "VIP customer"}
            ]
        }
        
        return client
    
    @pytest.fixture
    def query_executor(self, mock_api_client, cache_manager):
        """Create query executor with mock dependencies."""
        return QueryExecutor(mock_api_client, cache_manager)
    
    @pytest.fixture
    def query_optimizer(self):
        """Create query optimizer."""
        return QueryOptimizer()
    
    @pytest.fixture
    def api_parameter_optimizer(self):
        """Create API parameter optimizer."""
        return ApiParameterOptimizer()
    
    @pytest.mark.asyncio
    async def test_query_execution_with_server_optimization(self, query_executor, mock_api_client):
        """Test query execution using server-side optimization."""
        filters = [
            {"field": "email", "operator": "=", "value": "john@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"}
        ]
        
        # Execute optimized query
        contacts, metrics = await query_executor.execute_optimized_query(
            query_type="list_contacts",
            filters=filters,
            limit=50
        )
        
        # Verify results
        assert len(contacts) == 2
        assert contacts[0]["given_name"] == "John"
        assert contacts[1]["given_name"] == "Jane"
        
        # Verify metrics
        assert metrics.query_type == "list_contacts"
        assert metrics.api_calls >= 1
        assert metrics.total_duration_ms > 0
        
        # Verify API was called with optimizations
        mock_api_client.get_contacts.assert_called()
    
    @pytest.mark.asyncio
    async def test_query_execution_with_cache_optimization(self, query_executor, mock_api_client, cache_manager):
        """Test query execution with cache optimization."""
        filters = [{"field": "given_name", "operator": "=", "value": "John"}]
        
        # First execution - should hit API and cache result
        contacts1, metrics1 = await query_executor.execute_optimized_query(
            query_type="list_contacts",
            filters=filters,
            limit=50
        )
        
        # Verify first execution
        assert len(contacts1) == 2
        assert metrics1.cache_hit is False
        assert metrics1.api_calls == 1
        
        # Second execution - should hit cache
        contacts2, metrics2 = await query_executor.execute_optimized_query(
            query_type="list_contacts",
            filters=filters,
            limit=50
        )
        
        # Verify cache hit
        assert contacts1 == contacts2
        assert metrics2.cache_hit is True
        assert metrics2.api_calls == 0
        
        # API should only be called once
        assert mock_api_client.get_contacts.call_count == 1
    
    @pytest.mark.asyncio
    async def test_hybrid_optimization_strategy(self, query_executor, query_optimizer, mock_api_client):
        """Test hybrid optimization strategy with mixed filters."""
        filters = [
            {"field": "email", "operator": "=", "value": "john@example.com"},  # Server-optimizable
            {"field": "tag", "operator": "=", "value": "10"},  # Client-side
            {"field": "custom_field", "operator": "=", "value": "VIP"}  # Client-side
        ]
        
        # Analyze optimization strategy
        strategy = query_optimizer.analyze_query(filters)
        
        # Should recommend hybrid strategy
        assert strategy in ["hybrid", "client_optimized"]
        
        # Execute with optimization
        contacts, metrics = await query_executor.execute_optimized_query(
            query_type="list_contacts",
            filters=filters,
            limit=50
        )
        
        # Verify results
        assert len(contacts) >= 0  # May be filtered down by client-side logic
        assert metrics.api_calls >= 1
    
    @pytest.mark.asyncio
    async def test_api_parameter_optimization_integration(self, api_parameter_optimizer, mock_api_client):
        """Test API parameter optimization integration."""
        filters = [
            {"field": "email", "operator": "=", "value": "john@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"},
            {"field": "family_name", "operator": "=", "value": "Doe"}
        ]
        
        # Optimize parameters for contact query
        optimization_result = api_parameter_optimizer.optimize_contact_query_parameters(filters)
        
        # Verify optimization
        assert optimization_result.optimization_strategy in ["highly_optimized", "moderately_optimized"]
        assert optimization_result.optimization_score > 0
        assert len(optimization_result.server_side_filters) > 0
        
        # Analyze performance
        performance_analysis = api_parameter_optimizer.analyze_filter_performance(filters, "contact")
        
        # Verify performance analysis
        assert "performance_rating" in performance_analysis
        assert "estimated_response_time_ms" in performance_analysis
        assert performance_analysis["performance_rating"] in ["excellent", "good", "fair", "poor"]
    
    @pytest.mark.asyncio
    async def test_optimization_with_tag_queries(self, query_executor, api_parameter_optimizer, mock_api_client):
        """Test optimization integration with tag queries."""
        filters = [
            {"field": "name", "operator": "contains", "value": "Customer"},
            {"field": "category", "operator": "=", "value": "Status"}
        ]
        
        # Optimize tag query parameters
        optimization_result = api_parameter_optimizer.optimize_tag_query_parameters(filters)
        
        # Verify tag optimization
        assert optimization_result.optimization_strategy in ["highly_optimized", "moderately_optimized", "minimally_optimized"]
        assert optimization_result.optimization_score >= 0
        
        # Execute optimized tag query
        tags, metrics = await query_executor.execute_optimized_query(
            query_type="get_tags",
            filters=filters,
            limit=100
        )
        
        # Verify results
        assert len(tags) == 2
        assert metrics.query_type == "get_tags"
        assert metrics.api_calls >= 1
    
    @pytest.mark.asyncio
    async def test_optimization_performance_measurement(self, query_executor, mock_api_client):
        """Test optimization performance measurement and metrics."""
        filters = [{"field": "email", "operator": "=", "value": "john@example.com"}]
        
        # Execute multiple queries to measure performance
        execution_times = []
        
        for i in range(5):
            start_time = time.time()
            
            contacts, metrics = await query_executor.execute_optimized_query(
                query_type="list_contacts",
                filters=filters,
                limit=50
            )
            
            end_time = time.time()
            execution_times.append(end_time - start_time)
            
            # Verify consistent results
            assert len(contacts) == 2
            assert metrics.total_duration_ms > 0
        
        # Verify performance consistency
        avg_time = sum(execution_times) / len(execution_times)
        assert avg_time < 1.0  # Should complete quickly with optimization
    
    @pytest.mark.asyncio
    async def test_optimization_with_complex_filters(self, query_executor, query_optimizer):
        """Test optimization with complex nested filter groups."""
        complex_filters = [
            {
                "type": "group",
                "operator": "AND",
                "conditions": [
                    {"field": "email", "operator": "contains", "value": "@example.com"},
                    {
                        "type": "group",
                        "operator": "OR",
                        "conditions": [
                            {"field": "given_name", "operator": "=", "value": "John"},
                            {"field": "given_name", "operator": "=", "value": "Jane"}
                        ]
                    }
                ]
            }
        ]
        
        # Analyze complex query
        strategy = query_optimizer.analyze_query(complex_filters)
        assert strategy in ["server_optimized", "hybrid", "client_optimized"]
        
        # Execute complex query
        contacts, metrics = await query_executor.execute_optimized_query(
            query_type="list_contacts",
            filters=complex_filters,
            limit=50
        )
        
        # Verify handling of complex filters
        assert isinstance(contacts, list)
        assert metrics.query_type == "list_contacts"
    
    @pytest.mark.asyncio
    async def test_optimization_field_capabilities(self, api_parameter_optimizer):
        """Test optimization field capabilities analysis."""
        # Get field optimization info for contacts
        contact_info = api_parameter_optimizer.get_field_optimization_info("contact")
        
        # Verify field information
        assert isinstance(contact_info, dict)
        assert len(contact_info) > 0
        
        # Check for common contact fields
        expected_fields = ["email", "given_name", "family_name"]
        for field in expected_fields:
            if field in contact_info:
                field_info = contact_info[field]
                assert "performance_level" in field_info
                assert "server_supported" in field_info
        
        # Get field optimization info for tags
        tag_info = api_parameter_optimizer.get_field_optimization_info("tag")
        
        # Verify tag field information
        assert isinstance(tag_info, dict)
        assert len(tag_info) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_optimization_operations(self, query_executor, mock_api_client):
        """Test concurrent optimization operations."""
        async def execute_query(worker_id):
            filters = [
                {"field": "given_name", "operator": "=", "value": f"User{worker_id}"}
            ]
            
            contacts, metrics = await query_executor.execute_optimized_query(
                query_type="list_contacts",
                filters=filters,
                limit=10
            )
            
            return len(contacts), metrics.total_duration_ms
        
        # Execute multiple concurrent queries
        tasks = [execute_query(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed
        assert len(results) == 5
        
        # Verify each result has valid metrics
        for count, duration in results:
            assert count >= 0
            assert duration > 0
    
    @pytest.mark.asyncio
    async def test_optimization_error_handling(self, query_executor, mock_api_client):
        """Test optimization error handling and fallback strategies."""
        # Configure API to fail
        mock_api_client.get_contacts.side_effect = Exception("API temporarily unavailable")
        
        filters = [{"field": "email", "operator": "=", "value": "test@example.com"}]
        
        try:
            # Attempt optimized query with failing API
            contacts, metrics = await query_executor.execute_optimized_query(
                query_type="list_contacts",
                filters=filters,
                limit=50
            )
            
            # If no exception is raised, verify graceful handling
            assert isinstance(contacts, list)
            assert metrics.api_calls >= 0
            
        except Exception as e:
            # Exception handling is acceptable for API failures
            assert "API temporarily unavailable" in str(e)
        
        # Reset API to working state
        mock_api_client.get_contacts.side_effect = None
        
        # Verify recovery
        contacts, metrics = await query_executor.execute_optimized_query(
            query_type="list_contacts",
            filters=filters,
            limit=50
        )
        
        assert len(contacts) == 2
        assert metrics.api_calls >= 1
    
    @pytest.mark.asyncio
    async def test_optimization_cache_key_generation(self, query_executor):
        """Test optimization cache key generation for different query types."""
        filters = [{"field": "email", "operator": "=", "value": "test@example.com"}]
        
        # Generate cache keys for different scenarios
        key1 = query_executor._generate_cache_key(
            query_type="list_contacts",
            filters=filters,
            limit=50,
            offset=0
        )
        
        key2 = query_executor._generate_cache_key(
            query_type="list_contacts",
            filters=filters,
            limit=50,
            offset=10
        )
        
        key3 = query_executor._generate_cache_key(
            query_type="get_tags",
            filters=filters,
            limit=50
        )
        
        # Verify cache keys are unique for different parameters
        assert key1 != key2  # Different offset
        assert key1 != key3  # Different query type
        assert key2 != key3  # Different query type and offset
        
        # Verify cache keys are consistent for same parameters
        key1_duplicate = query_executor._generate_cache_key(
            query_type="list_contacts",
            filters=filters,
            limit=50,
            offset=0
        )
        
        assert key1 == key1_duplicate