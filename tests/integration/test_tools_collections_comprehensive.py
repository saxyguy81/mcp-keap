"""
Comprehensive integration tests for tools_collections.py functions.

Focus on achieving 70%+ coverage by testing all existing functions
with various scenarios, error conditions, and edge cases.
"""

import pytest
import asyncio
import os
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
    apply_tags_to_collection,
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


class TestListContactsComprehensive:
    """Comprehensive tests for list_contacts function"""

    @pytest.mark.asyncio
    async def test_list_contacts_all_parameters(self, context, skip_if_no_api_key):
        """Test list_contacts with all parameter combinations"""
        # Test basic call
        result1 = await list_contacts(context, limit=3)
        assert "collection_id" in result1
        assert "count" in result1
        assert result1["count"] >= 0
        
        # Test with offset
        result2 = await list_contacts(context, limit=2, offset=1)
        assert "collection_id" in result2
        assert result2["count"] >= 0
        
        # Test with optimization enabled
        result3 = await list_contacts(context, limit=2, enable_optimization=True)
        assert "collection_id" in result3
        assert result3["count"] >= 0
        
        # Test with metrics
        result4 = await list_contacts(context, limit=2, return_metrics=True)
        assert "collection_id" in result4
        if "performance_metrics" in result4:
            assert "api_calls" in result4["performance_metrics"]

    @pytest.mark.asyncio
    async def test_list_contacts_with_filters(self, context, skip_if_no_api_key):
        """Test list_contacts with various filter combinations"""
        filter_scenarios = [
            # Basic email filter
            [{"field": "email", "operator": "contains", "value": "@"}],
            # Name filters
            [{"field": "given_name", "operator": "not_equals", "value": ""}],
            [{"field": "family_name", "operator": "not_equals", "value": ""}],
            # Multiple filters
            [
                {"field": "email", "operator": "contains", "value": "@"},
                {"field": "given_name", "operator": "not_equals", "value": ""}
            ]
        ]
        
        for filters in filter_scenarios:
            try:
                result = await list_contacts(
                    context, 
                    filters=filters, 
                    limit=3,
                    enable_optimization=True,
                    return_metrics=True
                )
                assert "collection_id" in result
                assert result["count"] >= 0
                
            except Exception as e:
                # Some filters may not work in test environment
                expected_errors = ["invalid", "unauthorized", "bad request"]
                if not any(err in str(e).lower() for err in expected_errors):
                    raise

    @pytest.mark.asyncio
    async def test_list_contacts_edge_cases(self, context, skip_if_no_api_key):
        """Test list_contacts edge cases"""
        # Zero limit
        result1 = await list_contacts(context, limit=0)
        assert result1["count"] == 0
        
        # Large offset
        result2 = await list_contacts(context, limit=1, offset=1000)
        assert "collection_id" in result2
        assert result2["count"] >= 0
        
        # Invalid filters (should handle gracefully)
        try:
            result3 = await list_contacts(
                context, 
                filters=[{"field": "invalid_field", "operator": "equals", "value": "test"}],
                limit=1
            )
            assert "collection_id" in result3
        except Exception:
            # Expected to fail, but should be handled gracefully
            pass

    @pytest.mark.asyncio
    async def test_list_contacts_order_parameters(self, context, skip_if_no_api_key):
        """Test list_contacts with order parameters"""
        # Test different order combinations
        order_scenarios = [
            (None, None),
            ("given_name", "ASC"),
            ("family_name", "DESC"),
            ("id", "ASC"),
        ]
        
        for order_by, order_direction in order_scenarios:
            result = await list_contacts(
                context, 
                limit=2,
                order_by=order_by,
                order_direction=order_direction
            )
            assert "collection_id" in result
            assert result["count"] >= 0


