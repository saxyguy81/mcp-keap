"""
Core Query Optimization Framework

Provides intelligent query strategy selection and execution optimization
for Keap CRM operations with performance monitoring and adaptive learning.
"""

import logging
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class QueryStrategy(str, Enum):
    """Available query optimization strategies."""

    CACHED_RESULT = "cached_result"
    SERVER_OPTIMIZED = "server_optimized"
    TAG_OPTIMIZED = "tag_optimized"
    BULK_RETRIEVE = "bulk_retrieve"
    HYBRID = "hybrid"


@dataclass
class QueryMetrics:
    """Query performance metrics."""

    total_duration_ms: float
    api_calls: int
    cache_hit: bool
    strategy_used: str
    filters_applied: int
    results_count: int
    server_side_filters: int
    client_side_filters: int
    optimization_ratio: float


@dataclass
class OptimizationHint:
    """Hints for query optimization."""

    preferred_strategy: Optional[QueryStrategy] = None
    enable_caching: bool = True
    max_api_calls: Optional[int] = None
    estimated_result_size: Optional[int] = None


class QueryOptimizer:
    """
    Intelligent query optimizer that selects optimal execution strategies
    based on query characteristics and performance history.
    """

    def __init__(self):
        self.performance_history: Dict[str, List[QueryMetrics]] = {}
        self.strategy_scores: Dict[QueryStrategy, float] = {
            QueryStrategy.CACHED_RESULT: 1.0,
            QueryStrategy.SERVER_OPTIMIZED: 0.8,
            QueryStrategy.TAG_OPTIMIZED: 0.7,
            QueryStrategy.BULK_RETRIEVE: 0.5,
            QueryStrategy.HYBRID: 0.6,
        }

    def analyze_query(
        self,
        filters: List[Dict[str, Any]],
        limit: int = 200,
        hints: Optional[OptimizationHint] = None,
    ) -> QueryStrategy:
        """
        Analyze query characteristics and recommend optimal strategy.

        Args:
            filters: List of filter conditions
            limit: Maximum results requested
            hints: Optional optimization hints

        Returns:
            Recommended query strategy
        """
        # Check for cache preference
        if hints and hints.preferred_strategy:
            logger.debug(f"Using hint strategy: {hints.preferred_strategy}")
            return hints.preferred_strategy

        # Analyze filter complexity
        if not filters:
            return QueryStrategy.BULK_RETRIEVE

        # Check for tag-based filters
        tag_filters = [
            f for f in filters if f.get("field") in ["tags", "tag_id", "tag_ids"]
        ]
        if tag_filters and len(tag_filters) > 1:
            return QueryStrategy.TAG_OPTIMIZED

        # Check for complex logical groups
        logical_groups = [f for f in filters if "operator" in f and "conditions" in f]
        if logical_groups:
            return QueryStrategy.HYBRID

        # Check for server-optimizable filters
        server_optimizable = self._count_server_optimizable_filters(filters)
        if server_optimizable >= len(filters) * 0.7:  # 70% server-optimizable
            return QueryStrategy.SERVER_OPTIMIZED

        # Default to hybrid approach
        return QueryStrategy.HYBRID

    def _count_server_optimizable_filters(self, filters: List[Dict[str, Any]]) -> int:
        """Count filters that can be optimized server-side."""
        server_fields = {"email", "given_name", "family_name", "id", "date_created"}
        server_operators = {"EQUALS", "CONTAINS", "equals", "contains"}

        count = 0
        for filter_condition in filters:
            if (
                filter_condition.get("field") in server_fields
                and filter_condition.get("operator") in server_operators
            ):
                count += 1

        return count

    def track_performance(self, query_key: str, metrics: QueryMetrics):
        """Track query performance for learning."""
        if query_key not in self.performance_history:
            self.performance_history[query_key] = []

        self.performance_history[query_key].append(metrics)

        # Keep only recent history (last 20 queries)
        if len(self.performance_history[query_key]) > 20:
            self.performance_history[query_key] = self.performance_history[query_key][
                -20:
            ]

        # Update strategy scores based on performance
        self._update_strategy_scores(metrics)

    def _update_strategy_scores(self, metrics: QueryMetrics):
        """Update strategy effectiveness scores."""
        strategy = QueryStrategy(metrics.strategy_used)

        # Calculate performance score (lower duration is better)
        performance_score = max(0.1, 1.0 - (metrics.total_duration_ms / 10000.0))

        # Apply learning rate
        learning_rate = 0.1
        current_score = self.strategy_scores.get(strategy, 0.5)
        new_score = current_score + learning_rate * (performance_score - current_score)

        self.strategy_scores[strategy] = max(0.1, min(1.0, new_score))

        logger.debug(f"Updated {strategy} score to {new_score:.3f}")

    def get_performance_summary(
        self, query_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance summary for queries."""
        if query_key and query_key in self.performance_history:
            history = self.performance_history[query_key]
        else:
            # Aggregate all query histories
            history = []
            for queries in self.performance_history.values():
                history.extend(queries)

        if not history:
            return {"message": "No performance data available"}

        # Calculate averages
        avg_duration = sum(m.total_duration_ms for m in history) / len(history)
        avg_api_calls = sum(m.api_calls for m in history) / len(history)
        cache_hit_ratio = sum(1 for m in history if m.cache_hit) / len(history)

        # Strategy usage
        strategy_usage = {}
        for metrics in history:
            strategy = metrics.strategy_used
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1

        return {
            "total_queries": len(history),
            "avg_duration_ms": avg_duration,
            "avg_api_calls": avg_api_calls,
            "cache_hit_ratio": cache_hit_ratio,
            "strategy_usage": strategy_usage,
            "strategy_scores": dict(self.strategy_scores),
        }


class QueryExecutor:
    """Execute optimized queries based on selected strategy."""

    def __init__(self, api_client, cache_manager):
        self.api_client = api_client
        self.cache_manager = cache_manager
        self.optimizer = QueryOptimizer()
        from .api_optimization import ApiParameterOptimizer

        self.api_optimizer = ApiParameterOptimizer()

    async def execute_optimized_query(
        self,
        query_type: str,
        filters: List[Dict[str, Any]],
        limit: int = 200,
        offset: int = 0,
        **kwargs,
    ) -> Tuple[List[Dict[str, Any]], QueryMetrics]:
        """
        Execute an optimized query with performance tracking.

        Args:
            query_type: Type of query (e.g., 'list_contacts')
            filters: Filter conditions
            limit: Result limit
            offset: Result offset
            **kwargs: Additional parameters

        Returns:
            Tuple of (results, metrics)
        """
        start_time = time.time()

        # Generate cache key
        cache_key = self._generate_cache_key(query_type, filters, limit, offset)

        # Check cache first
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result:
            duration_ms = (time.time() - start_time) * 1000
            metrics = QueryMetrics(
                total_duration_ms=duration_ms,
                api_calls=0,
                cache_hit=True,
                strategy_used=QueryStrategy.CACHED_RESULT,
                filters_applied=len(filters),
                results_count=len(cached_result),
                server_side_filters=0,
                client_side_filters=0,
                optimization_ratio=1.0,
            )

            self.optimizer.track_performance(cache_key, metrics)
            return cached_result, metrics

        # Select optimization strategy
        strategy = self.optimizer.analyze_query(filters, limit)
        logger.debug(
            f"Selected strategy: {strategy} for query with {len(filters)} filters"
        )

        # Execute based on strategy
        if strategy == QueryStrategy.SERVER_OPTIMIZED:
            (
                results,
                api_calls,
                server_filters,
                client_filters,
            ) = await self._execute_server_optimized(
                query_type, filters, limit, offset, **kwargs
            )
        elif strategy == QueryStrategy.TAG_OPTIMIZED:
            (
                results,
                api_calls,
                server_filters,
                client_filters,
            ) = await self._execute_tag_optimized(
                query_type, filters, limit, offset, **kwargs
            )
        elif strategy == QueryStrategy.HYBRID:
            (
                results,
                api_calls,
                server_filters,
                client_filters,
            ) = await self._execute_hybrid(query_type, filters, limit, offset, **kwargs)
        else:
            # Default to bulk retrieve
            (
                results,
                api_calls,
                server_filters,
                client_filters,
            ) = await self._execute_bulk_retrieve(
                query_type, filters, limit, offset, **kwargs
            )

        # Calculate metrics
        duration_ms = (time.time() - start_time) * 1000
        optimization_ratio = server_filters / max(1, server_filters + client_filters)

        metrics = QueryMetrics(
            total_duration_ms=duration_ms,
            api_calls=api_calls,
            cache_hit=False,
            strategy_used=strategy,
            filters_applied=len(filters),
            results_count=len(results),
            server_side_filters=server_filters,
            client_side_filters=client_filters,
            optimization_ratio=optimization_ratio,
        )

        # Cache results
        await self.cache_manager.set(cache_key, results, ttl=1800)

        # Track performance
        self.optimizer.track_performance(cache_key, metrics)

        return results, metrics

    async def _execute_server_optimized(
        self,
        query_type: str,
        filters: List[Dict[str, Any]],
        limit: int,
        offset: int,
        **kwargs,
    ) -> Tuple[List[Dict[str, Any]], int, int, int]:
        """Execute with maximum server-side optimization."""
        from src.utils.filter_utils import (
            optimize_filters_for_api,
            apply_complex_filters,
        )

        # Optimize filters
        server_params, client_filters = optimize_filters_for_api(filters)

        # Execute API call
        if query_type == "list_contacts":
            params = {"limit": limit, "offset": offset, **server_params}
            response = await self.api_client.get_contacts(**params)
            results = response.get("contacts", [])
        else:
            # Handle other query types
            results = []

        # Apply remaining client-side filters
        if client_filters:
            results = apply_complex_filters(results, client_filters)

        api_calls = 1
        server_filters = len(filters) - len(client_filters)
        client_filters_count = len(client_filters)

        return results, api_calls, server_filters, client_filters_count

    async def _execute_tag_optimized(
        self,
        query_type: str,
        filters: List[Dict[str, Any]],
        limit: int,
        offset: int,
        **kwargs,
    ) -> Tuple[List[Dict[str, Any]], int, int, int]:
        """Execute with tag-specific optimizations."""
        # This would implement tag-parallel querying and result merging
        # For now, fallback to server optimized
        return await self._execute_server_optimized(
            query_type, filters, limit, offset, **kwargs
        )

    async def _execute_hybrid(
        self,
        query_type: str,
        filters: List[Dict[str, Any]],
        limit: int,
        offset: int,
        **kwargs,
    ) -> Tuple[List[Dict[str, Any]], int, int, int]:
        """Execute with hybrid server/client optimization."""
        # Use API optimizer for hybrid strategy
        optimization_result = self.api_optimizer.optimize_contact_query_parameters(
            filters, limit
        )

        # Execute with server-side filters
        server_filters = optimization_result.server_side_filters or []
        client_filters = optimization_result.client_side_filters or []

        if query_type == "list_contacts":
            # Build server parameters from server-side filters
            from src.utils.filter_utils import optimize_filters_for_api

            server_params, remaining_client_filters = optimize_filters_for_api(
                server_filters
            )

            # Execute API call
            params = {"limit": limit, "offset": offset, **server_params}
            response = await self.api_client.get_contacts(**params)
            results = response.get("contacts", [])

            # Apply client-side filters
            all_client_filters = client_filters + remaining_client_filters
            if all_client_filters:
                results = await self._apply_client_side_filters(
                    results, all_client_filters
                )
        else:
            results = []

        api_calls = 1
        server_filters_count = len(server_filters)
        client_filters_count = len(client_filters)

        return results, api_calls, server_filters_count, client_filters_count

    async def _execute_bulk_retrieve(
        self,
        query_type: str,
        filters: List[Dict[str, Any]],
        limit: int,
        offset: int,
        **kwargs,
    ) -> Tuple[List[Dict[str, Any]], int, int, int]:
        """Execute with bulk retrieval and client-side filtering."""
        from src.utils.filter_utils import apply_complex_filters

        # Get all data and filter client-side
        if query_type == "list_contacts":
            params = {"limit": limit, "offset": offset}
            response = await self.api_client.get_contacts(**params)
            results = response.get("contacts", [])
        else:
            results = []

        # Apply all filters client-side
        if filters:
            results = apply_complex_filters(results, filters)

        api_calls = 1
        server_filters = 0
        client_filters_count = len(filters)

        return results, api_calls, server_filters, client_filters_count

    def _generate_cache_key(
        self,
        query_type: str,
        filters: List[Dict[str, Any]],
        limit: int,
        offset: int,
        order_by: str = None,
        order_direction: str = "ASC",
    ) -> str:
        """Generate a cache key for the query."""
        import hashlib
        import json

        # Create a consistent string representation
        key_data = {
            "query_type": query_type,
            "filters": filters,
            "limit": limit,
            "offset": offset,
            "order_by": order_by,
            "order_direction": order_direction,
        }

        # Sort keys for consistency
        key_string = json.dumps(key_data, sort_keys=True)

        # Generate hash
        key_hash = hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()  # nosec B324 - Cache key generation

        return f"query:{key_hash}"

    async def _apply_client_side_filters(
        self, contacts: List[Dict[str, Any]], filters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply client-side filters to contacts."""
        if not filters:
            return contacts

        filtered_contacts = []

        for contact in contacts:
            matches = True

            for filter_condition in filters:
                field = filter_condition.get("field")
                operator = filter_condition.get("operator")
                value = filter_condition.get("value")
                field_id = filter_condition.get("field_id")

                if field == "custom_field":
                    # Import here to avoid circular imports
                    from src.utils.contact_utils import get_custom_field_value

                    if field_id:
                        contact_value = get_custom_field_value(contact, field_id)
                    else:
                        # Fallback to searching all custom fields for the value
                        contact_value = None
                        custom_fields = contact.get("custom_fields", [])
                        for cf in custom_fields:
                            if cf.get("content") == value:
                                contact_value = value
                                break
                else:
                    contact_value = contact.get(field)

                # Simple matching logic
                if operator in ["equals", "EQUALS", "="]:
                    if contact_value != value:
                        matches = False
                        break
                elif operator in ["contains", "CONTAINS"]:
                    if not contact_value or value not in str(contact_value):
                        matches = False
                        break
                # Add more operators as needed

            if matches:
                filtered_contacts.append(contact)

        return filtered_contacts
