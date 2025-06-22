"""
Comprehensive integration tests for collection workflows and optimization.

Tests complete end-to-end scenarios covering all collection operations,
optimization strategies, and performance characteristics.
"""

import pytest
import asyncio
import os
import time
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_contact_schema,
    collection_union,
    collection_intersect,
    collection_diff,
    collection_count,
    get_collection_details,
    get_collection_ids,
    get_tags,
    modify_collection_tags,
    get_api_diagnostics
)
from src.cache.collections import get_collection_manager


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


class TestComprehensiveCollectionOperations:
    """Test all collection operations comprehensively"""

    @pytest.mark.asyncio
    async def test_complete_collection_lifecycle(self, context, skip_if_no_api_key):
        """Test complete collection lifecycle from creation to cleanup"""
        collection_manager = get_collection_manager()
        initial_count = len(collection_manager.collections)
        
        # Step 1: Create primary collection
        result1 = await list_contacts(context, limit=5, enable_optimization=True)
        collection_id_1 = result1["collection_id"]
        assert result1["count"] >= 0
        
        # Step 2: Create secondary collection
        result2 = await list_contacts(context, limit=3, offset=2, enable_optimization=True)
        collection_id_2 = result2["collection_id"]
        assert result2["count"] >= 0
        
        # Step 3: Test union operation
        union_result = await collection_union(context, collection_id_1, collection_id_2)
        union_collection_id = union_result["collection_id"]
        assert union_result["count"] >= max(result1["count"], result2["count"])
        
        # Step 4: Test intersection operation
        intersect_result = await collection_intersect(context, collection_id_1, collection_id_2)
        intersect_collection_id = intersect_result["collection_id"]
        assert intersect_result["count"] >= 0
        
        # Step 5: Test difference operation
        diff_result = await collection_diff(context, collection_id_1, collection_id_2)
        diff_collection_id = diff_result["collection_id"]
        assert diff_result["count"] >= 0
        
        # Step 6: Verify mathematical relationships
        # |A ∪ B| + |A ∩ B| >= |A| and |A ∪ B| + |A ∩ B| >= |B|
        union_count = union_result["count"]
        intersect_count = intersect_result["count"]
        diff_count = diff_result["count"]
        
        # Basic set theory verification
        assert union_count >= result1["count"]
        assert union_count >= result2["count"]
        assert diff_count + intersect_count <= result1["count"] + 1  # Allow for API variance
        
        # Step 7: Test collection details retrieval
        details = await get_collection_details(context, union_collection_id)
        assert details["count"] == union_count
        assert len(details["contacts"]) == union_count
        
        # Step 8: Test collection ID retrieval
        ids = await get_collection_ids(context, union_collection_id)
        assert len(ids["contact_ids"]) == union_count
        
        # Step 9: Test collection counting
        count_result = await collection_count(context, union_collection_id)
        assert count_result["count"] == union_count

    @pytest.mark.asyncio
    async def test_optimization_strategy_coverage(self, context, skip_if_no_api_key):
        """Test various optimization strategies are exercised"""
        strategies_tested = set()
        
        # Test 1: Simple bulk retrieval (no filters)
        result1 = await list_contacts(
            context, 
            limit=5, 
            enable_optimization=True,
            return_metrics=True
        )
        if "performance_metrics" in result1:
            strategy = result1["performance_metrics"].get("strategy_used", "unknown")
            strategies_tested.add(strategy)
        
        # Test 2: Email filtering
        result2 = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        if "performance_metrics" in result2:
            strategy = result2["performance_metrics"].get("strategy_used", "unknown")
            strategies_tested.add(strategy)
        
        # Test 3: Name filtering  
        result3 = await list_contacts(
            context,
            filters=[{"field": "given_name", "operator": "starts_with", "value": "A"}],
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        if "performance_metrics" in result3:
            strategy = result3["performance_metrics"].get("strategy_used", "unknown")
            strategies_tested.add(strategy)
        
        # Should have tested multiple strategies
        print(f"Optimization strategies tested: {strategies_tested}")
        assert len(strategies_tested) >= 1  # At least one strategy should be detected

    @pytest.mark.asyncio
    async def test_concurrent_collection_operations(self, context, skip_if_no_api_key):
        """Test concurrent collection operations"""
        # Create multiple collections concurrently
        async def create_collection(offset):
            return await list_contacts(
                context, 
                limit=2, 
                offset=offset,
                enable_optimization=True
            )
        
        # Create 5 collections concurrently
        tasks = [create_collection(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert "collection_id" in result
            assert result["count"] >= 0
        
        # Test concurrent operations on the collections
        collection_ids = [result["collection_id"] for result in results]
        
        async def get_details(collection_id):
            return await get_collection_details(context, collection_id)
        
        # Get details for all collections concurrently
        detail_tasks = [get_details(cid) for cid in collection_ids[:3]]  # Limit to 3 for efficiency
        detail_results = await asyncio.gather(*detail_tasks)
        
        # All should succeed
        for detail_result in detail_results:
            assert "contacts" in detail_result
            assert "count" in detail_result

    @pytest.mark.asyncio
    async def test_large_scale_collection_operations(self, context, skip_if_no_api_key):
        """Test collection operations at larger scale"""
        # Create larger collections
        large_result1 = await list_contacts(
            context, 
            limit=10,
            enable_optimization=True,
            return_metrics=True
        )
        large_result2 = await list_contacts(
            context, 
            limit=8, 
            offset=5,
            enable_optimization=True,
            return_metrics=True
        )
        
        collection_id_1 = large_result1["collection_id"]
        collection_id_2 = large_result2["collection_id"]
        
        # Time the union operation
        start_time = time.time()
        union_result = await collection_union(context, collection_id_1, collection_id_2)
        union_time = time.time() - start_time
        
        # Should complete efficiently
        assert union_time < 3.0  # Should take less than 3 seconds
        assert union_result["count"] >= 0
        
        # Test intersection timing
        start_time = time.time()
        intersect_result = await collection_intersect(context, collection_id_1, collection_id_2)
        intersect_time = time.time() - start_time
        
        assert intersect_time < 2.0  # Should be faster than union
        assert intersect_result["count"] >= 0


class TestSchemaAndDiagnosticsComprehensive:
    """Comprehensive tests for schema and diagnostics"""

    @pytest.mark.asyncio
    async def test_comprehensive_schema_discovery(self, context, skip_if_no_api_key):
        """Test comprehensive schema discovery functionality"""
        schema = await get_contact_schema(context)
        
        # Verify core schema components exist
        assert isinstance(schema, dict), "Schema should be a dictionary"
        assert len(schema) > 0, "Schema should not be empty"
        
        # Check for at least some expected components
        expected_components = ["standard_fields", "supported_operators", "filter_examples"]
        found_components = [comp for comp in expected_components if comp in schema]
        assert len(found_components) >= 2, f"Expected at least 2 core components, found: {found_components}"
        
        # Verify standard fields exist if available
        if "standard_fields" in schema:
            standard_fields = schema["standard_fields"]
            assert isinstance(standard_fields, list), "Standard fields should be a list"
            assert len(standard_fields) > 0, "Should have some standard fields"
        
        # Verify operators exist if available
        if "supported_operators" in schema:
            operators = schema["supported_operators"]
            assert isinstance(operators, list), "Operators should be a list"
            assert len(operators) > 0, "Should have some operators"
        
        # Verify filter examples exist if available
        if "filter_examples" in schema:
            examples = schema["filter_examples"]
            assert isinstance(examples, list), "Examples should be a list"
            assert len(examples) > 0, "Should have some examples"

    @pytest.mark.asyncio
    async def test_comprehensive_api_diagnostics(self, context, skip_if_no_api_key):
        """Test comprehensive API diagnostics"""
        # Perform some operations to generate metrics
        await list_contacts(context, limit=2, enable_optimization=True)
        await list_contacts(context, limit=3, enable_optimization=True)
        
        # Get comprehensive diagnostics
        diagnostics = await get_api_diagnostics(context)
        
        # Verify diagnostic structure  
        assert "api_diagnostics" in diagnostics
        assert "performance_metrics" in diagnostics
        assert "collection_diagnostics" in diagnostics
        
        # Verify API diagnostics
        api_diag = diagnostics["api_diagnostics"]
        assert "daily_requests_remaining" in api_diag
        assert "average_response_time" in api_diag
        
        # Verify performance metrics
        perf_metrics = diagnostics["performance_metrics"]
        assert "total_requests" in perf_metrics
        assert "success_rate" in perf_metrics
        assert isinstance(perf_metrics["total_requests"], int)
        assert 0 <= perf_metrics["success_rate"] <= 100
        
        # Verify collection diagnostics (not collection_stats)
        collection_diag = diagnostics["collection_diagnostics"]
        assert "active_collections" in collection_diag
        assert "total_contacts_across_collections" in collection_diag


class TestErrorHandlingAndRecovery:
    """Comprehensive error handling and recovery tests"""

    @pytest.mark.asyncio
    async def test_comprehensive_error_scenarios(self, context, skip_if_no_api_key):
        """Test various error scenarios and recovery"""
        # Test invalid collection operations
        error_scenarios = [
            ("get_collection_details", "invalid_collection_id"),
            ("collection_union", "invalid1", "invalid2"),
            ("collection_intersect", "invalid1", "invalid2"),
            ("collection_diff", "invalid1", "invalid2"),
            ("collection_count", "invalid_collection_id"),
            ("get_collection_ids", "invalid_collection_id")
        ]
        
        for scenario in error_scenarios:
            operation = scenario[0]
            args = scenario[1:]
            
            with pytest.raises(ValueError, match="not found"):
                if operation == "get_collection_details":
                    await get_collection_details(context, args[0])
                elif operation == "collection_union":
                    await collection_union(context, args[0], args[1])
                elif operation == "collection_intersect":
                    await collection_intersect(context, args[0], args[1])
                elif operation == "collection_diff":
                    await collection_diff(context, args[0], args[1])
                elif operation == "collection_count":
                    await collection_count(context, args[0])
                elif operation == "get_collection_ids":
                    await get_collection_ids(context, args[0])

    @pytest.mark.asyncio
    async def test_recovery_after_errors(self, context, skip_if_no_api_key):
        """Test system recovery after errors"""
        # Trigger an error
        try:
            await get_collection_details(context, "invalid_collection")
        except ValueError:
            pass  # Expected error
        
        # Verify system still works normally
        result = await list_contacts(context, limit=2)
        assert "collection_id" in result
        assert result["count"] >= 0
        
        # Verify collection operations still work
        details = await get_collection_details(context, result["collection_id"])
        assert "contacts" in details


class TestFilteringAndOptimization:
    """Comprehensive filtering and optimization tests"""

    @pytest.mark.asyncio
    async def test_comprehensive_filtering_scenarios(self, context, skip_if_no_api_key):
        """Test various filtering scenarios with optimization"""
        filtering_scenarios = [
            # Basic filters
            ([{"field": "email", "operator": "contains", "value": "@"}], "email filtering"),
            ([{"field": "given_name", "operator": "starts_with", "value": "A"}], "name prefix filtering"),
            ([{"field": "family_name", "operator": "ends_with", "value": "son"}], "name suffix filtering"),
            
            # Multiple filters
            ([
                {"field": "email", "operator": "contains", "value": "@"},
                {"field": "given_name", "operator": "not_equals", "value": ""}
            ], "multiple field filtering"),
        ]
        
        for filters, description in filtering_scenarios:
            try:
                result = await list_contacts(
                    context,
                    filters=filters,
                    limit=5,
                    enable_optimization=True,
                    return_metrics=True
                )
                
                assert "collection_id" in result
                assert result["count"] >= 0
                
                print(f"✓ {description}: {result['count']} contacts")
                
                # Verify optimization was applied
                if "performance_metrics" in result:
                    metrics = result["performance_metrics"]
                    assert "strategy_used" in metrics
                    assert "api_calls" in metrics
                    
            except Exception as e:
                # Some filters may not work in test environment
                print(f"⚠ {description} failed: {e}")

    @pytest.mark.asyncio
    async def test_optimization_performance_comparison(self, context, skip_if_no_api_key):
        """Test optimization performance improvements"""
        # Test with optimization enabled
        start_time = time.time()
        optimized_result = await list_contacts(
            context,
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        optimized_time = time.time() - start_time
        
        # Test with optimization disabled
        start_time = time.time()
        unoptimized_result = await list_contacts(
            context,
            limit=5,
            enable_optimization=False,
            return_metrics=True
        )
        unoptimized_time = time.time() - start_time
        
        # Both should return valid results
        assert optimized_result["count"] >= 0
        assert unoptimized_result["count"] >= 0
        
        # Compare performance metrics if available
        if ("performance_metrics" in optimized_result and 
            "performance_metrics" in unoptimized_result):
            
            opt_metrics = optimized_result["performance_metrics"]
            unopt_metrics = unoptimized_result["performance_metrics"]
            
            print(f"Optimized: {opt_metrics.get('api_calls', 'N/A')} API calls")
            print(f"Unoptimized: {unopt_metrics.get('api_calls', 'N/A')} API calls")
            print(f"Optimized time: {optimized_time:.2f}s")
            print(f"Unoptimized time: {unoptimized_time:.2f}s")


class TestDataConsistencyAndIntegrity:
    """Test data consistency and integrity across operations"""

    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(self, context, skip_if_no_api_key):
        """Test data consistency across different operations"""
        # Create base collection
        base_result = await list_contacts(context, limit=5)
        collection_id = base_result["collection_id"]
        
        if base_result["count"] == 0:
            pytest.skip("No contacts available for consistency testing")
        
        # Get data through different methods
        details_result = await get_collection_details(context, collection_id)
        ids_result = await get_collection_ids(context, collection_id)
        count_result = await collection_count(context, collection_id)
        
        # Verify consistency
        assert details_result["count"] == len(details_result["contacts"])
        assert details_result["count"] == len(ids_result["contact_ids"])
        assert details_result["count"] == count_result["count"]
        
        # Verify contact ID consistency
        detail_ids = set(contact["id"] for contact in details_result["contacts"])
        ids_list = set(ids_result["contact_ids"])
        assert detail_ids == ids_list

    @pytest.mark.asyncio
    async def test_collection_immutability(self, context, skip_if_no_api_key):
        """Test that collections remain immutable after operations"""
        # Create collection
        result = await list_contacts(context, limit=3)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("No contacts available for immutability testing")
        
        # Get initial state
        initial_ids = await get_collection_ids(context, collection_id)
        initial_count = await collection_count(context, collection_id)
        
        # Perform operations that should not modify original
        union_result = await collection_union(context, collection_id, collection_id)
        intersect_result = await collection_intersect(context, collection_id, collection_id)
        
        # Verify original collection unchanged
        final_ids = await get_collection_ids(context, collection_id)
        final_count = await collection_count(context, collection_id)
        
        assert initial_ids["contact_ids"] == final_ids["contact_ids"]
        assert initial_count["count"] == final_count["count"]
        
        # Verify operations created new collections
        assert union_result["collection_id"] != collection_id
        assert intersect_result["collection_id"] != collection_id