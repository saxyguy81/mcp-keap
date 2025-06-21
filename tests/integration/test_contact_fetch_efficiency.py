"""
Streamlined Efficiency Integration Tests

Essential tests for contact fetch efficiency and optimization.
Focuses on core performance characteristics without extensive exploration.
"""

import pytest
import os
import time
from unittest.mock import patch, AsyncMock

from src.mcp.tools_collections import list_contacts, get_collection_details
from mcp.server.fastmcp import Context


@pytest.fixture
def skip_if_no_api_key():
    """Skip tests if KEAP_API_KEY is not available"""
    api_key = os.getenv('KEAP_API_KEY')
    if not api_key:
        pytest.skip("KEAP_API_KEY not available in environment")


@pytest.fixture
def context():
    """Create MCP context for testing."""
    return Context()


class TestContactFetchEfficiency:
    """Test contact fetching efficiency and optimization."""

    @pytest.mark.asyncio
    async def test_small_collection_efficiency(self, context, skip_if_no_api_key):
        """Test efficiency for small collections (typical use case)."""
        start_time = time.time()
        
        # Test with small collection
        result = await list_contacts(
            context,
            limit=3,
            enable_optimization=True,
            return_metrics=True
        )
        
        duration = time.time() - start_time
        
        # Verify basic results
        assert "collection_id" in result
        assert "count" in result
        assert result["count"] >= 0
        
        # Performance should be reasonable
        assert duration < 5.0, f"Small collection took too long: {duration:.2f}s"
        
        # Check performance metrics if available
        if "performance_metrics" in result:
            metrics = result["performance_metrics"]
            print(f"Small collection - API calls: {metrics.get('api_calls', 'N/A')}")
            print(f"Strategy used: {metrics.get('strategy_used', 'N/A')}")

    @pytest.mark.asyncio
    async def test_collection_details_efficiency(self, context, skip_if_no_api_key):
        """Test efficiency of getting detailed contact information."""
        # First get a collection
        contacts_result = await list_contacts(context, limit=2)
        collection_id = contacts_result["collection_id"]
        
        if contacts_result["count"] == 0:
            pytest.skip("No contacts available for efficiency testing")
        
        start_time = time.time()
        
        # Get detailed information
        details = await get_collection_details(
            context,
            collection_id,
            enable_optimization=True,
            return_metrics=True
        )
        
        duration = time.time() - start_time
        
        # Verify results
        assert "contacts" in details
        assert "count" in details
        assert details["count"] == contacts_result["count"]
        
        # Performance should be reasonable
        assert duration < 8.0, f"Details fetch took too long: {duration:.2f}s"
        
        # Check efficiency metrics
        if "performance_metrics" in details:
            metrics = details["performance_metrics"]
            print(f"Details fetch - API calls: {metrics.get('api_calls', 'N/A')}")
            efficiency = metrics.get('efficiency_ratio', 0)
            print(f"Efficiency ratio: {efficiency}")

    @pytest.mark.asyncio
    async def test_optimization_vs_no_optimization(self, context, skip_if_no_api_key):
        """Compare performance with and without optimization enabled."""
        filters = [{"field": "given_name", "operator": "contains", "value": "a"}]
        
        # Test with optimization
        start_time = time.time()
        optimized_result = await list_contacts(
            context,
            filters=filters,
            limit=3,
            enable_optimization=True,
            return_metrics=True
        )
        optimized_duration = time.time() - start_time
        
        # Test without optimization  
        start_time = time.time()
        basic_result = await list_contacts(
            context,
            filters=filters,
            limit=3,
            enable_optimization=False,
            return_metrics=True
        )
        basic_duration = time.time() - start_time
        
        # Both should return results
        assert optimized_result["count"] >= 0
        assert basic_result["count"] >= 0
        
        print(f"Optimized duration: {optimized_duration:.2f}s")
        print(f"Basic duration: {basic_duration:.2f}s")
        
        # Compare performance metrics if available
        if ("performance_metrics" in optimized_result and 
            "performance_metrics" in basic_result):
            opt_metrics = optimized_result["performance_metrics"]
            basic_metrics = basic_result["performance_metrics"]
            
            print(f"Optimized strategy: {opt_metrics.get('strategy_used', 'N/A')}")
            print(f"Basic strategy: {basic_metrics.get('strategy_used', 'N/A')}")


class TestPerformanceBaseline:
    """Establish performance baselines for regression testing."""

    @pytest.mark.asyncio
    async def test_api_response_time_baseline(self, context, skip_if_no_api_key):
        """Test that basic API operations meet performance baselines."""
        times = []
        
        # Run multiple small operations to get average
        for _ in range(3):
            start_time = time.time()
            result = await list_contacts(context, limit=1, enable_optimization=True)
            duration = time.time() - start_time
            times.append(duration)
            
            assert result["count"] >= 0
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"Average API response time: {avg_time:.2f}s")
        print(f"Maximum API response time: {max_time:.2f}s")
        
        # Performance baselines
        assert avg_time < 3.0, f"Average response time too high: {avg_time:.2f}s"
        assert max_time < 5.0, f"Maximum response time too high: {max_time:.2f}s"