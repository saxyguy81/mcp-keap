"""
Integration Tests for Optimization Strategy Selection

Tests that the optimization engine selects appropriate strategies for different
filter types and that results are consistent between optimization paths.
"""

import pytest
from mcp.server.fastmcp import Context
from src.mcp.tools_collections import list_contacts
from src.mcp.optimization.optimization import QueryOptimizer, QueryStrategy


class TestOptimizationStrategySelection:
    """Test optimization strategy selection logic"""

    def test_email_filter_strategy_selection(self):
        """Test that email filters select BULK_RETRIEVE strategy"""
        optimizer = QueryOptimizer()
        
        # Email filters should use BULK_RETRIEVE for email_addresses array handling
        email_filters = [{"field": "email", "operator": "contains", "value": "test"}]
        strategy = optimizer.analyze_query(email_filters, limit=10)
        
        assert strategy == QueryStrategy.BULK_RETRIEVE, \
            f"Email filters should use BULK_RETRIEVE, got {strategy}"

    def test_custom_field_strategy_selection(self):
        """Test that custom field filters select BULK_RETRIEVE strategy"""
        optimizer = QueryOptimizer()
        
        # Custom field filters should use BULK_RETRIEVE for client-side processing
        custom_field_filters = [{"field": "custom_fields.239", "operator": "equals", "value": "test"}]
        strategy = optimizer.analyze_query(custom_field_filters, limit=10)
        
        assert strategy == QueryStrategy.BULK_RETRIEVE, \
            f"Custom field filters should use BULK_RETRIEVE, got {strategy}"

    def test_standard_field_strategy_selection(self):
        """Test that standard fields can use server optimization"""
        optimizer = QueryOptimizer()
        
        # Standard name fields should allow server optimization
        name_filters = [{"field": "given_name", "operator": "contains", "value": "John"}]
        strategy = optimizer.analyze_query(name_filters, limit=10)
        
        assert strategy == QueryStrategy.SERVER_OPTIMIZED, \
            f"Standard field filters should use SERVER_OPTIMIZED, got {strategy}"

    def test_mixed_filter_strategy_selection(self):
        """Test strategy selection with mixed filter types"""
        optimizer = QueryOptimizer()
        
        # Mixed filters (email + name) should use BULK_RETRIEVE due to email
        mixed_filters = [
            {"field": "given_name", "operator": "contains", "value": "Scott"},
            {"field": "email", "operator": "contains", "value": "gmail"}
        ]
        strategy = optimizer.analyze_query(mixed_filters, limit=10)
        
        assert strategy == QueryStrategy.BULK_RETRIEVE, \
            f"Mixed filters with email should use BULK_RETRIEVE, got {strategy}"

    def test_server_optimizable_count(self):
        """Test server-optimizable filter counting"""
        optimizer = QueryOptimizer()
        
        # Email and custom fields should not be server-optimizable
        filters = [
            {"field": "email", "operator": "contains", "value": "test"},  # Not server-optimizable
            {"field": "custom_fields.239", "operator": "equals", "value": "test"},  # Not server-optimizable
            {"field": "given_name", "operator": "contains", "value": "John"},  # Server-optimizable
            {"field": "family_name", "operator": "equals", "value": "Doe"}  # Server-optimizable
        ]
        
        count = optimizer._count_server_optimizable_filters(filters)
        assert count == 2, f"Should count 2 server-optimizable filters, got {count}"


