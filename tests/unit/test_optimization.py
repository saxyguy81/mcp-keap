"""
Unit tests for the optimization engine.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp.optimization.api_optimization import ApiParameterOptimizer, OptimizationResult
from src.mcp.optimization.optimization import QueryOptimizer, QueryExecutor, QueryMetrics


class TestApiParameterOptimizer:
    """Test API parameter optimization functionality."""
    
    def test_init(self):
        """Test optimizer initialization."""
        optimizer = ApiParameterOptimizer()
        assert optimizer.contact_field_mappings is not None
        assert optimizer.tag_field_mappings is not None
        assert len(optimizer.contact_field_mappings) > 0
        assert len(optimizer.tag_field_mappings) > 0
    
    def test_optimize_contact_query_parameters_server_optimizable(self):
        """Test optimization of server-optimizable contact query."""
        optimizer = ApiParameterOptimizer()
        
        filters = [
            {"field": "email", "operator": "CONTAINS", "value": "@company.com"},
            {"field": "given_name", "operator": "EQUALS", "value": "John"}
        ]
        
        result = optimizer.optimize_contact_query_parameters(filters)
        
        assert isinstance(result, OptimizationResult)
        assert result.optimization_strategy in ["highly_optimized", "moderately_optimized"]
        assert len(result.server_side_filters) == 2
        assert len(result.client_side_filters) == 0
        assert result.optimization_score == 1.0
    
    def test_optimize_contact_query_parameters_mixed(self):
        """Test optimization of mixed contact query."""
        optimizer = ApiParameterOptimizer()
        
        filters = [
            {"field": "email", "operator": "CONTAINS", "value": "@company.com"},
            {"field": "custom_field", "operator": "EQUALS", "value": "VIP"}
        ]
        
        result = optimizer.optimize_contact_query_parameters(filters)
        
        assert result.optimization_strategy in ["moderately_optimized", "partially_optimized"]
        assert len(result.server_side_filters) == 1
        assert len(result.client_side_filters) == 1
        assert result.optimization_score == 0.5
    
    def test_optimize_contact_query_parameters_client_only(self):
        """Test optimization of client-only contact query."""
        optimizer = ApiParameterOptimizer()
        
        filters = [
            {"field": "custom_field", "operator": "EQUALS", "value": "VIP"},
            {"field": "tags", "operator": "CONTAINS", "value": "customer"}
        ]
        
        result = optimizer.optimize_contact_query_parameters(filters)
        
        assert result.optimization_strategy == "minimal_optimization"
        assert len(result.server_side_filters) == 0
        assert len(result.client_side_filters) == 2
        assert result.optimization_score == 0.0
    
    def test_optimize_tag_query_parameters(self):
        """Test tag query optimization."""
        optimizer = ApiParameterOptimizer()
        
        filters = [
            {"field": "name", "operator": "CONTAINS", "value": "VIP"},
            {"field": "category", "operator": "EQUALS", "value": "123"}
        ]
        
        result = optimizer.optimize_tag_query_parameters(filters)
        
        assert isinstance(result, OptimizationResult)
        assert result.optimization_strategy in ["highly_optimized", "moderately_optimized"]
    
    def test_analyze_filter_performance_excellent(self):
        """Test performance analysis for excellent filters."""
        optimizer = ApiParameterOptimizer()
        
        filters = [
            {"field": "email", "operator": "EQUALS", "value": "specific@email.com"}
        ]
        
        analysis = optimizer.analyze_filter_performance(filters, "contact")
        
        assert analysis["performance_rating"] == "Excellent"
        assert analysis["optimization_score"] == 1.0
    
    def test_analyze_filter_performance_poor(self):
        """Test performance analysis for poor filters."""
        optimizer = ApiParameterOptimizer()
        
        filters = [
            {"field": "custom_field", "operator": "CONTAINS", "value": "a"}
        ]
        
        analysis = optimizer.analyze_filter_performance(filters, "contact")
        
        assert analysis["performance_rating"] == "Very Poor"
        assert analysis["optimization_score"] == 0.0
    
    def test_get_field_optimization_info_contact(self):
        """Test getting field optimization info for contacts."""
        optimizer = ApiParameterOptimizer()
        
        info = optimizer.get_field_optimization_info("contact")
        
        assert "email" in info
        assert "given_name" in info
        assert info["email"]["api_field"] == "email"
        assert "EQUALS" in info["email"]["supported_operators"]
    
    def test_get_field_optimization_info_tag(self):
        """Test getting field optimization info for tags."""
        optimizer = ApiParameterOptimizer()
        
        info = optimizer.get_field_optimization_info("tag")
        
        assert "name" in info
        assert "id" in info
        assert info["name"]["api_field"] == "name"
        assert "EQUALS" in info["name"]["supported_operators"]
    
    def test_get_field_optimization_info_unknown(self):
        """Test getting field optimization info for unknown type."""
        optimizer = ApiParameterOptimizer()
        
        info = optimizer.get_field_optimization_info("unknown")
        
        assert info == {}


class TestQueryOptimizer:
    """Test query optimization logic."""
    
    def test_init(self):
        """Test query optimizer initialization."""
        optimizer = QueryOptimizer()
        assert hasattr(optimizer, 'analyze_query')
        assert hasattr(optimizer, 'performance_history')
        assert hasattr(optimizer, 'strategy_scores')
        assert len(optimizer.strategy_scores) > 0
    
    def test_analyze_query_simple(self):
        """Test analysis of simple query."""
        optimizer = QueryOptimizer()
        
        filters = [
            {"field": "email", "operator": "EQUALS", "value": "test@example.com"}
        ]
        
        strategy = optimizer.analyze_query(filters)
        
        assert strategy in ["server_optimized", "hybrid"]
    
    def test_analyze_query_complex(self):
        """Test analysis of complex query."""
        optimizer = QueryOptimizer()
        
        filters = [
            {"field": "email", "operator": "CONTAINS", "value": "@company.com"},
            {"field": "custom_field", "operator": "EQUALS", "value": "VIP"},
            {
                "operator": "OR",
                "conditions": [
                    {"field": "given_name", "operator": "EQUALS", "value": "John"},
                    {"field": "family_name", "operator": "EQUALS", "value": "Doe"}
                ]
            }
        ]
        
        strategy = optimizer.analyze_query(filters)
        
        assert strategy == "hybrid"
    
    def test_analyze_query_empty(self):
        """Test analysis of empty query."""
        optimizer = QueryOptimizer()
        
        strategy = optimizer.analyze_query([])
        
        assert strategy == "bulk_retrieve"


class TestQueryMetrics:
    """Test query metrics functionality."""
    
    def test_init(self):
        """Test metrics initialization."""
        metrics = QueryMetrics(
            total_duration_ms=0,
            api_calls=0,
            cache_hit=False,
            strategy_used="",
            filters_applied=0,
            results_count=0,
            server_side_filters=0,
            client_side_filters=0,
            optimization_ratio=0.0
        )
        
        assert metrics.total_duration_ms == 0
        assert metrics.api_calls == 0
        assert metrics.cache_hit is False
        assert metrics.strategy_used == ""
        assert metrics.filters_applied == 0
        assert metrics.server_side_filters == 0
        assert metrics.client_side_filters == 0
        assert metrics.optimization_ratio == 0.0
    
    def test_calculate_optimization_ratio(self):
        """Test optimization ratio calculation."""
        metrics = QueryMetrics(
            total_duration_ms=100,
            api_calls=1,
            cache_hit=False,
            strategy_used="hybrid",
            filters_applied=5,
            results_count=10,
            server_side_filters=3,
            client_side_filters=2,
            optimization_ratio=0.6
        )
        
        expected = 0.6
        assert metrics.optimization_ratio == expected
    
    def test_calculate_optimization_ratio_no_filters(self):
        """Test optimization ratio with no filters."""
        metrics = QueryMetrics(
            total_duration_ms=100,
            api_calls=1,
            cache_hit=False,
            strategy_used="bulk_retrieve",
            filters_applied=0,
            results_count=10,
            server_side_filters=0,
            client_side_filters=0,
            optimization_ratio=0.0
        )
        
        assert metrics.optimization_ratio == 0.0


class TestQueryExecutor:
    """Test query execution functionality."""
    
    def test_init(self):
        """Test executor initialization."""
        mock_api_client = MagicMock()
        mock_cache_manager = MagicMock()
        
        executor = QueryExecutor(mock_api_client, mock_cache_manager)
        
        assert executor.api_client == mock_api_client
        assert executor.cache_manager == mock_cache_manager
        assert isinstance(executor.optimizer, QueryOptimizer)
    
    @pytest.mark.asyncio
    async def test_execute_optimized_query_direct_api(self):
        """Test execution with bulk retrieve strategy."""
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        # Mock API response
        mock_contacts = [{"id": 1, "name": "Test"}]
        mock_api_client.get_contacts.return_value = {"contacts": mock_contacts}
        
        executor = QueryExecutor(mock_api_client, mock_cache_manager)
        
        with patch.object(executor.optimizer, 'analyze_query', return_value='bulk_retrieve'):
            with patch.object(executor, '_execute_bulk_retrieve', return_value=(mock_contacts, 1, 0, 0)):
                contacts, metrics = await executor.execute_optimized_query(
                    'list_contacts', 
                    filters=[{"field": "email", "operator": "EQUALS", "value": "test@example.com"}],
                    limit=50
                )
        
        assert contacts == mock_contacts
        assert metrics.api_calls == 1
        assert metrics.strategy_used == 'bulk_retrieve'
        assert not metrics.cache_hit
    
    @pytest.mark.asyncio
    async def test_execute_optimized_query_cached_lookup(self):
        """Test execution with cached lookup strategy."""
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        # Mock cache hit
        mock_contacts = [{"id": 1, "name": "Cached"}]
        mock_cache_manager.get.return_value = mock_contacts
        
        executor = QueryExecutor(mock_api_client, mock_cache_manager)
        
        contacts, metrics = await executor.execute_optimized_query(
            'list_contacts',
            filters=[{"field": "email", "operator": "EQUALS", "value": "test@example.com"}],
            limit=50
        )
        
        assert contacts == mock_contacts
        assert metrics.api_calls == 0
        assert metrics.strategy_used == 'cached_result'
        assert metrics.cache_hit
    
    @pytest.mark.asyncio
    async def test_execute_optimized_query_hybrid_optimization(self):
        """Test execution with hybrid optimization strategy."""
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        # Mock API response
        mock_contacts = [
            {"id": 1, "name": "Test1", "custom_fields": [{"id": 7, "content": "VIP"}]},
            {"id": 2, "name": "Test2", "custom_fields": [{"id": 7, "content": "Regular"}]}
        ]
        mock_api_client.get_contacts.return_value = {"contacts": mock_contacts}
        
        # Mock cache miss
        mock_cache_manager.get.return_value = None
        
        executor = QueryExecutor(mock_api_client, mock_cache_manager)
        
        # Mock optimization result
        mock_optimization = OptimizationResult(
            server_side_filters=[{"field": "email", "operator": "contains", "value": "@test.com"}],
            client_side_filters=[{"field": "custom_field", "operator": "equals", "value": "VIP"}],
            optimization_strategy="hybrid",
            optimization_score=0.5,
            estimated_data_reduction_ratio=0.3
        )
        
        with patch.object(executor.optimizer, 'analyze_query', return_value='hybrid'):
            with patch.object(executor.api_optimizer, 'optimize_contact_query_parameters', return_value=mock_optimization):
                with patch('src.utils.contact_utils.get_custom_field_value', return_value="VIP"):
                    with patch('src.utils.contact_utils.format_contact_data', side_effect=lambda x: x):
                        with patch('time.time', side_effect=[0, 150]):  # 150ms duration
                            contacts, metrics = await executor.execute_optimized_query(
                                'list_contacts',
                                filters=[
                                    {"field": "email", "operator": "contains", "value": "@test.com"},
                                    {"field": "custom_field", "operator": "equals", "value": "VIP"}
                                ],
                                limit=50
                            )
        
        assert len(contacts) == 1  # Only VIP contact should match
        assert contacts[0]["id"] == 1
        assert metrics.total_duration_ms == 150
        assert metrics.api_calls == 1
        assert metrics.strategy_used == 'hybrid'
        assert not metrics.cache_hit
        assert metrics.server_side_filters == 1
        assert metrics.client_side_filters == 1
    
    @pytest.mark.asyncio
    async def test_execute_optimized_query_exception(self):
        """Test execution with exception handling."""
        mock_api_client = AsyncMock()
        mock_cache_manager = AsyncMock()
        
        # Mock API exception
        mock_api_client.get_contacts.side_effect = Exception("API Error")
        
        executor = QueryExecutor(mock_api_client, mock_cache_manager)
        
        with patch.object(executor.optimizer, 'analyze_query', return_value='bulk_retrieve'):
            with pytest.raises(Exception, match="API Error"):
                await executor.execute_optimized_query(
                    'list_contacts',
                    filters=[],
                    limit=50
                )
    
    def test_generate_cache_key(self):
        """Test cache key generation."""
        mock_api_client = MagicMock()
        mock_cache_manager = MagicMock()
        
        executor = QueryExecutor(mock_api_client, mock_cache_manager)
        
        filters = [{"field": "email", "operator": "=", "value": "test@example.com"}]
        
        key1 = executor._generate_cache_key('list_contacts', filters, 50, 0, 'email', 'ASC')
        key2 = executor._generate_cache_key('list_contacts', filters, 50, 0, 'email', 'ASC')
        key3 = executor._generate_cache_key('list_contacts', filters, 100, 0, 'email', 'ASC')  # Different limit
        
        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different parameters should generate different key
        assert key1.startswith('query:')
    
    @pytest.mark.asyncio
    async def test_apply_client_side_filters(self):
        """Test client-side filter application."""
        mock_api_client = MagicMock()
        mock_cache_manager = MagicMock()
        
        executor = QueryExecutor(mock_api_client, mock_cache_manager)
        
        contacts = [
            {"id": 1, "custom_fields": [{"id": 7, "content": "VIP"}]},
            {"id": 2, "custom_fields": [{"id": 7, "content": "Regular"}]},
            {"id": 3, "custom_fields": [{"id": 8, "content": "VIP"}]}  # Different field
        ]
        
        filters = [{"field": "custom_field", "operator": "equals", "value": "VIP", "field_id": "7"}]
        
        with patch('src.utils.contact_utils.get_custom_field_value') as mock_get_field:
            # Mock field values: VIP, Regular, None (different field)
            mock_get_field.side_effect = ["VIP", "Regular", None]
            
            filtered_contacts = await executor._apply_client_side_filters(contacts, filters)
        
        assert len(filtered_contacts) == 1
        assert filtered_contacts[0]["id"] == 1


class TestOptimizationResult:
    """Test OptimizationResult data class."""
    
    def test_init(self):
        """Test OptimizationResult initialization."""
        result = OptimizationResult(
            server_side_filters=[{"field": "email"}],
            client_side_filters=[{"field": "custom"}],
            optimization_strategy="hybrid",
            optimization_score=0.6,
            estimated_data_reduction_ratio=0.4
        )
        
        assert len(result.server_side_filters) == 1
        assert len(result.client_side_filters) == 1
        assert result.optimization_strategy == "hybrid"
        assert result.optimization_score == 0.6
        assert result.estimated_data_reduction_ratio == 0.4