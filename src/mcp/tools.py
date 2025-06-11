"""
Simplified MCP Tools for Keap CRM integration.

This module provides the main MCP tool interface, combining contact and tag tools
for streamlined Keap CRM operations.
"""

import logging
import time
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import Context

from src.api.client import KeapApiService
from src.cache.manager import CacheManager

logger = logging.getLogger(__name__)


# Initialize shared components
def get_api_client() -> KeapApiService:
    """Get or create API client instance."""
    import os

    # For testing, provide a default API key if none exists
    if not os.getenv("KEAP_API_KEY"):
        os.environ["KEAP_API_KEY"] = "test_api_key_for_testing"
    return KeapApiService()


def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance."""
    return CacheManager()


# Main tool functions for MCP server
async def list_contacts(
    context: Context,
    filters: Optional[List[Dict[str, Any]]] = None,
    limit: int = 200,
    offset: int = 0,
    order_by: Optional[str] = None,
    order_direction: str = "ASC",
    include: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """List contacts with optional filtering and pagination.

    This function now uses the optimized query engine for better performance.
    For advanced features like performance metrics, use query_contacts_optimized directly.
    """
    # Use the optimized query function internally but maintain the simple interface
    result = await query_contacts_optimized(
        context=context,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        include=include,
        enable_optimization=True,
        return_metrics=False,
    )

    # Return just the contacts list for backward compatibility
    return result["contacts"]


async def get_tags(
    context: Context,
    filters: Optional[List[Dict[str, Any]]] = None,
    include_categories: bool = True,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Get tags with optional filtering."""
    from src.mcp.tag_tools import get_tags as _get_tags

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _get_tags(
        context=ctx, filters=filters, include_categories=include_categories, limit=limit
    )


