"""
Advanced unit tests for optimization modules - covering missing functionality
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.mcp.optimization.optimization import (
    QueryExecutor,
    QueryOptimizer,
    QueryMetrics,
)
from src.mcp.optimization.api_optimization import (
    ApiParameterOptimizer,
    OptimizationResult,
)


class TestQueryExecutorAdvanced:
    """Test advanced QueryExecutor functionality"""

    @pytest.fixture
    def mock_api_client(self):
        client = AsyncMock()
        client.get_contacts.return_value = {"contacts": [{"id": 1}, {"id": 2}]}
        client.get_tags.return_value = {"tags": [{"id": 10}, {"id": 20}]}
        return client

    @pytest.fixture
    def mock_cache_manager(self):
        cache = MagicMock()
        cache.get.return_value = None  # Cache miss by default
        return cache

    @pytest.fixture
    def query_executor(self, mock_api_client, mock_cache_manager):
        return QueryExecutor(mock_api_client, mock_cache_manager)

    @pytest.mark.asyncio
    async def test_execute_optimized_query_list_contacts(
        self, query_executor, mock_api_client
    ):
        """Test basic optimized query execution for contacts"""
        filters = [{"field": "email", "operator": "=", "value": "test@example.com"}]

        contacts, metrics = await query_executor.execute_optimized_query(
            query_type="list_contacts", filters=filters, limit=50
        )

        assert len(contacts) == 2
        assert isinstance(metrics, QueryMetrics)
        mock_api_client.get_contacts.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_optimized_query_get_tags(
        self, query_executor, mock_api_client
    ):
        """Test optimized query for tags"""
        filters = [{"field": "name", "operator": "contains", "value": "VIP"}]

        tags, metrics = await query_executor.execute_optimized_query(
            query_type="get_tags", filters=filters, limit=100
        )

        assert len(tags) == 2
        assert isinstance(metrics, QueryMetrics)
        mock_api_client.get_tags.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_optimized_query_with_cache_hit(
        self, query_executor, mock_cache_manager
    ):
        """Test optimized query with cache hit"""
        cached_data = [{"id": 1, "cached": True}]
        mock_cache_manager.get.return_value = cached_data

        contacts, metrics = await query_executor.execute_optimized_query(
            query_type="list_contacts", filters=[], limit=50
        )

        assert contacts == cached_data
        assert isinstance(metrics, QueryMetrics)

    def test_generate_cache_key(self, query_executor):
        """Test cache key generation"""
        filters = [{"field": "email", "operator": "=", "value": "test@example.com"}]

        key = query_executor._generate_cache_key(
            query_type="list_contacts", filters=filters, limit=50, offset=10
        )

        assert "list_contacts" in key
        assert isinstance(key, str)
        assert len(key) > 0


class TestQueryOptimizerAdvanced:
    """Test advanced QueryOptimizer functionality"""

    @pytest.fixture
    def optimizer(self):
        return QueryOptimizer()

    def test_analyze_query_basic(self, optimizer):
        """Test basic query analysis"""
        filters = [
            {"field": "email", "operator": "=", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"},
        ]

        strategy = optimizer.analyze_query(filters)
        assert strategy in ["server_optimized", "hybrid", "client_optimized"]

    def test_analyze_query_empty_filters(self, optimizer):
        """Test query analysis with empty filters"""
        strategy = optimizer.analyze_query([])
        assert strategy in ["server_optimized", "hybrid", "client_optimized"]

    def test_analyze_query_complex_filters(self, optimizer):
        """Test query analysis with complex filter types"""
        filters = [
            {
                "type": "group",
                "operator": "AND",
                "conditions": [
                    {"field": "email", "operator": "=", "value": "test@example.com"},
                    {"field": "tag", "operator": "=", "value": "10"},
                ],
            }
        ]

        strategy = optimizer.analyze_query(filters)
        assert strategy in ["server_optimized", "hybrid", "client_optimized"]


class TestApiParameterOptimizerAdvanced:
    """Test advanced ApiParameterOptimizer functionality"""

    @pytest.fixture
    def optimizer(self):
        return ApiParameterOptimizer()

    def test_optimize_contact_query_parameters_basic(self, optimizer):
        """Test basic contact query optimization"""
        filters = [
            {"field": "email", "operator": "=", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"},
        ]

        result = optimizer.optimize_contact_query_parameters(filters)

        assert isinstance(result, OptimizationResult)
        assert hasattr(result, "optimization_strategy")
        assert hasattr(result, "optimization_score")
        assert hasattr(result, "server_side_filters")
        assert hasattr(result, "client_side_filters")

    def test_optimize_tag_query_parameters_basic(self, optimizer):
        """Test basic tag query optimization"""
        filters = [
            {"field": "name", "operator": "contains", "value": "VIP"},
            {"field": "category", "operator": "=", "value": "Status"},
        ]

        result = optimizer.optimize_tag_query_parameters(filters)

        assert isinstance(result, OptimizationResult)
        assert hasattr(result, "optimization_strategy")
        assert hasattr(result, "optimization_score")

    def test_analyze_filter_performance_contact(self, optimizer):
        """Test filter performance analysis for contacts"""
        filters = [
            {"field": "email", "operator": "=", "value": "test@example.com"},
            {"field": "given_name", "operator": "=", "value": "John"},
        ]

        analysis = optimizer.analyze_filter_performance(filters, "contact")

        assert isinstance(analysis, dict)
        assert "performance_rating" in analysis
        assert "estimated_response_time_ms" in analysis
        assert "data_transfer_efficiency" in analysis

    def test_analyze_filter_performance_tag(self, optimizer):
        """Test filter performance analysis for tags"""
        filters = [{"field": "name", "operator": "contains", "value": "VIP"}]

        analysis = optimizer.analyze_filter_performance(filters, "tag")

        assert isinstance(analysis, dict)
        assert "performance_rating" in analysis
        assert "estimated_response_time_ms" in analysis
        assert "data_transfer_efficiency" in analysis

    def test_get_field_optimization_info_contact(self, optimizer):
        """Test field optimization info for contact type"""
        info = optimizer.get_field_optimization_info("contact")

        assert isinstance(info, dict)
        # Should contain information about various contact fields
        assert len(info) > 0

    def test_get_field_optimization_info_tag(self, optimizer):
        """Test field optimization info for tag type"""
        info = optimizer.get_field_optimization_info("tag")

        assert isinstance(info, dict)
        # Should contain information about tag fields
        assert len(info) > 0


class TestQueryMetrics:
    """Test QueryMetrics functionality"""

    def test_query_metrics_creation(self):
        """Test creating query metrics"""
        metrics = QueryMetrics(
            query_type="list_contacts",
            total_duration_ms=150.5,
            api_calls=2,
            cache_hit=False,
            strategy_used="hybrid",
        )

        assert metrics.query_type == "list_contacts"
        assert metrics.total_duration_ms == 150.5
        assert metrics.api_calls == 2
        assert metrics.cache_hit is False
        assert metrics.strategy_used == "hybrid"

    def test_query_metrics_dict_conversion(self):
        """Test converting metrics to dictionary"""
        metrics = QueryMetrics(
            query_type="get_tags",
            total_duration_ms=75.0,
            api_calls=1,
            cache_hit=True,
            strategy_used="server_optimized",
        )

        metrics_dict = metrics.__dict__
        assert metrics_dict["query_type"] == "get_tags"
        assert metrics_dict["total_duration_ms"] == 75.0
        assert metrics_dict["cache_hit"] is True


class TestOptimizationResult:
    """Test OptimizationResult functionality"""

    def test_optimization_result_creation(self):
        """Test creating optimization result"""
        server_filters = [
            {"field": "email", "operator": "=", "value": "test@example.com"}
        ]
        client_filters = [{"field": "tag", "operator": "=", "value": "10"}]

        result = OptimizationResult(
            server_side_filters=server_filters,
            client_side_filters=client_filters,
            optimization_strategy="moderately_optimized",
            optimization_score=0.6,
            estimated_data_reduction_ratio=0.4,
        )

        assert result.server_side_filters == server_filters
        assert result.client_side_filters == client_filters
        assert result.optimization_strategy == "moderately_optimized"
        assert result.optimization_score == 0.6
        assert result.estimated_data_reduction_ratio == 0.4

    def test_optimization_result_empty_filters(self):
        """Test optimization result with empty filters"""
        result = OptimizationResult(
            server_side_filters=[],
            client_side_filters=[],
            optimization_strategy="no_optimization",
            optimization_score=0.0,
            estimated_data_reduction_ratio=0.0,
        )

        assert len(result.server_side_filters) == 0
        assert len(result.client_side_filters) == 0
        assert result.optimization_score == 0.0


# Note: PerformanceAnalysis tests removed as the class is not available in the current implementation