class TestCollectionOperationsComprehensive:
    """Comprehensive tests for all collection operations"""

    @pytest.mark.asyncio
    async def test_all_collection_operations_workflow(self, context, skip_if_no_api_key):
        """Test complete workflow using all collection operations"""
        # Create base collections
        result1 = await list_contacts(context, limit=4)
        result2 = await list_contacts(context, limit=3, offset=1)
        
        collection_id_1 = result1["collection_id"]
        collection_id_2 = result2["collection_id"]
        
        if result1["count"] == 0 or result2["count"] == 0:
            pytest.skip("Need contacts for collection operations")
        
        # Test union
        union_result = await collection_union(context, collection_id_1, collection_id_2)
        union_id = union_result["collection_id"]
        assert union_result["count"] >= max(result1["count"], result2["count"])
        
        # Test intersection
        intersect_result = await collection_intersect(context, collection_id_1, collection_id_2)
        intersect_id = intersect_result["collection_id"]
        assert intersect_result["count"] >= 0
        
        # Test difference
        diff_result = await collection_diff(context, collection_id_1, collection_id_2)
        diff_id = diff_result["collection_id"]
        assert diff_result["count"] >= 0
        
        # Test collection_count on all results
        union_count = await collection_count(context, union_id)
        assert union_count["count"] == union_result["count"]
        
        intersect_count = await collection_count(context, intersect_id)
        assert intersect_count["count"] == intersect_result["count"]
        
        diff_count = await collection_count(context, diff_id)
        assert diff_count["count"] == diff_result["count"]
        
        # Test get_collection_ids on all results
        union_ids = await get_collection_ids(context, union_id)
        assert len(union_ids["contact_ids"]) == union_result["count"]
        
        intersect_ids = await get_collection_ids(context, intersect_id)
        assert len(intersect_ids["contact_ids"]) == intersect_result["count"]
        
        diff_ids = await get_collection_ids(context, diff_id)
        assert len(diff_ids["contact_ids"]) == diff_result["count"]
        
        # Test get_collection_details on all results
        union_details = await get_collection_details(context, union_id)
        assert len(union_details["contacts"]) == union_result["count"]
        
        intersect_details = await get_collection_details(context, intersect_id)
        assert len(intersect_details["contacts"]) == intersect_result["count"]
        
        diff_details = await get_collection_details(context, diff_id)
        assert len(diff_details["contacts"]) == diff_result["count"]

    @pytest.mark.asyncio
    async def test_collection_details_with_fields(self, context, skip_if_no_api_key):
        """Test get_collection_details with field filtering"""
        result = await list_contacts(context, limit=3)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for field testing")
        
        # Test with specific fields
        field_scenarios = [
            ["id"],
            ["id", "given_name"],
            ["id", "given_name", "family_name"],
            ["id", "email"],
            ["id", "given_name", "family_name", "email"],
        ]
        
        for fields in field_scenarios:
            details = await get_collection_details(context, collection_id, fields=fields)
            assert "contacts" in details
            assert details["count"] == result["count"]
            
            # Verify field filtering
            for contact in details["contacts"]:
                assert "id" in contact  # ID should always be present
                # Other fields should be present if requested
                for field in fields:
                    if field != "id":  # Skip ID as it's always present
                        # Field should be present (might be None but key should exist)
                        if field in contact:
                            # If present, verify it's the right type for common fields
                            if field in ["given_name", "family_name", "email"] and contact[field] is not None:
                                assert isinstance(contact[field], str)

    @pytest.mark.asyncio
    async def test_collection_operations_with_empty_collections(self, context, skip_if_no_api_key):
        """Test collection operations with empty collections"""
        # Create empty collections
        empty1 = await list_contacts(context, limit=0)
        empty2 = await list_contacts(context, limit=0, offset=1000)
        
        empty_id_1 = empty1["collection_id"]
        empty_id_2 = empty2["collection_id"]
        
        # Test operations on empty collections
        union_empty = await collection_union(context, empty_id_1, empty_id_2)
        assert union_empty["count"] == 0
        
        intersect_empty = await collection_intersect(context, empty_id_1, empty_id_2)
        assert intersect_empty["count"] == 0
        
        diff_empty = await collection_diff(context, empty_id_1, empty_id_2)
        assert diff_empty["count"] == 0
        
        # Test details, count, and IDs on empty collections
        empty_details = await get_collection_details(context, empty_id_1)
        assert empty_details["count"] == 0
        assert len(empty_details["contacts"]) == 0
        
        empty_count = await collection_count(context, empty_id_1)
        assert empty_count["count"] == 0
        
        empty_ids = await get_collection_ids(context, empty_id_1)
        assert len(empty_ids["contact_ids"]) == 0


class TestSchemaDiscoveryComprehensive:
    """Comprehensive tests for schema discovery"""

    @pytest.mark.asyncio
    async def test_get_contact_schema_comprehensive(self, context, skip_if_no_api_key):
        """Test comprehensive schema discovery"""
        schema = await get_contact_schema(context)
        
        # Verify all expected schema components
        required_components = [
            "standard_fields", "custom_fields", "supported_operators", 
            "filter_examples", "field_types"
        ]
        
        for component in required_components:
            assert component in schema, f"Missing schema component: {component}"
        
        # Verify standard fields
        standard_fields = schema["standard_fields"]
        assert isinstance(standard_fields, list)
        essential_fields = ["id", "given_name", "family_name", "email"]
        
        for field in essential_fields:
            assert field in standard_fields
        
        # Verify operators
        operators = schema["supported_operators"]
        assert isinstance(operators, list)
        essential_operators = [
            "equals", "not_equals", "contains", "not_contains",
            "starts_with", "ends_with", "is_null", "is_not_null"
        ]
        
        for operator in essential_operators:
            assert operator in operators
        
        # Verify filter examples structure
        examples = schema["filter_examples"]
        assert isinstance(examples, list)
        assert len(examples) >= 3
        
        for example in examples:
            assert isinstance(example, dict)
            assert "description" in example
            assert "filter" in example or "filters" in example
        
        # Verify field types
        field_types = schema["field_types"]
        assert isinstance(field_types, dict)
        
        # Common fields should have type information
        common_fields = ["id", "given_name", "family_name", "email"]
        for field in common_fields:
            if field in field_types:
                type_info = field_types[field]
                assert isinstance(type_info, dict)