class TestOptimizationConsistency:
    """Test consistency between optimization engine and client-side filtering"""

    @pytest.mark.asyncio
    async def test_email_filtering_consistency(self):
        """Test that optimization engine and client-side produce same email results"""
        context = Context()
        
        test_filters = [
            {"field": "email", "operator": "contains", "value": "@gmail.com"},
            {"field": "email", "operator": "is_not_null", "value": ""},
            {"field": "email", "operator": "equals", "value": "smhanan@gmail.com"}
        ]
        
        for test_filter in test_filters:
            # Test client-side
            client_result = await list_contacts(
                context,
                filters=[test_filter],
                limit=10,
                enable_optimization=False
            )
            
            # Test optimization engine
            opt_result = await list_contacts(
                context,
                filters=[test_filter],
                limit=10,
                enable_optimization=True
            )
            
            assert client_result["count"] == opt_result["count"], \
                f"Filter {test_filter}: Client-side ({client_result['count']}) != Optimization ({opt_result['count']})"

    @pytest.mark.asyncio
    async def test_combined_filtering_consistency(self):
        """Test consistency with combined filters"""
        context = Context()
        
        combined_filters = [
            {"field": "given_name", "operator": "contains", "value": "Scott"},
            {"field": "email", "operator": "contains", "value": "smhanan"}
        ]
        
        # Test client-side
        client_result = await list_contacts(
            context,
            filters=combined_filters,
            limit=15,
            enable_optimization=False
        )
        
        # Test optimization engine
        opt_result = await list_contacts(
            context,
            filters=combined_filters,
            limit=15,
            enable_optimization=True
        )
        
        assert client_result["count"] == opt_result["count"], \
            f"Combined filters: Client-side ({client_result['count']}) != Optimization ({opt_result['count']})"
        
        # Both should find the known Scott+smhanan contacts
        assert client_result["count"] >= 10, "Should find at least 10 Scott+smhanan contacts"

    @pytest.mark.asyncio
    async def test_strategy_metrics_reporting(self):
        """Test that optimization engine reports correct strategy in metrics"""
        context = Context()
        
        # Email filter should use BULK_RETRIEVE
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "test"}],
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        
        metrics = result.get("performance_metrics", {})
        strategy = metrics.get("strategy_used", "")
        
        assert "BULK_RETRIEVE" in str(strategy), \
            f"Email filter should report BULK_RETRIEVE strategy, got {strategy}"
        
        # Should report API calls were made
        api_calls = metrics.get("api_calls", 0)
        assert api_calls > 0, "Should report API calls were made"

    @pytest.mark.asyncio
    async def test_field_name_resolution_in_optimization(self):
        """Test that field name resolution works in optimization engine"""
        context = Context()
        
        # Use field name instead of field ID
        result = await list_contacts(
            context,
            filters=[{"field": "6FN Next Date/Time", "operator": "is_not_null", "value": ""}],
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        
        # Should not error (even if no results found)
        assert "count" in result, "Should return valid result structure"
        
        metrics = result.get("performance_metrics", {})
        strategy = metrics.get("strategy_used", "")
        
        # Custom field should use BULK_RETRIEVE
        assert "BULK_RETRIEVE" in str(strategy), \
            f"Custom field filter should use BULK_RETRIEVE, got {strategy}"


class TestOptimizationPerformance:
    """Test optimization engine performance characteristics"""

    @pytest.mark.asyncio
    async def test_bulk_retrieve_comprehensive_search(self):
        """Test that BULK_RETRIEVE strategy performs comprehensive search"""
        context = Context()
        
        # Search for smhanan (we know these exist but are in newer part of database)
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "smhanan"}],
            limit=15,
            enable_optimization=True,
            return_metrics=True
        )
        
        # Should find all smhanan contacts
        assert result["count"] >= 10, f"Should find at least 10 smhanan contacts, got {result['count']}"
        
        metrics = result.get("performance_metrics", {})
        strategy = metrics.get("strategy_used", "")
        api_calls = metrics.get("api_calls", 0)
        
        assert "BULK_RETRIEVE" in str(strategy), "Should use BULK_RETRIEVE for comprehensive search"
        assert api_calls >= 1, "Should make API calls for search"

    @pytest.mark.asyncio
    async def test_no_filter_fallback(self):
        """Test behavior with no filters (should use BULK_RETRIEVE)"""
        context = Context()
        
        result = await list_contacts(
            context,
            filters=[],
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        
        assert result["count"] > 0, "Should find contacts with no filters"
        
        metrics = result.get("performance_metrics", {})
        strategy = metrics.get("strategy_used", "")
        
        # No filters should default to BULK_RETRIEVE
        assert "BULK_RETRIEVE" in str(strategy), \
            f"No filters should use BULK_RETRIEVE, got {strategy}"