async def search_contacts_by_email(
    context: Context, email: str, include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search contacts by email address."""
    from src.mcp.contact_tools import search_contacts_by_email as _search_by_email

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _search_by_email(context=ctx, email=email, include=include)


async def search_contacts_by_name(
    context: Context, name: str, include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search contacts by name."""
    from src.mcp.contact_tools import search_contacts_by_name as _search_by_name

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _search_by_name(context=ctx, name=name, include=include)


async def get_contacts_with_tag(
    context: Context, tag_id: str, limit: int = 200, include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Get contacts that have a specific tag."""
    from src.mcp.tag_tools import get_contacts_with_tag as _get_contacts_with_tag

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _get_contacts_with_tag(
        context=ctx, tag_id=tag_id, limit=limit, include=include
    )


async def get_contact_details(
    context: Context, contact_id: str, include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get detailed information about a specific contact."""
    from src.mcp.contact_tools import get_contact_details as _get_contact_details

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _get_contact_details(
        context=ctx, contact_id=contact_id, include=include
    )


async def get_tag_details(context: Context, tag_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific tag."""
    from src.mcp.tag_tools import get_tag_details as _get_tag_details

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _get_tag_details(context=ctx, tag_id=tag_id)


async def apply_tags_to_contacts(
    context: Context, tag_ids: List[str], contact_ids: List[str]
) -> Dict[str, Any]:
    """Apply multiple tags to multiple contacts using batch operations."""
    from src.mcp.tag_tools import apply_tags_to_contacts as _apply_tags_to_contacts

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _apply_tags_to_contacts(
        context=ctx, tag_ids=tag_ids, contact_ids=contact_ids
    )


async def remove_tags_from_contacts(
    context: Context, tag_ids: List[str], contact_ids: List[str]
) -> Dict[str, Any]:
    """Remove multiple tags from multiple contacts."""
    from src.mcp.tag_tools import (
        remove_tags_from_contacts as _remove_tags_from_contacts,
    )

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _remove_tags_from_contacts(
        context=ctx, tag_ids=tag_ids, contact_ids=contact_ids
    )


async def create_tag(
    context: Context,
    name: str,
    description: Optional[str] = None,
    category_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new tag."""
    from src.mcp.tag_tools import create_tag as _create_tag

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    return await _create_tag(
        context=ctx, name=name, description=description, category_id=category_id
    )


async def intersect_id_lists(
    context: Context, lists: List[Dict[str, Any]], id_field: str = "item_ids"
) -> Dict[str, Any]:
    """Find the intersection of multiple ID lists."""
    try:
        if not lists or len(lists) < 2:
            return {
                "success": False,
                "error": "At least two lists are required for intersection",
            }

        # Extract ID sets from each list
        id_sets = []
        for list_item in lists:
            ids = list_item.get(id_field, [])
            if not isinstance(ids, list):
                return {"success": False, "error": f"Field '{id_field}' must be a list"}
            id_sets.append(set(ids))

        # Find intersection
        intersection = id_sets[0]
        for id_set in id_sets[1:]:
            intersection = intersection.intersection(id_set)

        result_ids = list(intersection)

        logger.info(
            f"Intersected {len(lists)} lists, found {len(result_ids)} common IDs"
        )
        return {
            "success": True,
            "intersection": result_ids,
            "count": len(result_ids),
            "lists_processed": len(lists),
        }

    except Exception as e:
        logger.error(f"Error intersecting ID lists: {e}")
        return {"success": False, "error": str(e)}


async def query_contacts_by_custom_field(
    context: Context,
    field_id: str,
    field_value: str,
    operator: str = "equals",
    limit: int = 200,
    include: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Query contacts by custom field value."""
    try:
        from src.utils.contact_utils import get_custom_field_value

        # Create a context-like object with required dependencies
        class ContextWithDeps:
            def __init__(self):
                self.api_client = get_api_client()
                self.cache_manager = get_cache_manager()

        ctx = ContextWithDeps()

        api_client = ctx.api_client
        cache_manager = ctx.cache_manager

        cache_key = f"custom_field_query:{field_id}:{field_value}:{operator}:{limit}"

        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        # Get all contacts (this could be optimized with server-side filtering if supported)
        response = await api_client.get_contacts(limit=limit)
        all_contacts = response.get("contacts", [])

        # Filter by custom field
        matching_contacts = []
        for contact in all_contacts:
            custom_field_value = get_custom_field_value(contact, field_id)

            if custom_field_value is not None:
                if operator == "equals" and str(custom_field_value) == str(field_value):
                    matching_contacts.append(contact)
                elif (
                    operator == "contains"
                    and str(field_value).lower() in str(custom_field_value).lower()
                ):
                    matching_contacts.append(contact)
                elif operator == "starts_with" and str(
                    custom_field_value
                ).lower().startswith(str(field_value).lower()):
                    matching_contacts.append(contact)

        # Process include fields
        if include:
            from src.utils.contact_utils import process_contact_include_fields

            matching_contacts = [
                process_contact_include_fields(contact, include)
                for contact in matching_contacts
            ]

        # Format contacts
        from src.utils.contact_utils import format_contact_data

        formatted_contacts = [
            format_contact_data(contact) for contact in matching_contacts
        ]

        # Cache result
        await cache_manager.set(cache_key, formatted_contacts, ttl=1800)

        logger.info(
            f"Found {len(formatted_contacts)} contacts with custom field {field_id}={field_value}"
        )
        return formatted_contacts

    except Exception as e:
        logger.error(f"Error querying contacts by custom field: {e}")
        raise


async def query_contacts_optimized(
    context: Context,
    filters: Optional[List[Dict[str, Any]]] = None,
    limit: int = 200,
    offset: int = 0,
    order_by: Optional[str] = None,
    order_direction: str = "ASC",
    include: Optional[List[str]] = None,
    enable_optimization: bool = True,
    return_metrics: bool = False,
) -> Dict[str, Any]:
    """Advanced contact query with optimization and performance analytics."""
    try:
        # Create a context-like object with required dependencies
        class ContextWithDeps:
            def __init__(self):
                self.api_client = get_api_client()
                self.cache_manager = get_cache_manager()

        ctx = ContextWithDeps()

        if enable_optimization:
            # Use optimization framework
            from src.mcp.optimization.optimization import QueryExecutor

            executor = QueryExecutor(ctx.api_client, ctx.cache_manager)

            # Execute optimized query
            contacts, metrics = await executor.execute_optimized_query(
                query_type="list_contacts",
                filters=filters or [],
                limit=limit,
                offset=offset,
                order_by=order_by,
                order_direction=order_direction,
                include=include,
            )

            result = {"contacts": contacts, "count": len(contacts)}

            if return_metrics:
                result["performance_metrics"] = {
                    "total_duration_ms": metrics.total_duration_ms,
                    "api_calls": metrics.api_calls,
                    "cache_hit": metrics.cache_hit,
                    "strategy_used": metrics.strategy_used,
                    "filters_applied": metrics.filters_applied,
                    "server_side_filters": metrics.server_side_filters,
                    "client_side_filters": metrics.client_side_filters,
                    "optimization_ratio": metrics.optimization_ratio,
                }

            logger.info(
                f"Optimized query returned {len(contacts)} contacts using {metrics.strategy_used} strategy"
            )
            return result

        else:
            # Use standard query
            from src.mcp.contact_tools import list_contacts as _list_contacts

            contacts = await _list_contacts(
                context=ctx,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                order_direction=order_direction,
                include=include,
            )

            return {"contacts": contacts, "count": len(contacts)}

    except Exception as e:
        logger.error(f"Error in optimized contact query: {e}")
        raise


async def analyze_query_performance(
    context: Context, filters: List[Dict[str, Any]], query_type: str = "contact"
) -> Dict[str, Any]:
    """Analyze query performance and optimization potential."""
    try:
        from src.mcp.optimization.api_optimization import ApiParameterOptimizer
        from src.mcp.optimization.optimization import QueryOptimizer

        # Set up optimizers
        api_optimizer = ApiParameterOptimizer()
        query_optimizer = QueryOptimizer()

        # Analyze API optimization potential
        if query_type == "contact":
            optimization_result = api_optimizer.optimize_contact_query_parameters(
                filters
            )
        else:
            optimization_result = api_optimizer.optimize_tag_query_parameters(filters)

        # Get performance analysis
        performance_analysis = api_optimizer.analyze_filter_performance(
            filters, query_type
        )

        # Get recommended strategy
        recommended_strategy = query_optimizer.analyze_query(filters)

        # Get field optimization info
        field_info = api_optimizer.get_field_optimization_info(query_type)

        result = {
            "query_analysis": {
                "total_filters": len(filters),
                "recommended_strategy": recommended_strategy,
                "optimization_strategy": optimization_result.optimization_strategy,
                "optimization_score": optimization_result.optimization_score,
                "estimated_data_reduction": optimization_result.estimated_data_reduction_ratio,
                "performance_rating": performance_analysis["performance_rating"],
            },
            "filter_breakdown": {
                "server_side_filters": optimization_result.server_side_filters,
                "client_side_filters": optimization_result.client_side_filters,
                "server_optimizable_count": len(
                    optimization_result.server_side_filters
                ),
                "client_only_count": len(optimization_result.client_side_filters),
            },
            "optimization_suggestions": _generate_optimization_suggestions(
                optimization_result, filters
            ),
            "field_capabilities": field_info,
        }

        logger.info(
            f"Analyzed query with {len(filters)} filters - {performance_analysis['performance_rating']} performance rating"
        )
        return result

    except Exception as e:
        logger.error(f"Error analyzing query performance: {e}")
        raise


def _generate_optimization_suggestions(
    optimization_result, filters: List[Dict[str, Any]]
) -> List[str]:
    """Generate optimization suggestions based on analysis."""
    suggestions = []

    if optimization_result.optimization_score < 0.5:
        suggestions.append(
            "Consider restructuring filters to use server-optimizable fields like 'email', 'given_name', 'family_name'"
        )

    if len(optimization_result.client_side_filters) > len(
        optimization_result.server_side_filters
    ):
        suggestions.append(
            "Many filters require client-side processing - consider caching results for repeated queries"
        )

    # Check for logical groups
    logical_groups = [f for f in filters if "operator" in f and "conditions" in f]
    if logical_groups:
        suggestions.append(
            "Complex logical conditions detected - ensure you're using the optimized query endpoint for best performance"
        )

    # Check for unsupported operators
    unsupported_fields = []
    for filter_condition in optimization_result.client_side_filters:
        if "field" in filter_condition:
            field = filter_condition["field"]
            if field not in [
                "tags",
                "custom_fields",
            ]:  # These are expected to be client-side
                unsupported_fields.append(field)

    if unsupported_fields:
        suggestions.append(
            f"Fields {unsupported_fields} cannot be optimized server-side with current operators"
        )

    if optimization_result.optimization_score >= 0.8:
        suggestions.append(
            "Excellent optimization! This query should perform very well"
        )

    return suggestions


async def modify_tags(
    context: Context, contact_ids: List[str], tag_ids: List[str], action: str = "add"
) -> Dict[str, Any]:
    """Add or remove tags from contacts."""

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    try:
        if action == "add":
            for tag_id in tag_ids:
                result = await ctx.api_client.apply_tag_to_contacts(tag_id, contact_ids)
                if not result.get("success", False):
                    return {"success": False, "error": f"Failed to apply tag {tag_id}"}
        elif action == "remove":
            for tag_id in tag_ids:
                result = await ctx.api_client.remove_tag_from_contacts(
                    tag_id, contact_ids
                )
                if not result.get("success", False):
                    return {"success": False, "error": f"Failed to remove tag {tag_id}"}
        else:
            return {"success": False, "error": f"Invalid action: {action}"}

        if action == "add":
            message = "Successfully added tags"
        elif action == "remove":
            message = "Successfully removed tags"
        else:
            message = f"Successfully {action}ed tags"

        return {"success": True, "message": message}

    except Exception as e:
        logger.error(f"Error modifying tags: {e}")
        return {"success": False, "error": str(e)}


async def get_api_diagnostics(context: Context) -> Dict[str, Any]:
    """Get comprehensive API diagnostics and performance metrics."""
    try:
        # Create a context-like object with required dependencies
        class ContextWithDeps:
            def __init__(self):
                self.api_client = get_api_client()
                self.cache_manager = get_cache_manager()

        ctx = ContextWithDeps()

        api_client = ctx.api_client
        cache_manager = ctx.cache_manager

        # Get API client diagnostics
        api_diagnostics = api_client.get_diagnostics()

        # Get cache diagnostics if available
        cache_diagnostics = {}
        if hasattr(cache_manager, "get_diagnostics"):
            cache_diagnostics = cache_manager.get_diagnostics()

        # Get system information
        try:
            import psutil
            import platform

            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_available_gb": round(
                    psutil.virtual_memory().available / (1024**3), 2
                ),
                "memory_percent": psutil.virtual_memory().percent,
            }
        except ImportError:
            system_info = {"message": "psutil not available for system metrics"}

        # Calculate performance metrics
        performance_metrics = {
            "success_rate": (
                api_diagnostics["successful_requests"]
                / max(api_diagnostics["total_requests"], 1)
                * 100
            ),
            "retry_rate": (
                api_diagnostics["retried_requests"]
                / max(api_diagnostics["total_requests"], 1)
                * 100
            ),
            "rate_limit_hit_rate": (
                api_diagnostics["rate_limited_requests"]
                / max(api_diagnostics["total_requests"], 1)
                * 100
            ),
            "cache_hit_rate": (
                api_diagnostics["cache_hits"]
                / max(
                    api_diagnostics["cache_hits"] + api_diagnostics["cache_misses"], 1
                )
                * 100
            ),
        }

        # Most used endpoints
        top_endpoints = dict(
            sorted(
                api_diagnostics["endpoints_called"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
        )

        # Most common errors
        top_errors = dict(
            sorted(
                api_diagnostics["error_counts"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
        )

        result = {
            "timestamp": api_diagnostics.get("last_request_time"),
            "api_diagnostics": api_diagnostics,
            "cache_diagnostics": cache_diagnostics,
            "system_info": system_info,
            "performance_metrics": performance_metrics,
            "top_endpoints": top_endpoints,
            "top_errors": top_errors,
            "recommendations": _generate_performance_recommendations(
                api_diagnostics, performance_metrics
            ),
        }

        logger.info("Generated comprehensive API diagnostics report")
        return result

    except Exception as e:
        logger.error(f"Error generating API diagnostics: {e}")
        return {"error": str(e), "timestamp": time.time()}


def _generate_performance_recommendations(
    api_diagnostics: Dict, performance_metrics: Dict
) -> List[str]:
    """Generate performance recommendations based on diagnostics."""
    recommendations = []

    if performance_metrics["success_rate"] < 95:
        recommendations.append(
            "Success rate is below 95% - check error patterns and consider API key/permissions"
        )

    if performance_metrics["retry_rate"] > 10:
        recommendations.append(
            "High retry rate detected - API may be unstable or rate limits too aggressive"
        )

    if performance_metrics["rate_limit_hit_rate"] > 5:
        recommendations.append(
            "Frequent rate limiting - consider reducing request frequency or implementing better backoff"
        )

    if performance_metrics["cache_hit_rate"] < 70:
        recommendations.append(
            "Low cache hit rate - consider increasing cache TTL or reviewing query patterns"
        )

    if api_diagnostics["average_response_time"] > 2.0:
        recommendations.append(
            "High average response time - check network conditions and API performance"
        )

    if api_diagnostics["requests_per_hour"] > 5000:
        recommendations.append(
            "High request rate - monitor daily limits and consider optimization"
        )

    if not recommendations:
        recommendations.append(
            "Performance looks good! All metrics are within acceptable ranges."
        )

    return recommendations


async def set_custom_field_values(
    context: Context,
    field_id: str,
    contact_values: Optional[Dict[str, Any]] = None,
    contact_ids: Optional[List[str]] = None,
    common_value: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Set custom field values across multiple contacts.

    Args:
        context: MCP context
        field_id: Custom field ID to modify
        contact_values: Dictionary mapping contact IDs to field values
        contact_ids: List of contact IDs (when using common_value)
        common_value: Value to set for all contacts in contact_ids

    Returns:
        Result with success/error information
    """

    # Create a context-like object with required dependencies
    class ContextWithDeps:
        def __init__(self):
            self.api_client = get_api_client()
            self.cache_manager = get_cache_manager()

    ctx = ContextWithDeps()

    try:
        api_client = ctx.api_client
        cache_manager = ctx.cache_manager

        # Validate input parameters
        if contact_values and (contact_ids or common_value is not None):
            return {
                "success": False,
                "error": "Cannot specify both contact_values and contact_ids/common_value",
            }

        if not contact_values and not (contact_ids and common_value is not None):
            return {
                "success": False,
                "error": "Must specify either contact_values or contact_ids with common_value",
            }

        # Prepare update operations
        updates = []
        if contact_values:
            # Dictionary mode: different values per contact
            for contact_id, value in contact_values.items():
                updates.append(
                    {
                        "contact_id": str(contact_id),
                        "field_id": str(field_id),
                        "value": value,
                    }
                )
        else:
            # Common value mode: same value for all contacts
            for contact_id in contact_ids:
                updates.append(
                    {
                        "contact_id": str(contact_id),
                        "field_id": str(field_id),
                        "value": common_value,
                    }
                )

        # Execute updates with error tracking
        successful_updates = []
        failed_updates = []

        for update in updates:
            try:
                # Update custom field for contact
                result = await api_client.update_contact_custom_field(
                    contact_id=update["contact_id"],
                    field_id=update["field_id"],
                    value=update["value"],
                )

                if result.get("success", False):
                    successful_updates.append(
                        {
                            "contact_id": update["contact_id"],
                            "field_id": update["field_id"],
                            "value": update["value"],
                        }
                    )

                    # Invalidate cache for this contact
                    cache_key_patterns = [
                        f"contact:{update['contact_id']}:*",
                        f"contacts:*custom_field*{update['field_id']}*",
                    ]
                    for pattern in cache_key_patterns:
                        await cache_manager.invalidate_pattern(pattern)

                else:
                    failed_updates.append(
                        {
                            "contact_id": update["contact_id"],
                            "error": result.get("error", "Unknown error"),
                        }
                    )

            except Exception as e:
                failed_updates.append(
                    {"contact_id": update["contact_id"], "error": str(e)}
                )

        # Prepare response
        total_requested = len(updates)
        total_successful = len(successful_updates)
        total_failed = len(failed_updates)

        response = {
            "success": total_failed == 0,
            "total_requested": total_requested,
            "successful_updates": total_successful,
            "failed_updates": total_failed,
            "field_id": field_id,
        }

        if successful_updates:
            response["successful_contacts"] = [
                u["contact_id"] for u in successful_updates
            ]

        if failed_updates:
            response["failed_contacts"] = failed_updates
            response["error_summary"] = (
                f"{total_failed} out of {total_requested} updates failed"
            )

        if total_failed == 0:
            response["message"] = (
                f"Successfully updated custom field {field_id} for {total_successful} contacts"
            )
        elif total_successful > 0:
            response["message"] = (
                f"Partially successful: {total_successful} updated, {total_failed} failed"
            )
        else:
            response["message"] = f"All {total_failed} updates failed"

        logger.info(
            f"Custom field update: {total_successful}/{total_requested} successful for field {field_id}"
        )
        return response

    except Exception as e:
        logger.error(f"Error setting custom field values: {e}")
        return {"success": False, "error": str(e)}


# MCP tool registry
MCP_TOOLS = [
    {
        "name": "list_contacts",
        "description": "List contacts from Keap CRM with optional filtering and pagination",
        "function": list_contacts,
        "parameters": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "array",
                    "description": "Filter conditions to apply",
                    "items": {"type": "object"},
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of contacts to return",
                    "default": 200,
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of contacts to skip",
                    "default": 0,
                },
                "order_by": {"type": "string", "description": "Field to order by"},
                "order_direction": {
                    "type": "string",
                    "enum": ["ASC", "DESC"],
                    "default": "ASC",
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"},
                },
            },
        },
    },
    {
        "name": "get_tags",
        "description": "Get tags from Keap CRM with optional filtering",
        "function": get_tags,
        "parameters": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "array",
                    "description": "Filter conditions for tags",
                    "items": {"type": "object"},
                },
                "include_categories": {
                    "type": "boolean",
                    "description": "Include category information",
                    "default": True,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of tags to return",
                    "default": 1000,
                },
            },
        },
    },
    {
        "name": "search_contacts_by_email",
        "description": "Search contacts by email address",
        "function": search_contacts_by_email,
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Email address to search for",
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"},
                },
            },
            "required": ["email"],
        },
    },
    {
        "name": "search_contacts_by_name",
        "description": "Search contacts by name (first or last)",
        "function": search_contacts_by_name,
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name to search for"},
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"},
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_contacts_with_tag",
        "description": "Get contacts that have a specific tag",
        "function": get_contacts_with_tag,
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {"type": "string", "description": "Tag ID to search for"},
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of contacts to return",
                    "default": 200,
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"},
                },
            },
            "required": ["tag_id"],
        },
    },
    {
        "name": "modify_tags",
        "description": "Add or remove tags from contacts",
        "function": modify_tags,
        "parameters": {
            "type": "object",
            "properties": {
                "contact_ids": {
                    "type": "array",
                    "description": "List of contact IDs to modify",
                    "items": {"type": "string"},
                },
                "tag_ids": {
                    "type": "array",
                    "description": "List of tag IDs to add or remove",
                    "items": {"type": "string"},
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'add' or 'remove'",
                    "enum": ["add", "remove"],
                    "default": "add",
                },
            },
            "required": ["contact_ids", "tag_ids"],
        },
    },
    {
        "name": "get_contact_details",
        "description": "Get detailed information about a specific contact",
        "function": get_contact_details,
        "parameters": {
            "type": "object",
            "properties": {
                "contact_id": {
                    "type": "string",
                    "description": "Contact ID to retrieve",
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"},
                },
            },
            "required": ["contact_id"],
        },
    },
    {
        "name": "get_tag_details",
        "description": "Get detailed information about a specific tag",
        "function": get_tag_details,
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {"type": "string", "description": "Tag ID to retrieve"}
            },
            "required": ["tag_id"],
        },
    },
    {
        "name": "apply_tags_to_contacts",
        "description": "Apply multiple tags to multiple contacts using batch operations",
        "function": apply_tags_to_contacts,
        "parameters": {
            "type": "object",
            "properties": {
                "tag_ids": {
                    "type": "array",
                    "description": "List of tag IDs to apply",
                    "items": {"type": "string"},
                },
                "contact_ids": {
                    "type": "array",
                    "description": "List of contact IDs to modify",
                    "items": {"type": "string"},
                },
            },
            "required": ["tag_ids", "contact_ids"],
        },
    },
    {
        "name": "remove_tags_from_contacts",
        "description": "Remove multiple tags from multiple contacts",
        "function": remove_tags_from_contacts,
        "parameters": {
            "type": "object",
            "properties": {
                "tag_ids": {
                    "type": "array",
                    "description": "List of tag IDs to remove",
                    "items": {"type": "string"},
                },
                "contact_ids": {
                    "type": "array",
                    "description": "List of contact IDs to modify",
                    "items": {"type": "string"},
                },
            },
            "required": ["tag_ids", "contact_ids"],
        },
    },
    {
        "name": "create_tag",
        "description": "Create a new tag",
        "function": create_tag,
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the new tag"},
                "description": {
                    "type": "string",
                    "description": "Optional description for the tag",
                },
                "category_id": {
                    "type": "string",
                    "description": "Optional category ID for the tag",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "intersect_id_lists",
        "description": "Find the intersection of multiple ID lists",
        "function": intersect_id_lists,
        "parameters": {
            "type": "object",
            "properties": {
                "lists": {
                    "type": "array",
                    "description": "List of objects containing ID arrays",
                    "items": {"type": "object"},
                },
                "id_field": {
                    "type": "string",
                    "description": "Field name containing the IDs",
                    "default": "item_ids",
                },
            },
            "required": ["lists"],
        },
    },
    {
        "name": "query_contacts_by_custom_field",
        "description": "Query contacts by custom field value",
        "function": query_contacts_by_custom_field,
        "parameters": {
            "type": "object",
            "properties": {
                "field_id": {
                    "type": "string",
                    "description": "Custom field ID to search",
                },
                "field_value": {"type": "string", "description": "Value to search for"},
                "operator": {
                    "type": "string",
                    "description": "Comparison operator",
                    "enum": ["equals", "contains", "starts_with"],
                    "default": "equals",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of contacts to return",
                    "default": 200,
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"},
                },
            },
            "required": ["field_id", "field_value"],
        },
    },
    {
        "name": "query_contacts_optimized",
        "description": "Advanced contact query with optimization and performance analytics",
        "function": query_contacts_optimized,
        "parameters": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "array",
                    "description": "Advanced filter conditions with logical operators",
                    "items": {"type": "object"},
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of contacts to return",
                    "default": 200,
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of contacts to skip",
                    "default": 0,
                },
                "order_by": {"type": "string", "description": "Field to order by"},
                "order_direction": {
                    "type": "string",
                    "enum": ["ASC", "DESC"],
                    "default": "ASC",
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"},
                },
                "enable_optimization": {
                    "type": "boolean",
                    "description": "Enable query optimization",
                    "default": True,
                },
                "return_metrics": {
                    "type": "boolean",
                    "description": "Include performance metrics in response",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "analyze_query_performance",
        "description": "Analyze query performance and optimization potential",
        "function": analyze_query_performance,
        "parameters": {
            "type": "object",
            "properties": {
                "filters": {
                    "type": "array",
                    "description": "Filter conditions to analyze",
                    "items": {"type": "object"},
                },
                "query_type": {
                    "type": "string",
                    "description": "Type of query to analyze",
                    "enum": ["contact", "tag"],
                    "default": "contact",
                },
            },
            "required": ["filters"],
        },
    },
    {
        "name": "set_custom_field_values",
        "description": "Set custom field values across multiple contacts with individual or common values",
        "function": set_custom_field_values,
        "parameters": {
            "type": "object",
            "properties": {
                "field_id": {
                    "type": "string",
                    "description": "Custom field ID to modify",
                },
                "contact_values": {
                    "type": "object",
                    "description": "Dictionary mapping contact IDs to field values for individual values per contact",
                },
                "contact_ids": {
                    "type": "array",
                    "description": "List of contact IDs (when using common_value)",
                    "items": {"type": "string"},
                },
                "common_value": {
                    "description": "Value to set for all contacts in contact_ids (any type)"
                },
            },
            "required": ["field_id"],
            "oneOf": [
                {
                    "required": ["contact_values"],
                    "not": {
                        "anyOf": [
                            {"required": ["contact_ids"]},
                            {"required": ["common_value"]},
                        ]
                    },
                },
                {
                    "required": ["contact_ids", "common_value"],
                    "not": {"required": ["contact_values"]},
                },
            ],
        },
    },
    {
        "name": "get_api_diagnostics",
        "description": "Get comprehensive API diagnostics, performance metrics, and system information",
        "function": get_api_diagnostics,
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


def get_available_tools():
    """Get list of all available MCP tools."""
    return MCP_TOOLS


def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get tool definition by name."""
    for tool in MCP_TOOLS:
        if tool["name"] == name:
            return tool
    return None