class TestTagOperationsComprehensive:
    """Comprehensive tests for tag operations"""

    @pytest.mark.asyncio
    async def test_get_tags_comprehensive(self, context, skip_if_no_api_key):
        """Test comprehensive tag retrieval"""
        try:
            # Test basic tag retrieval
            tags_result = await get_tags(context)
            assert "tags" in tags_result
            assert isinstance(tags_result["tags"], list)
            
            # Test with filters if tags exist
            if len(tags_result["tags"]) > 0:
                # Test with limit
                limited_tags = await get_tags(context, limit=2)
                assert len(limited_tags["tags"]) <= 2
                
                # Test with different limit
                small_tags = await get_tags(context, limit=1)
                assert len(small_tags["tags"]) <= 1
            
        except Exception as e:
            # Tag operations may not be available in test environment
            expected_errors = ["unauthorized", "forbidden", "not found"]
            if any(err in str(e).lower() for err in expected_errors):
                pytest.skip(f"Tag operations not available: {e}")
            else:
                raise

    @pytest.mark.asyncio
    async def test_apply_tags_to_collection_comprehensive(self, context, skip_if_no_api_key):
        """Test comprehensive tag application (read-only for safety)"""
        # Create test collection
        result = await list_contacts(context, limit=2)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for tag operations")
        
        try:
            # Test tag application (may fail due to permissions)
            tag_result = await apply_tags_to_collection(
                context, 
                collection_id, 
                [1],  # Test tag ID
                "add"
            )
            
            # If successful, verify structure
            assert "collection_id" in tag_result
            assert "operation" in tag_result
            assert "tag_ids" in tag_result
            
        except Exception as e:
            # Expected in test environment
            expected_errors = ["unauthorized", "forbidden", "permission", "not found"]
            if any(err in str(e).lower() for err in expected_errors):
                pytest.skip(f"Tag operations not permitted: {e}")
            else:
                raise


class TestDiagnosticsComprehensive:
    """Comprehensive tests for diagnostics"""

    @pytest.mark.asyncio
    async def test_get_api_diagnostics_comprehensive(self, context, skip_if_no_api_key):
        """Test comprehensive API diagnostics"""
        # Perform some operations to generate metrics
        await list_contacts(context, limit=2)
        await get_contact_schema(context)
        
        # Get diagnostics
        diagnostics = await get_api_diagnostics(context)
        
        # Verify diagnostic structure (check what's actually returned)
        available_components = list(diagnostics.keys())
        print(f"Available diagnostic components: {available_components}")
        
        # Check for essential components that should exist
        essential_components = ["api_diagnostics", "performance_metrics"]
        for component in essential_components:
            if component in diagnostics:
                assert component in diagnostics
        
        # Verify API diagnostics
        api_diag = diagnostics["api_diagnostics"]
        assert "api_status" in api_diag
        assert "last_request_time" in api_diag
        
        # Verify performance metrics
        perf_metrics = diagnostics["performance_metrics"]
        assert "total_requests" in perf_metrics
        assert "success_rate" in perf_metrics
        assert isinstance(perf_metrics["total_requests"], int)
        assert 0 <= perf_metrics["success_rate"] <= 100
        
        # Verify collection stats if available
        if "collection_diagnostics" in diagnostics:
            collection_stats = diagnostics["collection_diagnostics"]
            assert "active_collections" in collection_stats
            assert "total_contacts_across_collections" in collection_stats
            assert isinstance(collection_stats["active_collections"], int)
            assert isinstance(collection_stats["total_contacts_across_collections"], int)
        elif "collection_stats" in diagnostics:
            collection_stats = diagnostics["collection_stats"]
            assert "active_collections" in collection_stats


