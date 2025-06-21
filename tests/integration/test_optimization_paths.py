"""
Integration tests targeting specific optimization code paths to improve coverage.

Focus on exercising optimization engine paths and batch operations.
"""

import pytest
import os
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    collection_union,
    collection_intersect,
    collection_diff
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


class TestOptimizationPaths:
    """Test specific optimization code paths"""

    @pytest.mark.asyncio
    async def test_collection_details_optimization_engine_path(self, context, skip_if_no_api_key):
        """Test get_collection_details with optimization engine path (lines 529-553)"""
        # Create collection with enough contacts to potentially trigger optimization
        result = await list_contacts(context, limit=5)
        collection_id = result["collection_id"]
        
        if result["count"] < 2:
            pytest.skip("Need multiple contacts for optimization testing")
        
        # Try to trigger optimization engine path by requesting details
        # This should exercise lines 529-553 if optimization conditions are met
        details = await get_collection_details(
            context, 
            collection_id,
            fields=["id", "given_name", "family_name", "email", "custom_fields"]
        )
        
        assert "contacts" in details
        assert details["count"] == result["count"]
        assert len(details["contacts"]) == result["count"]

    @pytest.mark.asyncio
    async def test_list_contacts_complex_filter_optimization(self, context, skip_if_no_api_key):
        """Test list_contacts with complex filters to trigger optimization paths"""
        # Test with multiple filters that might trigger different optimization strategies
        complex_filter_scenarios = [
            # Single field filters
            [{"field": "email", "operator": "not_equals", "value": ""}],
            [{"field": "given_name", "operator": "not_equals", "value": ""}],
            
            # Multiple field filters (might trigger hybrid optimization)
            [
                {"field": "email", "operator": "not_equals", "value": ""},
                {"field": "given_name", "operator": "not_equals", "value": ""}
            ],
            
            # Complex operator combinations
            [{"field": "email", "operator": "contains", "value": "@"}],
            [{"field": "given_name", "operator": "starts_with", "value": "A"}],
            [{"field": "family_name", "operator": "ends_with", "value": "son"}],
        ]
        
        for filters in complex_filter_scenarios:
            try:
                result = await list_contacts(
                    context,
                    filters=filters,
                    limit=4,
                    enable_optimization=True,
                    return_metrics=True
                )
                
                assert "collection_id" in result
                assert result["count"] >= 0
                
                # Check if optimization metrics were generated
                if "performance_metrics" in result:
                    metrics = result["performance_metrics"]
                    assert "strategy_used" in metrics
                    
            except Exception as e:
                # Some complex filters might not be supported
                expected_errors = ["invalid", "unsupported", "bad request"]
                if not any(err in str(e).lower() for err in expected_errors):
                    raise

    @pytest.mark.asyncio
    async def test_collection_operations_with_optimization_paths(self, context, skip_if_no_api_key):
        """Test collection operations that might trigger optimization"""
        # Create collections of different sizes to potentially trigger different optimization paths
        small_result = await list_contacts(context, limit=2)
        medium_result = await list_contacts(context, limit=4, offset=1)
        large_result = await list_contacts(context, limit=6, offset=2)
        
        collections = [
            (small_result["collection_id"], "small"),
            (medium_result["collection_id"], "medium"), 
            (large_result["collection_id"], "large")
        ]
        
        # Test operations between different sized collections
        for i, (col_a, size_a) in enumerate(collections):
            for j, (col_b, size_b) in enumerate(collections):
                if i != j:  # Don't test collection with itself
                    # Test union (might trigger optimization for large collections)
                    union_result = await collection_union(context, col_a, col_b)
                    assert "collection_id" in union_result
                    assert union_result["count"] >= 0
                    
                    # Test intersection (might have different optimization path)
                    intersect_result = await collection_intersect(context, col_a, col_b)
                    assert "collection_id" in intersect_result
                    assert intersect_result["count"] >= 0
                    
                    # Test difference (might have another optimization path)
                    diff_result = await collection_diff(context, col_a, col_b)
                    assert "collection_id" in diff_result
                    assert diff_result["count"] >= 0

    @pytest.mark.asyncio
    async def test_batch_operations_with_different_strategies(self, context, skip_if_no_api_key):
        """Test batch operations that might use different strategies"""
        # Create collection with specific characteristics
        result = await list_contacts(context, limit=5)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for batch operation testing")
        
        # Test get_collection_details with different field combinations that might trigger
        # different batch strategies
        field_combinations = [
            # Basic fields (might use simple strategy)
            ["id", "given_name"],
            
            # Fields including custom data (might trigger enhanced strategy)
            ["id", "given_name", "custom_fields"],
            
            # Comprehensive fields (might trigger full optimization)
            ["id", "given_name", "family_name", "email", "custom_fields", "tag_ids"],
        ]
        
        for fields in field_combinations:
            details = await get_collection_details(context, collection_id, fields=fields)
            assert "contacts" in details
            assert details["count"] == result["count"]
            
            # Verify field filtering worked
            for contact in details["contacts"]:
                assert "id" in contact
                # Should have some of the requested fields
                contact_fields = set(contact.keys())
                requested_fields = set(fields)
                # At least id should match
                assert "id" in contact_fields.intersection(requested_fields)

    @pytest.mark.asyncio  
    async def test_optimization_with_different_limits(self, context, skip_if_no_api_key):
        """Test optimization behavior with different limit values"""
        # Test with various limits that might trigger different optimization thresholds
        limit_scenarios = [
            1,   # Very small - might use simple strategy
            3,   # Small - might use basic optimization  
            5,   # Medium - might use enhanced optimization
            8,   # Larger - might use full optimization
        ]
        
        for limit in limit_scenarios:
            # Test basic list_contacts
            result = await list_contacts(
                context,
                limit=limit,
                enable_optimization=True,
                return_metrics=True
            )
            
            assert "collection_id" in result
            assert result["count"] >= 0
            
            # Test collection details if we have contacts
            if result["count"] > 0:
                details = await get_collection_details(
                    context,
                    result["collection_id"],
                    fields=["id", "given_name", "email"]
                )
                assert "contacts" in details
                assert len(details["contacts"]) == result["count"]

    @pytest.mark.asyncio
    async def test_error_recovery_in_optimization_paths(self, context, skip_if_no_api_key):
        """Test error recovery in optimization code paths"""
        # Create valid collection
        result = await list_contacts(context, limit=3)
        collection_id = result["collection_id"]
        
        # Test optimization with potential error conditions
        error_scenarios = [
            # Large field list that might cause issues
            ["id", "given_name", "family_name", "email", "phone", "address", 
             "city", "state", "zip", "country", "custom_fields", "tag_ids"],
            
            # Field combinations that might not be supported
            ["id", "invalid_field_name"],
        ]
        
        for fields in error_scenarios:
            try:
                details = await get_collection_details(context, collection_id, fields=fields)
                # If successful, verify basic structure
                assert "contacts" in details
                assert "count" in details
                
            except Exception as e:
                # Some field combinations might fail, but should be handled gracefully
                if "field" not in str(e).lower() and "invalid" not in str(e).lower():
                    raise

    @pytest.mark.asyncio
    async def test_optimization_caching_behavior(self, context, skip_if_no_api_key):
        """Test optimization caching behavior"""
        # Create collection
        result = await list_contacts(context, limit=3)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for caching test")
        
        # Call the same operation multiple times to test caching behavior
        for i in range(3):
            details = await get_collection_details(
                context,
                collection_id,
                fields=["id", "given_name", "family_name"]
            )
            
            assert "contacts" in details
            assert details["count"] == result["count"]
            
            # Results should be consistent across calls
            if i == 0:
                first_result = details
            else:
                # Verify consistency (same contacts, same count)
                assert details["count"] == first_result["count"]
                if details["count"] > 0:
                    # Contact IDs should be the same
                    first_ids = {c["id"] for c in first_result["contacts"]}
                    current_ids = {c["id"] for c in details["contacts"]}
                    assert first_ids == current_ids