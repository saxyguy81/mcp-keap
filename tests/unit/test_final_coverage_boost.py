"""
Final tests to boost coverage over 90%.

Targets specific uncovered lines in key modules.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.optimization.api_optimization import ApiParameterOptimizer
from src.mcp.optimization.optimization import QueryOptimizer, QueryStrategy
from src.api.client import KeapApiService


class TestFinalCoverageBoost:
    """Additional tests to reach 90% coverage."""

    def test_api_parameter_optimizer_edge_cases(self):
        """Test ApiParameterOptimizer edge cases for coverage."""
        optimizer = ApiParameterOptimizer()
        
        # Test IN operator with large list (line 149-160)
        filters = [{"field": "id", "operator": "IN", "value": list(range(10))}]
        result = optimizer.optimize_contact_query_parameters(filters)
        
        assert isinstance(result.server_side_filters, dict)
        assert isinstance(result.client_side_filters, list)
        
        # Test empty contact values - get_field_optimization_info edge case
        field_info = optimizer.get_field_optimization_info("unknown_type")
        assert field_info == {}

    def test_query_optimizer_performance_summary_edge_cases(self):
        """Test QueryOptimizer performance summary edge cases."""
        optimizer = QueryOptimizer()
        
        # Test with no performance data (line 173-174)
        summary = optimizer.get_performance_summary()
        assert "message" in summary
        assert summary["message"] == "No performance data available"
        
        # Test with specific query key that doesn't exist
        summary = optimizer.get_performance_summary("nonexistent_key")
        assert "message" in summary

    def test_query_strategy_coverage(self):
        """Test QueryStrategy enum for full coverage."""
        # Ensure all enum values are accessible
        strategies = [
            QueryStrategy.CACHED_RESULT,
            QueryStrategy.SERVER_OPTIMIZED,
            QueryStrategy.TAG_OPTIMIZED,
            QueryStrategy.BULK_RETRIEVE,
            QueryStrategy.HYBRID
        ]
        
        assert len(strategies) == 5
        assert all(isinstance(strategy, str) for strategy in strategies)

    @pytest.mark.asyncio
    async def test_api_client_edge_cases(self):
        """Test KeapApiService edge cases for coverage."""
        with patch.dict('os.environ', {'KEAP_API_KEY': 'test_key'}):
            client = KeapApiService()
            
            # Test close session when no session exists
            client.session = None
            await client.close()  # Should not raise error
            
            # Test diagnostics update methods
            client._update_diagnostics_success(100, retried=True)
            client._update_diagnostics_failure("test_error", retried=True)
            
            diagnostics = client.get_diagnostics()
            assert "retried_requests" in diagnostics

    def test_api_parameter_optimizer_contains_filtering(self):
        """Test specific contains filtering logic."""
        optimizer = ApiParameterOptimizer()
        
        # Test CONTAINS operator for non-email fields
        filters = [
            {"field": "given_name", "operator": "CONTAINS", "value": "John"},
            {"field": "family_name", "operator": "CONTAINS", "value": "Smith"}
        ]
        
        result = optimizer.optimize_contact_query_parameters(filters)
        assert len(result.server_side_filters) == 2

    def test_query_optimizer_analyze_query_edge_cases(self):
        """Test QueryOptimizer analyze_query edge cases."""
        optimizer = QueryOptimizer()
        
        # Test with multiple tag filters to trigger TAG_OPTIMIZED
        filters = [
            {"field": "tags", "operator": "=", "value": "VIP"},
            {"field": "tag_id", "operator": "=", "value": 123},
            {"field": "tag_ids", "operator": "=", "value": [1, 2, 3]}
        ]
        
        strategy = optimizer.analyze_query(filters)
        assert strategy == QueryStrategy.TAG_OPTIMIZED

    def test_optimization_result_all_fields(self):
        """Test OptimizationResult with all fields set."""
        from src.mcp.optimization.api_optimization import OptimizationResult
        
        result = OptimizationResult(
            optimization_strategy="test",
            server_side_filters={"field": "value"},
            client_side_filters=[{"field": "client"}],
            estimated_data_reduction_ratio=0.8,
            optimization_score=0.9
        )
        
        # Test all fields are accessible
        assert result.optimization_strategy == "test"
        assert "field" in result.server_side_filters
        assert len(result.client_side_filters) == 1
        assert result.estimated_data_reduction_ratio == 0.8
        assert result.optimization_score == 0.9

    def test_api_parameter_optimizer_performance_ratings(self):
        """Test performance rating calculations."""
        optimizer = ApiParameterOptimizer()
        
        # Test all performance rating thresholds
        ratings = [
            (0.9, "Excellent"),
            (0.7, "Good"), 
            (0.5, "Fair"),
            (0.3, "Poor"),
            (0.1, "Very Poor")
        ]
        
        for score, expected_rating in ratings:
            rating = optimizer._get_performance_rating(score)
            assert rating == expected_rating