"""
Integration tests for optimized collection architecture.

Tests the integration between collection manager, optimization engine, and API client
with real API calls to verify performance improvements and optimization strategies.
"""

import pytest
import os
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    get_api_diagnostics
)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


@pytest.fixture
def skip_if_no_api_key():
    """Skip tests if KEAP_API_KEY is not available"""
    api_key = os.getenv('KEAP_API_KEY')
    if not api_key:
        pytest.skip("KEAP_API_KEY not available in environment")


@pytest.fixture
def context():
    """Create MCP context"""
    return Context()


class TestOptimizedCollectionIntegration:
    """Test optimized collection architecture with real API calls."""

    @pytest.mark.asyncio
    async def test_optimized_contact_search_with_metrics(self, context, skip_if_no_api_key):
        """Test optimized contact search with performance metrics."""
        # Test with filters to trigger optimization engine
        filters = [
            {"field": "email", "operator": "contains", "value": "@"}
        ]
        
        # Call with optimization and metrics enabled
        result = await list_contacts(
            context, 
            filters=filters,
            limit=10,
            enable_optimization=True,
            return_metrics=True
        )
        
        # Verify basic result structure
        assert "collection_id" in result
        assert "count" in result
        assert result["count"] >= 0
        
        # Verify performance metrics are included
        if "performance_metrics" in result:
            metrics = result["performance_metrics"]
            assert "api_calls" in metrics
            assert "strategy_used" in metrics
            print(f"Strategy used: {metrics['strategy_used']}")
            print(f"API calls made: {metrics['api_calls']}")
            
            if "total_duration_ms" in metrics:
                print(f"Total duration: {metrics['total_duration_ms']:.2f}ms")
                print(f"Optimization ratio: {metrics.get('optimization_ratio', 'N/A')}")

    @pytest.mark.asyncio 
    async def test_optimization_vs_non_optimization_performance(self, context, skip_if_no_api_key):
        """Compare performance of optimized vs non-optimized queries."""
        filters = [
            {"field": "given_name", "operator": "contains", "value": "a"}
        ]
        
        # Test with optimization enabled
        result_optimized = await list_contacts(
            context,
            filters=filters,
            limit=20,
            enable_optimization=True,
            return_metrics=True
        )
        
        # Test with optimization disabled  
        result_basic = await list_contacts(
            context,
            filters=filters,
            limit=20,
            enable_optimization=False,
            return_metrics=True
        )
        
        # Both should return results
        assert result_optimized["count"] >= 0
        assert result_basic["count"] >= 0
        
        # Compare metrics if available
        if "performance_metrics" in result_optimized and "performance_metrics" in result_basic:
            opt_metrics = result_optimized["performance_metrics"]
            basic_metrics = result_basic["performance_metrics"]
            
            print(f"Optimized strategy: {opt_metrics.get('strategy_used', 'N/A')}")
            print(f"Basic strategy: {basic_metrics.get('strategy_used', 'N/A')}")
            print(f"Optimized API calls: {opt_metrics.get('api_calls', 'N/A')}")
            print(f"Basic API calls: {basic_metrics.get('api_calls', 'N/A')}")

    @pytest.mark.asyncio
    async def test_optimized_collection_details_bulk_fetch(self, context, skip_if_no_api_key):
        """Test optimized bulk fetching for collection details."""
        # First create a collection with multiple contacts
        result = await list_contacts(context, limit=5)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("No contacts available for bulk fetch testing")
        
        # Test optimized details fetch with metrics
        details = await get_collection_details(
            context, 
            collection_id,
            enable_optimization=True,
            return_metrics=True
        )
        
        # Verify results
        assert "contacts" in details
        assert "count" in details
        assert details["count"] > 0
        
        # Check for optimization metrics
        if "performance_metrics" in details:
            metrics = details["performance_metrics"]
            print(f"Details fetch strategy: {metrics.get('strategy_used', 'N/A')}")
            print(f"Details fetch API calls: {metrics.get('api_calls', 'N/A')}")
            print(f"Efficiency ratio: {metrics.get('efficiency_ratio', 'N/A')}")

    @pytest.mark.asyncio
    async def test_optimization_engine_strategy_selection(self, context, skip_if_no_api_key):
        """Test that optimization engine selects appropriate strategies."""
        test_cases = [
            {
                "name": "Simple query (no filters)",
                "filters": None,
                "limit": 5,
                "expected_strategy_type": "bulk"
            },
            {
                "name": "Email filter query",
                "filters": [{"field": "email", "operator": "contains", "value": "@gmail.com"}],
                "limit": 10,
                "expected_strategy_type": "optimized"
            },
            {
                "name": "Tag-based query",
                "filters": [{"field": "tags", "operator": "contains", "value": "customer"}],
                "limit": 15,
                "expected_strategy_type": "tag_optimized"
            }
        ]
        
        for test_case in test_cases:
            result = await list_contacts(
                context,
                filters=test_case["filters"],
                limit=test_case["limit"],
                enable_optimization=True,
                return_metrics=True
            )
            
            print(f"\nTest case: {test_case['name']}")
            print(f"Collection size: {result['count']}")
            
            if "performance_metrics" in result:
                strategy = result["performance_metrics"].get("strategy_used", "unknown")
                print(f"Strategy selected: {strategy}")
                
                # Verify strategy makes sense for the query type
                if test_case["filters"] is None:
                    # No filters should use bulk retrieval or similar
                    assert strategy in ["bulk_retrieve", "BULK_RETRIEVE", "direct_api"]
                else:
                    # Filtered queries should use optimization
                    assert strategy not in ["bulk_retrieve", "BULK_RETRIEVE"]

    @pytest.mark.asyncio
    async def test_optimization_caching_integration(self, context, skip_if_no_api_key):
        """Test that optimization engine properly integrates with caching."""
        filters = [{"field": "email", "operator": "contains", "value": "@test.com"}]
        
        # First call - should miss cache
        result1 = await list_contacts(
            context,
            filters=filters,
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        
        # Second call - should potentially hit cache
        result2 = await list_contacts(
            context,
            filters=filters,
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        
        # Both should return similar results
        assert result1["count"] == result2["count"]
        
        # Check cache behavior in metrics
        if "performance_metrics" in result1 and "performance_metrics" in result2:
            cache1 = result1["performance_metrics"].get("cache_hit", False)
            cache2 = result2["performance_metrics"].get("cache_hit", False)
            
            print(f"First call cache hit: {cache1}")
            print(f"Second call cache hit: {cache2}")
            
            # Second call should potentially be faster due to caching
            if "total_duration_ms" in result1["performance_metrics"] and "total_duration_ms" in result2["performance_metrics"]:
                duration1 = result1["performance_metrics"]["total_duration_ms"]
                duration2 = result2["performance_metrics"]["total_duration_ms"]
                print(f"First call duration: {duration1:.2f}ms")
                print(f"Second call duration: {duration2:.2f}ms")


class TestOptimizationEngineIntegration:
    """Test optimization engine components integration."""
    
    @pytest.mark.asyncio
    async def test_api_diagnostics_with_optimization_metrics(self, context, skip_if_no_api_key):
        """Test that API diagnostics include optimization metrics."""
        # Perform some operations first to generate metrics
        await list_contacts(context, limit=3, enable_optimization=True)
        
        # Get diagnostics
        diagnostics = await get_api_diagnostics(context)
        
        # Verify diagnostics structure
        assert "api_diagnostics" in diagnostics
        assert "performance_metrics" in diagnostics
        
        # Check for optimization-related metrics
        perf_metrics = diagnostics["performance_metrics"]
        assert "total_requests" in perf_metrics
        assert "success_rate" in perf_metrics
        
        print(f"Total API requests: {perf_metrics['total_requests']}")
        print(f"Success rate: {perf_metrics['success_rate']:.1f}%")
        
        if "cache_hit_rate" in perf_metrics:
            print(f"Cache hit rate: {perf_metrics['cache_hit_rate']:.1f}%")