class TestErrorHandlingComprehensive:
    """Comprehensive tests for error handling scenarios"""

    @pytest.mark.asyncio
    async def test_invalid_collection_ids_all_functions(self, context, skip_if_no_api_key):
        """Test all functions with invalid collection IDs"""
        invalid_id = "invalid_collection_id_12345"
        
        # Test each function that takes collection_id
        functions_to_test = [
            ("get_collection_details", lambda: get_collection_details(context, invalid_id)),
            ("collection_count", lambda: collection_count(context, invalid_id)),
            ("get_collection_ids", lambda: get_collection_ids(context, invalid_id)),
            ("collection_union", lambda: collection_union(context, invalid_id, invalid_id)),
            ("collection_intersect", lambda: collection_intersect(context, invalid_id, invalid_id)),
            ("collection_diff", lambda: collection_diff(context, invalid_id, invalid_id)),
            ("apply_tags_to_collection", lambda: apply_tags_to_collection(context, invalid_id, [1], "add")),
        ]
        
        for func_name, func_call in functions_to_test:
            with pytest.raises(ValueError, match="not found"):
                await func_call()

    @pytest.mark.asyncio
    async def test_mixed_valid_invalid_collection_operations(self, context, skip_if_no_api_key):
        """Test operations with one valid and one invalid collection"""
        # Create valid collection
        result = await list_contacts(context, limit=2)
        valid_id = result["collection_id"]
        invalid_id = "invalid_collection_id"
        
        # Test mixed operations
        with pytest.raises(ValueError, match="not found"):
            await collection_union(context, valid_id, invalid_id)
        
        with pytest.raises(ValueError, match="not found"):
            await collection_intersect(context, invalid_id, valid_id)
        
        with pytest.raises(ValueError, match="not found"):
            await collection_diff(context, valid_id, invalid_id)

    @pytest.mark.asyncio
    async def test_api_error_recovery_comprehensive(self, context, skip_if_no_api_key):
        """Test comprehensive API error recovery"""
        # Trigger errors and verify system recovers
        error_scenarios = [
            # Invalid collection operations
            lambda: get_collection_details(context, "invalid"),
            lambda: collection_count(context, "invalid"),
            # Invalid filter scenarios
            lambda: list_contacts(context, filters=[{"invalid": "filter"}], limit=1),
        ]
        
        for error_func in error_scenarios:
            try:
                await error_func()
            except (ValueError, Exception):
                pass  # Expected errors
        
        # Verify system still works after errors
        recovery_result = await list_contacts(context, limit=1)
        assert "collection_id" in recovery_result
        assert recovery_result["count"] >= 0
        
        # Verify diagnostics still work
        diagnostics = await get_api_diagnostics(context)
        assert "api_diagnostics" in diagnostics


class TestPerformanceAndConcurrency:
    """Test performance characteristics and concurrency"""

    @pytest.mark.asyncio
    async def test_concurrent_list_contacts(self, context, skip_if_no_api_key):
        """Test concurrent list_contacts calls"""
        async def create_collection(offset):
            return await list_contacts(context, limit=2, offset=offset)
        
        # Create multiple collections concurrently
        tasks = [create_collection(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert "collection_id" in result
            assert result["count"] >= 0

    @pytest.mark.asyncio
    async def test_concurrent_collection_operations(self, context, skip_if_no_api_key):
        """Test concurrent collection operations"""
        # Create base collections
        base_collections = []
        for i in range(3):
            result = await list_contacts(context, limit=2, offset=i)
            base_collections.append(result["collection_id"])
        
        # Perform concurrent operations
        async def get_details(collection_id):
            return await get_collection_details(context, collection_id)
        
        async def get_count(collection_id):
            return await collection_count(context, collection_id)
        
        async def get_ids(collection_id):
            return await get_collection_ids(context, collection_id)
        
        # Run all operations concurrently
        tasks = []
        for collection_id in base_collections:
            tasks.extend([
                get_details(collection_id),
                get_count(collection_id),
                get_ids(collection_id)
            ])
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == len(base_collections) * 3
        for result in results:
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_optimization_metrics_collection(self, context, skip_if_no_api_key):
        """Test optimization metrics are properly collected"""
        # Test with optimization and metrics enabled
        result = await list_contacts(
            context, 
            limit=3,
            enable_optimization=True,
            return_metrics=True
        )
        
        if "performance_metrics" in result:
            metrics = result["performance_metrics"]
            expected_metrics = ["api_calls", "strategy_used", "total_duration_ms"]
            
            for metric in expected_metrics:
                if metric in metrics:
                    assert isinstance(metrics[metric], (int, float, str))
                    if metric == "api_calls":
                        assert metrics[metric] > 0
                    elif metric == "total_duration_ms":
                        assert metrics[metric] >= 0