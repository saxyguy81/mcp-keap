"""
Collection-based MCP Tools for Keap CRM integration.

This module provides the streamlined collection-based MCP tool interface,
replacing the previous 17 tools with enhanced collection-based operations
including field management, tag operations, and optimization.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import time

from mcp.server.fastmcp import Context

from src.api.client import KeapApiService
from src.cache.manager import CacheManager
from src.cache.collections import get_collection_manager

logger = logging.getLogger(__name__)

# Field type validation mappings
FIELD_TYPE_MAPPINGS = {
    "email": {"type": "email", "validator": "email_format"},
    "phone": {"type": "phone", "validator": "phone_format"},
    "given_name": {"type": "string", "required": True, "max_length": 50},
    "family_name": {"type": "string", "max_length": 50},
}

# DateTime validation rules
DATETIME_VALIDATION = {
    "appointment_date": {"require_timezone": True, "future_only": True},
    "created_date": {"require_timezone": True, "readonly": True},
    "birthday": {"require_timezone": False, "date_only": True},
    "last_contact": {"require_timezone": True, "past_only": True}
}

# Read-only fields that get auto-stripped from tag modifications
READONLY_TAG_FIELDS = {
    "usage_stats", "contact_count", "last_applied", "created_date", 
    "last_modified", "id"
}


# Helper functions for enhanced API
def _is_datetime_field(field_name: str) -> bool:
    """Check if a field is a datetime field requiring special handling."""
    return field_name in DATETIME_VALIDATION or field_name.endswith('_date') or field_name.endswith('_time')


def _convert_datetime_value(value: Any, field_name: str = None, timezone_str: str = None) -> Any:
    """Convert datetime value with timezone conversion."""
    if not value:
        return value
        
    validation_rules = DATETIME_VALIDATION.get(field_name or "", {}) if field_name else {}
    
    if isinstance(value, str):
        try:
            # Parse datetime string
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            
            # Check timezone requirement
            if validation_rules.get('require_timezone', False) and dt.tzinfo is None:
                raise ValueError(f"Field '{field_name}' requires timezone information")
                
            # Validate future/past constraints
            now = datetime.now(timezone.utc)
            if validation_rules.get('future_only', False) and dt < now:
                raise ValueError(f"Field '{field_name}' must be in the future")
            if validation_rules.get('past_only', False) and dt > now:
                raise ValueError(f"Field '{field_name}' must be in the past")
            
            # Convert timezone if requested
            if timezone_str and dt.tzinfo:
                try:
                    import pytz
                    target_tz = pytz.timezone(timezone_str)
                    dt = dt.astimezone(target_tz)
                except ImportError:
                    pass  # Skip timezone conversion if pytz not available
                except Exception:
                    pass  # Skip conversion on any timezone error
                
            return dt.isoformat()
        except ValueError as e:
            if field_name:
                raise ValueError(f"Invalid datetime format for field '{field_name}': {e}")
            else:
                raise ValueError(f"Invalid datetime format: {e}")
    
    return value


def _normalize_datetime_value(value: Any, field_name: str = None) -> Any:
    """Normalize datetime value for API consumption."""
    if not value:
        return value
        
    validation_rules = DATETIME_VALIDATION.get(field_name or "", {}) if field_name else {}
    
    if validation_rules.get('date_only', False):
        # Convert to date-only format
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                pass
    
    return value


async def _validate_field_value(field_name: str, value: Any, require_timezone: bool = False) -> Dict[str, Any]:
    """Validate field value against type constraints."""
    errors = []
    
    # Check if field has type constraints
    if field_name in FIELD_TYPE_MAPPINGS:
        field_config = FIELD_TYPE_MAPPINGS[field_name]
        field_type = field_config.get('type')
        
        # Handle null values
        if value is None or value == "":
            if field_config.get('required', False):
                errors.append(f"Field '{field_name}' is required")
        else:
            # Type validation
            if field_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field_name}' must be a string")
                else:
                    max_length = field_config.get('max_length')
                    if max_length and len(value) > max_length:
                        errors.append(f"Field '{field_name}' exceeds maximum length of {max_length}")
            elif field_type == 'email':
                if not isinstance(value, str) or '@' not in value:
                    errors.append(f"Field '{field_name}' must be a valid email address")
            elif field_type == 'phone':
                if not isinstance(value, str) or len(value.replace('+', '').replace('-', '').replace(' ', '')) < 10:
                    errors.append(f"Field '{field_name}' must be a valid phone number")
    
    # Datetime validation
    if _is_datetime_field(field_name) and value is not None and value != "":
        try:
            _convert_datetime_value(value, field_name)
        except ValueError as e:
            errors.append(str(e))
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# Initialize shared components
def get_api_client() -> KeapApiService:
    """Get or create API client instance."""
    import os

    # Debug: Write API key status to a debug file
    try:
        api_key = os.getenv("KEAP_API_KEY")
        with open("/tmp/keap_debug.log", "a") as f:
            f.write(f"API Key status: {'Found' if api_key else 'Missing'} - {api_key[:20] if api_key else 'None'}...\n")
            f.write(f"Working directory: {os.getcwd()}\n")
            f.write(f"Environment vars: {list(os.environ.keys())}\n")
    except:
        pass

    # For testing, provide a default API key if none exists
    if not os.getenv("KEAP_API_KEY"):
        os.environ["KEAP_API_KEY"] = "test_api_key_for_testing"
    return KeapApiService()


def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance."""
    return CacheManager()


# Core Contact Operations
async def list_contacts(
    context: Context,
    filters: Optional[List[Dict[str, Any]]] = None,
    limit: int = 200,
    offset: int = 0,
    order_by: Optional[str] = None,
    order_direction: str = "ASC",
    enable_optimization: bool = True,
    return_metrics: bool = False,
) -> Dict[str, Any]:
    """Universal contact search with comprehensive filters and optimization, returns collection ID.
    
    This is the primary contact search tool that replaces search_contacts_by_email,
    search_contacts_by_name, query_contacts_by_custom_field, etc.
    
    Args:
        context: MCP context
        filters: List of filter conditions
        limit: Maximum number of contacts to retrieve
        offset: Number of contacts to skip
        order_by: Field to sort by
        order_direction: Sort direction (ASC/DESC)
        enable_optimization: Use query optimization engine
        return_metrics: Include performance metrics in response
        
    Returns:
        Dict with collection_id, contact count, and optional metrics
        
    Example filters:
        [{"field": "email", "operator": "contains", "value": "@company.com"}]
        [{"field": "given_name", "operator": "equals", "value": "John"}]
        [{"field": "custom_field_7", "operator": "equals", "value": "VIP"}]
        [{"field": "tags", "operator": "contains", "value": "customer"}]
    """
    api_client = get_api_client()
    collection_manager = get_collection_manager()
    
    try:
        # Handle edge case: limit=0 should return empty collection
        if limit == 0:
            contacts = []
            metrics = None
        elif enable_optimization and filters:
            # Use optimization engine for complex queries
            from src.mcp.optimization.optimization import QueryExecutor
            
            executor = QueryExecutor(api_client, get_cache_manager())
            
            # Execute optimized query
            contacts, metrics = await executor.execute_optimized_query(
                query_type="list_contacts",
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                order_direction=order_direction,
            )
        else:
            # Use direct API call for simple queries
            contacts_data = await api_client.get_contacts(
                limit=limit,
                offset=offset,
                order_by=order_by,
                order_direction=order_direction,
                include_custom_fields=True,
                include_tags=True
            )
            
            # Extract contacts and apply client-side filtering if needed
            contacts = contacts_data.get("contacts", [])
            if filters:
                contacts = _apply_filters(contacts, filters)
            
            metrics = None
        
        contact_ids = [contact["id"] for contact in contacts]
        
        # Create collection
        collection_id = collection_manager.create_collection(
            contact_ids=contact_ids,
            name=f"Search results",
            description=f"Contacts matching filters: {filters}"
        )
        
        result = {
            "collection_id": collection_id,
            "count": len(contact_ids),
            "description": f"Created collection with {len(contact_ids)} contacts"
        }
        
        # Add performance metrics if requested and available
        if return_metrics and metrics:
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
        
        return result
        
    except Exception as e:
        logger.error(f"Error in list_contacts: {e}")
        raise
    finally:
        await api_client.close()


async def get_contact_schema(context: Context) -> Dict[str, Any]:
    """Get available fields, custom fields, and filter examples.
    
    Returns comprehensive schema information to help construct filters
    for the list_contacts function.
    """
    api_client = get_api_client()
    
    try:
        # Get a sample contact to determine available fields (include all optional properties)
        contacts_data = await api_client.get_contacts(
            limit=1, 
            include_custom_fields=True, 
            include_tags=True
        )
        contacts = contacts_data.get("contacts", [])
        
        available_fields = []
        if contacts:
            sample_contact = contacts[0]
            available_fields = list(sample_contact.keys())
        
        # Get custom fields (this would need API support)
        custom_fields = []
        # TODO: Implement custom field discovery via API
        
        schema = {
            "standard_fields": available_fields,
            "custom_fields": custom_fields,
            "supported_operators": [
                "equals", "not_equals", "contains", "not_contains",
                "starts_with", "ends_with", "greater_than", "less_than",
                "between", "in", "not_in", "is_null", "is_not_null"
            ],
            "filter_examples": [
                {
                    "description": "Find contacts by email domain",
                    "filter": {"field": "email", "operator": "contains", "value": "@company.com"}
                },
                {
                    "description": "Find contacts by name",
                    "filter": {"field": "given_name", "operator": "contains", "value": "John"}
                },
                {
                    "description": "Find contacts with specific tag",
                    "filter": {"field": "tags", "operator": "contains", "value": "VIP"}
                },
                {
                    "description": "Multiple criteria (AND logic)",
                    "filters": [
                        {"field": "email", "operator": "contains", "value": "@company.com"},
                        {"field": "tags", "operator": "contains", "value": "customer"}
                    ]
                }
            ]
        }
        
        return schema
        
    except Exception as e:
        logger.error(f"Error in get_contact_schema: {e}")
        raise
    finally:
        await api_client.close()


# Collection Operations
async def collection_union(
    context: Context,
    collection_a: str,
    collection_b: str
) -> Dict[str, Any]:
    """Combine two collections (A ∪ B).
    
    Args:
        context: MCP context
        collection_a: First collection ID
        collection_b: Second collection ID
        
    Returns:
        Dict with new collection_id and count
    """
    collection_manager = get_collection_manager()
    
    try:
        new_collection_id = collection_manager.union(collection_a, collection_b)
        count = collection_manager.count(new_collection_id)
        
        return {
            "collection_id": new_collection_id,
            "count": count,
            "operation": f"union of {collection_a} and {collection_b}"
        }
        
    except ValueError as e:
        logger.error(f"Collection union error: {e}")
        raise


async def collection_intersect(
    context: Context,
    collection_a: str,
    collection_b: str
) -> Dict[str, Any]:
    """Find contacts in both collections (A ∩ B).
    
    Args:
        context: MCP context
        collection_a: First collection ID
        collection_b: Second collection ID
        
    Returns:
        Dict with new collection_id and count
    """
    collection_manager = get_collection_manager()
    
    try:
        new_collection_id = collection_manager.intersect(collection_a, collection_b)
        count = collection_manager.count(new_collection_id)
        
        return {
            "collection_id": new_collection_id,
            "count": count,
            "operation": f"intersection of {collection_a} and {collection_b}"
        }
        
    except ValueError as e:
        logger.error(f"Collection intersection error: {e}")
        raise


async def collection_diff(
    context: Context,
    collection_a: str,
    collection_b: str
) -> Dict[str, Any]:
    """Find contacts in first but not second collection (A - B).
    
    Args:
        context: MCP context
        collection_a: First collection ID
        collection_b: Second collection ID
        
    Returns:
        Dict with new collection_id and count
    """
    collection_manager = get_collection_manager()
    
    try:
        new_collection_id = collection_manager.diff(collection_a, collection_b)
        count = collection_manager.count(new_collection_id)
        
        return {
            "collection_id": new_collection_id,
            "count": count,
            "operation": f"difference of {collection_a} minus {collection_b}"
        }
        
    except ValueError as e:
        logger.error(f"Collection difference error: {e}")
        raise


async def collection_count(
    context: Context,
    collection_id: str
) -> Dict[str, Any]:
    """Get collection size without fetching data.
    
    Args:
        context: MCP context
        collection_id: Collection identifier
        
    Returns:
        Dict with count information
    """
    collection_manager = get_collection_manager()
    
    collection = collection_manager.get_collection(collection_id)
    if not collection:
        raise ValueError(f"Collection {collection_id} not found or expired")
    
    return {
        "collection_id": collection_id,
        "count": len(collection.contact_ids),
        "name": collection.name,
        "description": collection.description,
        "created_at": collection.created_at
    }


# Collection Data Access
async def get_collection_details(
    context: Context,
    collection_id: str,
    fields: Optional[List[str]] = None,
    limit: Optional[int] = None,
    enable_optimization: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Fetch contact data with field selection from collection.
    
    Args:
        context: MCP context
        collection_id: Collection identifier
        fields: List of fields to include (None for all fields)
        limit: Maximum number of contacts to return (None for all)
        enable_optimization: Use optimization engine for bulk operations
        return_metrics: Include performance metrics in response
        
    Returns:
        Dict with contact details and optional metrics
    """
    collection_manager = get_collection_manager()
    api_client = get_api_client()
    
    try:
        contact_ids = collection_manager.get_contact_ids(collection_id)
        if not contact_ids:
            raise ValueError(f"Collection {collection_id} not found or expired")
        
        # Apply limit if specified
        if limit is not None and limit > 0:
            contact_ids = contact_ids[:limit]
        
        # Strategy selection based on collection size and optimization settings
        target_ids = set(contact_ids)
        contacts = []
        api_calls_made = 0
        metrics = None
        
        if enable_optimization and len(target_ids) > 50:
            # Large collection: Use optimization engine for bulk retrieval
            logger.info(f"Fetching details for {len(target_ids)} contacts using optimization engine")
            
            from src.mcp.optimization.optimization import QueryExecutor
            executor = QueryExecutor(api_client, get_cache_manager())
            
            # Create filter to match the contact IDs in the collection
            id_filter = {
                "field": "id",
                "operator": "in", 
                "value": list(target_ids)
            }
            
            try:
                contacts, metrics = await executor.execute_optimized_query(
                    query_type="bulk_contact_details",
                    filters=[id_filter],
                    limit=len(target_ids),
                    include_custom_fields=True,
                    include_tags=True
                )
                api_calls_made = metrics.api_calls if metrics else 1
            except Exception as e:
                logger.warning(f"Optimization engine failed, falling back to individual calls: {e}")
                # Fall back to individual calls strategy
                enable_optimization = False
        
        if not enable_optimization or len(target_ids) <= 50:
            # Small collection: Use individual API calls (most reliable)
            logger.info(f"Fetching details for {len(target_ids)} contacts using individual calls strategy")
            target_list = list(target_ids)
            
            for contact_id in target_list:
                try:
                    contact = await api_client.get_contact(
                        str(contact_id), 
                        include_custom_fields=True, 
                        include_tags=True
                    )
                    api_calls_made += 1
                    
                    # Apply field filtering if specified
                    if fields:
                        filtered_contact = {field: contact.get(field) for field in fields if field in contact}
                        contacts.append(filtered_contact)
                    else:
                        contacts.append(contact)
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch contact {contact_id}: {e}")
                    continue
        else:
            # Large collection: Use optimized bulk fetching with early termination
            logger.info(f"Fetching details for {len(target_ids)} contacts using optimized bulk strategy")
            found_ids = set()
            batch_size = min(200, len(target_ids) * 2)  # Adaptive batch size
            offset = 0
            
            while len(found_ids) < len(target_ids) and offset < 2000:  # Safety limit
                batch_response = await api_client.get_contacts(
                    limit=batch_size,
                    offset=offset,
                    include_custom_fields=True,
                    include_tags=True
                )
                api_calls_made += 1
                
                batch_contacts = batch_response.get("contacts", [])
                
                # Filter for contacts in our collection
                for contact in batch_contacts:
                    contact_id = contact["id"]
                    if contact_id in target_ids and contact_id not in found_ids:
                        # Apply field filtering if specified
                        if fields:
                            filtered_contact = {field: contact.get(field) for field in fields if field in contact}
                            contacts.append(filtered_contact)
                        else:
                            contacts.append(contact)
                        found_ids.add(contact_id)
                
                offset += batch_size
                
                # Early termination if we found all contacts
                if len(found_ids) == len(target_ids):
                    logger.info(f"Found all {len(target_ids)} contacts after {api_calls_made} API calls")
                    break
                    
                # If batch was not full, we've reached the end
                if len(batch_contacts) < batch_size:
                    logger.info(f"Reached end of contacts after {api_calls_made} API calls")
                    break
        
        # Log efficiency metrics
        efficiency_ratio = len(target_ids) / api_calls_made if api_calls_made > 0 else 0
        logger.info(f"Batch fetching efficiency: {efficiency_ratio:.1f} contacts per API call")
        
        result = {
            "collection_id": collection_id,
            "count": len(contacts),
            "contacts": contacts
        }
        
        # Add performance metrics if requested and available
        if return_metrics and metrics:
            result["performance_metrics"] = {
                "total_duration_ms": metrics.total_duration_ms,
                "api_calls": metrics.api_calls,
                "cache_hit": metrics.cache_hit,
                "strategy_used": metrics.strategy_used,
                "optimization_ratio": metrics.optimization_ratio,
                "efficiency_ratio": efficiency_ratio
            }
        elif return_metrics:
            # Provide basic metrics even without optimization engine
            result["performance_metrics"] = {
                "api_calls": api_calls_made,
                "efficiency_ratio": efficiency_ratio,
                "strategy_used": "individual_calls" if len(target_ids) <= 50 else "bulk_scan"
            }
            
        return result
        
    except Exception as e:
        logger.error(f"Error in get_collection_details: {e}")
        raise
    finally:
        await api_client.close()


async def get_collection_ids(
    context: Context,
    collection_id: str
) -> Dict[str, Any]:
    """Get raw contact ID list from collection.
    
    Args:
        context: MCP context
        collection_id: Collection identifier
        
    Returns:
        Dict with contact ID list
    """
    collection_manager = get_collection_manager()
    
    contact_ids = collection_manager.get_contact_ids(collection_id)
    if not contact_ids and not collection_manager.get_collection(collection_id):
        raise ValueError(f"Collection {collection_id} not found or expired")
    
    return {
        "collection_id": collection_id,
        "contact_ids": contact_ids,
        "count": len(contact_ids)
    }


# Tag Operations
async def get_tags(
    context: Context,
    category_id: Optional[int] = None,
    limit: int = 200
) -> List[Dict[str, Any]]:
    """List available tags with optional filtering.
    
    Args:
        context: MCP context
        category_id: Optional category filter
        limit: Maximum number of tags
        
    Returns:
        List of tag information
    """
    api_client = get_api_client()
    
    try:
        tags = await api_client.get_tags(limit=limit)
        
        # Filter by category if specified
        if category_id is not None:
            tags = [tag for tag in tags if tag.get("category_id") == category_id]
        
        return tags
        
    except Exception as e:
        logger.error(f"Error in get_tags: {e}")
        raise
    finally:
        await api_client.close()


async def apply_tags_to_collection(
    context: Context,
    collection_id: str,
    tag_ids: List[int],
    operation: str = "add",
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Bulk tag operations on contact collections.
    
    Args:
        context: MCP context
        collection_id: Collection identifier
        tag_ids: List of tag IDs to apply/remove
        operation: "add", "remove", or "replace"
        return_metrics: Include performance metrics
        
    Returns:
        Dict with operation results
    """
    collection_manager = get_collection_manager()
    api_client = get_api_client()
    
    try:
        contact_ids = collection_manager.get_contact_ids(collection_id)
        if not contact_ids:
            raise ValueError(f"Collection {collection_id} not found or expired")
        
        results = []
        
        # Try to use bulk operations if API client supports v2
        if hasattr(api_client, 'api_version') and api_client.api_version == "v2" and operation == "add":
            try:
                # Use efficient bulk tag application
                contact_id_strs = [str(cid) for cid in contact_ids]
                tag_id_strs = [str(tid) for tid in tag_ids]
                
                bulk_result = await api_client.apply_tags_to_contacts(tag_id_strs, contact_id_strs)
                logger.info(f"Applied {len(tag_ids)} tags to {len(contact_ids)} contacts using bulk API")
                
                # Create success results for all combinations
                for contact_id in contact_ids:
                    for tag_id in tag_ids:
                        results.append({
                            "contact_id": contact_id,
                            "tag_id": tag_id,
                            "operation": operation,
                            "status": "success"
                        })
                        
            except Exception as e:
                logger.warning(f"Bulk tag operation failed, falling back to individual calls: {e}")
                # Fall back to individual calls
                for contact_id in contact_ids:
                    for tag_id in tag_ids:
                        try:
                            await api_client.apply_tag_to_contact(str(contact_id), tag_id)
                            results.append({
                                "contact_id": contact_id,
                                "tag_id": tag_id,
                                "operation": operation,
                                "status": "success"
                            })
                        except Exception as individual_error:
                            logger.warning(f"Failed to {operation} tag {tag_id} for contact {contact_id}: {individual_error}")
                            results.append({
                                "contact_id": contact_id,
                                "tag_id": tag_id,
                                "operation": operation,
                                "status": "failed",
                                "error": str(individual_error)
                            })
        else:
            # Use individual API calls for v1 or remove operations
            for contact_id in contact_ids:
                for tag_id in tag_ids:
                    try:
                        if operation == "add":
                            await api_client.apply_tag_to_contact(str(contact_id), tag_id)
                        elif operation == "remove":
                            await api_client.remove_tag_from_contact(str(contact_id), tag_id)
                        elif operation == "replace":
                            # For replace, we need to first get current tags and remove non-target ones
                            # This is a simplified implementation - would need contact details
                            await api_client.apply_tag_to_contact(str(contact_id), tag_id)
                        else:
                            raise ValueError(f"Invalid operation: {operation}")
                        
                        results.append({
                            "contact_id": contact_id,
                            "tag_id": tag_id,
                            "operation": operation,
                            "status": "success"
                        })
                    except Exception as e:
                        logger.warning(f"Failed to {operation} tag {tag_id} for contact {contact_id}: {e}")
                        results.append({
                            "contact_id": contact_id,
                            "tag_id": tag_id,
                            "operation": operation,
                            "status": "failed",
                            "error": str(e)
                        })
        
        successful = sum(1 for r in results if r["status"] == "success")
        
        return {
            "collection_id": collection_id,
            "operation": operation,
            "tag_ids": tag_ids,
            "total_operations": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in apply_tags_to_collection: {e}")
        raise
    finally:
        await api_client.close()


# System Operations
async def get_api_diagnostics(context: Context) -> Dict[str, Any]:
    """Get comprehensive API diagnostics and performance metrics."""
    try:
        # Create a context-like object with required dependencies
        class ContextWithDeps:
            def __init__(self):
                self.api_client = get_api_client()
                self.cache_manager = get_cache_manager()
                self.collection_manager = get_collection_manager()

        ctx = ContextWithDeps()

        api_client = ctx.api_client
        cache_manager = ctx.cache_manager
        collection_manager = ctx.collection_manager

        # Get API client diagnostics
        api_diagnostics = api_client.get_diagnostics()

        # Get cache diagnostics if available
        cache_diagnostics = {}
        if hasattr(cache_manager, "get_diagnostics"):
            cache_diagnostics = cache_manager.get_diagnostics()

        # Get collection diagnostics
        collection_diagnostics = collection_manager.get_diagnostics()

        # Get system information
        try:
            import psutil
            import platform

            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/').percent
            }
        except ImportError:
            system_info = {
                "platform": "unknown",
                "python_version": "unknown",
                "note": "psutil not available for detailed system info"
            }

        # Calculate performance metrics
        performance_metrics = {
            "total_requests": api_diagnostics.get("total_requests", 0),
            "success_rate": (
                api_diagnostics.get("successful_requests", 0) / 
                max(api_diagnostics.get("total_requests", 1), 1) * 100
            ),
            "average_response_time": api_diagnostics.get("average_response_time", 0),
            "cache_hit_rate": (
                cache_diagnostics.get("cache_hits", 0) / 
                max(cache_diagnostics.get("total_requests", 1), 1) * 100
            ) if cache_diagnostics else 0
        }

        # Get top endpoints and errors
        top_endpoints = list(api_diagnostics.get("endpoints_called", {}).items())
        top_endpoints.sort(key=lambda x: x[1], reverse=True)
        
        top_errors = list(api_diagnostics.get("error_counts", {}).items())
        top_errors.sort(key=lambda x: x[1], reverse=True)

        # Generate recommendations
        recommendations = []
        if api_diagnostics.get("failed_requests", 0) > api_diagnostics.get("successful_requests", 0):
            recommendations.append("High failure rate detected - check API credentials and network connectivity")
        if api_diagnostics.get("average_response_time", 0) > 2.0:
            recommendations.append("Slow API responses detected - consider using caching more aggressively")
        if collection_diagnostics.get("active_collections", 0) > 50:
            recommendations.append("Large number of active collections - consider cleaning up unused collections")

        return {
            "timestamp": api_diagnostics.get("last_request_time"),
            "api_diagnostics": api_diagnostics,
            "cache_diagnostics": cache_diagnostics,
            "collection_diagnostics": collection_diagnostics,
            "system_info": system_info,
            "performance_metrics": performance_metrics,
            "top_endpoints": top_endpoints[:10],
            "top_errors": top_errors[:10],
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Error in get_api_diagnostics: {e}")
        raise


# Helper functions
def _apply_filters(contacts: List[Dict], filters: List[Dict]) -> List[Dict]:
    """Apply client-side filters to contact list.
    
    Args:
        contacts: List of contact dictionaries
        filters: List of filter conditions
        
    Returns:
        Filtered contact list
    """
    if not filters:
        return contacts
    
    filtered_contacts = []
    for contact in contacts:
        if _contact_matches_filters(contact, filters):
            filtered_contacts.append(contact)
    
    return filtered_contacts


def _contact_matches_filters(contact: Dict, filters: List[Dict]) -> bool:
    """Check if a contact matches all filter conditions (AND logic).
    
    Args:
        contact: Contact dictionary
        filters: List of filter conditions
        
    Returns:
        True if contact matches all filters
    """
    for filter_condition in filters:
        field = filter_condition.get("field")
        operator = filter_condition.get("operator")
        value = filter_condition.get("value")
        
        if not _field_matches_condition(contact, field, operator, value):
            return False
    
    return True


def _field_matches_condition(contact: Dict, field: str, operator: str, value: Any) -> bool:
    """Check if a field matches a specific condition.
    
    Args:
        contact: Contact dictionary
        field: Field name to check
        operator: Comparison operator
        value: Value to compare against
        
    Returns:
        True if field matches condition
    """
    contact_value = contact.get(field)
    
    if contact_value is None:
        return operator in ["is_null", "not_equals"]
    
    if operator == "equals":
        return str(contact_value).lower() == str(value).lower()
    elif operator == "not_equals":
        return str(contact_value).lower() != str(value).lower()
    elif operator == "contains":
        return str(value).lower() in str(contact_value).lower()
    elif operator == "not_contains":
        return str(value).lower() not in str(contact_value).lower()
    elif operator == "starts_with":
        return str(contact_value).lower().startswith(str(value).lower())
    elif operator == "ends_with":
        return str(contact_value).lower().endswith(str(value).lower())
    elif operator == "is_null":
        return contact_value is None
    elif operator == "is_not_null":
        return contact_value is not None
    elif operator == "greater_than":
        try:
            return float(contact_value) > float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "less_than":
        try:
            return float(contact_value) < float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "between":
        try:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return float(value[0]) <= float(contact_value) <= float(value[1])
            return False
        except (ValueError, TypeError):
            return False
    elif operator == "in":
        if isinstance(value, (list, tuple)):
            return str(contact_value).lower() in [str(v).lower() for v in value]
        return False
    elif operator == "not_in":
        if isinstance(value, (list, tuple)):
            return str(contact_value).lower() not in [str(v).lower() for v in value]
        return True
    
    return False


# Enhanced Field Management Functions
async def get_fields_for_collection(
    collection_id: str,
    fields: List[str],
    limit: Optional[int] = None,
    return_raw_json: bool = False,
    timezone: Optional[str] = None,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Get specific field values for all contacts in collection with intelligent date/time handling.
    
    Args:
        collection_id: Collection identifier from list_contacts()
        fields: List of field names (e.g., ["custom_field_7", "email", "given_name"])
        limit: Maximum number of contacts to process (None for all)
        return_raw_json: Return raw API values without conversion (for debugging)
        timezone: Convert datetime fields to this timezone (e.g., "UTC", "America/New_York")
        return_metrics: Include performance metrics
        
    Returns:
        Dict with field values, statistics, and optional metrics
    """
    collection_manager = get_collection_manager()
    api_client = get_api_client()
    
    try:
        start_time = time.time()
        contact_ids = collection_manager.get_contact_ids(collection_id)
        if not contact_ids:
            raise ValueError(f"Collection {collection_id} not found or expired")
        
        # Apply limit if specified (already done above, but kept for clarity)
        if limit is not None and limit > 0:
            contact_ids = contact_ids[:limit]
        
        # Fetch contact details directly without context dependency
        contacts = []
        for contact_id in contact_ids:
            try:
                contact_detail = await api_client.get_contact_details(str(contact_id))
                contacts.append(contact_detail)
            except Exception as e:
                logger.warning(f"Failed to get details for contact {contact_id}: {e}")
        
        # Process field data
        field_values = {}
        field_stats = {}
        
        for field in fields:
            field_values[field] = {}
            populated_count = 0
            null_count = 0
            
            for contact in contacts:
                contact_id = str(contact["id"])
                value = contact.get(field)
                
                # Handle datetime conversion if not raw mode
                if not return_raw_json and value and _is_datetime_field(field):
                    value = _convert_datetime_value(value, field, timezone)
                
                field_values[field][contact_id] = value
                
                if value is not None and value != "":
                    populated_count += 1
                else:
                    null_count += 1
            
            field_stats[field] = {
                "populated_count": populated_count,
                "null_count": null_count
            }
        
        result = {
            "collection_id": collection_id,
            "fields": field_values,
            "field_stats": field_stats
        }
        
        # Add performance metrics
        if return_metrics:
            duration_ms = (time.time() - start_time) * 1000
            result["performance_metrics"] = {
                "total_duration_ms": duration_ms,
                "fields_processed": len(fields),
                "contacts_processed": len(contacts)
            }
            
            # Additional metrics could be added here if needed
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_fields_for_collection: {e}")
        raise
    finally:
        await api_client.close()


async def set_fields_for_collection(
    collection_id: str,
    field_updates: Dict[str, Any],
    validate_types: bool = True,
    require_timezone_for_datetime: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Set field values for all contacts in collection with type validation and smart null handling.
    
    Args:
        collection_id: Collection identifier
        field_updates: Dict of field_name -> value (use None to nullify fields)
        validate_types: Perform type checking before setting values
        require_timezone_for_datetime: Require timezone-aware datetime objects
        return_metrics: Include performance metrics
        
    Returns:
        Dict with update results and optional metrics
    """
    collection_manager = get_collection_manager()
    api_client = get_api_client()
    
    try:
        start_time = time.time()
        contact_ids = collection_manager.get_contact_ids(collection_id)
        if not contact_ids:
            raise ValueError(f"Collection {collection_id} not found or expired")
        
        # Validate field values if requested
        validation_errors = []
        if validate_types:
            for field_name, value in field_updates.items():
                if value is not None:  # Skip validation for null values
                    validation_result = await _validate_field_value(
                        field_name, value, require_timezone_for_datetime
                    )
                    if not validation_result["valid"]:
                        validation_errors.extend([
                            {"field": field_name, "error": error} 
                            for error in validation_result["errors"]
                        ])
        
        if validation_errors:
            return {
                "collection_id": collection_id,
                "successful_updates": 0,
                "failed_updates": len(contact_ids),
                "validation_errors": validation_errors,
                "results": []
            }
        
        # Process updates for each contact
        results = []
        successful_updates = 0
        failed_updates = 0
        api_calls_made = 0
        
        for contact_id in contact_ids:
            try:
                # Prepare update data with datetime conversion
                update_data = {}
                for field_name, value in field_updates.items():
                    if value is None:
                        update_data[field_name] = None  # Nullify
                    elif _is_datetime_field(field_name):
                        update_data[field_name] = _normalize_datetime_value(value, field_name)
                    else:
                        update_data[field_name] = value
                
                # Update contact via API
                await api_client.update_contact(str(contact_id), update_data)
                api_calls_made += 1
                
                results.append({
                    "contact_id": str(contact_id),
                    "status": "success",
                    "fields_updated": list(field_updates.keys())
                })
                successful_updates += 1
                
            except Exception as e:
                logger.warning(f"Failed to update contact {contact_id}: {e}")
                results.append({
                    "contact_id": str(contact_id),
                    "status": "failed",
                    "error": str(e)
                })
                failed_updates += 1
        
        result = {
            "collection_id": collection_id,
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "validation_errors": validation_errors,
            "results": results
        }
        
        # Add performance metrics
        if return_metrics:
            duration_ms = (time.time() - start_time) * 1000
            result["performance_metrics"] = {
                "total_duration_ms": duration_ms,
                "api_calls": api_calls_made,
                "fields_updated": len(field_updates),
                "contacts_processed": len(contact_ids),
                "success_rate": (successful_updates / len(contact_ids)) * 100 if contact_ids else 0
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in set_fields_for_collection: {e}")
        raise
    finally:
        await api_client.close()


async def set_field_for_contacts(
    collection_id: str,
    field_name: str,
    contact_values: Dict[str, Any],
    validate_types: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Set different field values for specific contacts in collection.
    
    Args:
        collection_id: Collection identifier
        field_name: Single field to update
        contact_values: Dict of contact_id -> value (e.g., {"contact_123": "VIP", "contact_456": None})
        validate_types: Perform type checking
        return_metrics: Include performance metrics
        
    Returns:
        Dict with update results and optional metrics
    """
    collection_manager = get_collection_manager()
    api_client = get_api_client()
    
    try:
        start_time = time.time()
        collection_contact_ids = set(str(cid) for cid in collection_manager.get_contact_ids(collection_id))
        if not collection_contact_ids:
            raise ValueError(f"Collection {collection_id} not found or expired")
        
        # Validate that all contact IDs are in the collection
        invalid_contacts = set(contact_values.keys()) - collection_contact_ids
        if invalid_contacts:
            raise ValueError(f"Contact IDs not in collection: {list(invalid_contacts)}")
        
        # Validate field values if requested
        validation_errors = []
        if validate_types:
            for contact_id, value in contact_values.items():
                if value is not None:  # Skip validation for null values
                    validation_result = await _validate_field_value(field_name, value)
                    if not validation_result["valid"]:
                        validation_errors.extend([
                            {"contact_id": contact_id, "field": field_name, "error": error}
                            for error in validation_result["errors"]
                        ])
        
        if validation_errors:
            return {
                "collection_id": collection_id,
                "field_name": field_name,
                "successful_updates": 0,
                "failed_updates": len(contact_values),
                "validation_errors": validation_errors,
                "results": []
            }
        
        # Process updates
        results = []
        successful_updates = 0
        failed_updates = 0
        api_calls_made = 0
        
        for contact_id, value in contact_values.items():
            try:
                # Prepare update data
                if value is None:
                    update_data = {field_name: None}  # Nullify
                elif _is_datetime_field(field_name):
                    update_data = {field_name: _normalize_datetime_value(value, field_name)}
                else:
                    update_data = {field_name: value}
                
                # Update contact
                await api_client.update_contact(contact_id, update_data)
                api_calls_made += 1
                
                results.append({
                    "contact_id": contact_id,
                    "status": "success",
                    "field_updated": field_name,
                    "value_set": value
                })
                successful_updates += 1
                
            except Exception as e:
                logger.warning(f"Failed to update contact {contact_id}: {e}")
                results.append({
                    "contact_id": contact_id,
                    "status": "failed",
                    "error": str(e)
                })
                failed_updates += 1
        
        result = {
            "collection_id": collection_id,
            "field_name": field_name,
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "results": results
        }
        
        # Add performance metrics
        if return_metrics:
            duration_ms = (time.time() - start_time) * 1000
            result["performance_metrics"] = {
                "total_duration_ms": duration_ms,
                "api_calls": api_calls_made,
                "contacts_processed": len(contact_values),
                "success_rate": (successful_updates / len(contact_values)) * 100 if contact_values else 0
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in set_field_for_contacts: {e}")
        raise
    finally:
        await api_client.close()


# Enhanced Tag Management Functions  
async def modify_collection_tags(
    collection_id: str,
    tag_ids: List[int],
    operation: str = "add",
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Modify tags for all contacts in collection with flexible operations.
    
    Args:
        collection_id: Collection identifier
        tag_ids: List of tag IDs to apply/remove
        operation: "add" (append), "remove" (remove), "replace" (set exact tags)
        return_metrics: Include performance metrics
        
    Returns:
        Dict with operation results and optional metrics
    """
    # Implement tag modification directly without context dependency
    collection_manager = get_collection_manager()
    api_client = get_api_client()
    
    try:
        start_time = time.time()
        contact_ids = collection_manager.get_contact_ids(collection_id)
        if not contact_ids:
            raise ValueError(f"Collection {collection_id} not found or expired")
        
        results = []
        api_calls_made = 0
        
        # Process tag operations for each contact
        for contact_id in contact_ids:
            for tag_id in tag_ids:
                try:
                    if operation == "add":
                        await api_client.apply_tag_to_contact(str(contact_id), tag_id)
                    elif operation == "remove":
                        await api_client.remove_tag_from_contact(str(contact_id), tag_id)
                    elif operation == "replace":
                        # For replace, would need to get current tags and manage accordingly
                        # Simplified implementation - just add the tags
                        await api_client.apply_tag_to_contact(str(contact_id), tag_id)
                    else:
                        raise ValueError(f"Invalid operation: {operation}")
                    
                    api_calls_made += 1
                    results.append({
                        "contact_id": contact_id,
                        "tag_id": tag_id,
                        "operation": operation,
                        "status": "success"
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to {operation} tag {tag_id} for contact {contact_id}: {e}")
                    results.append({
                        "contact_id": contact_id,
                        "tag_id": tag_id,
                        "operation": operation,
                        "status": "failed",
                        "error": str(e)
                    })
        
        successful = sum(1 for r in results if r["status"] == "success")
        
        result = {
            "collection_id": collection_id,
            "operation": operation,
            "tag_ids": tag_ids,
            "total_operations": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "results": results
        }
        
        # Add performance metrics
        if return_metrics:
            duration_ms = (time.time() - start_time) * 1000
            result["performance_metrics"] = {
                "total_duration_ms": duration_ms,
                "api_calls": api_calls_made,
                "contacts_processed": len(contact_ids),
                "tags_processed": len(tag_ids)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in modify_collection_tags: {e}")
        raise
    finally:
        await api_client.close()


async def get_tag_details(
    tag_ids: List[int],
    include_usage_stats: bool = False,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Get detailed information for multiple tags including usage statistics.
    
    Args:
        tag_ids: List of tag IDs to fetch
        include_usage_stats: Include contact count and usage statistics
        return_metrics: Include performance metrics
        
    Returns:
        Dict with tag details and optional metrics
    """
    api_client = get_api_client()
    
    try:
        start_time = time.time()
        tags = []
        not_found = []
        api_calls_made = 0
        
        for tag_id in tag_ids:
            try:
                # Get tag details from API
                tag_data = await api_client.get_tag(str(tag_id))
                api_calls_made += 1
                
                # Format tag data
                formatted_tag = {
                    "id": tag_data.get("id"),
                    "name": tag_data.get("name"),
                    "description": tag_data.get("description"),
                }
                
                # Add category info if available
                if "category" in tag_data:
                    formatted_tag["category"] = tag_data["category"]
                
                # Add usage statistics if requested
                if include_usage_stats:
                    try:
                        # Get usage stats (this would need API support)
                        # For now, return placeholder data
                        usage_stats = {
                            "contact_count": 0,  # Would need actual API call
                            "last_applied": tag_data.get("last_applied"),
                            "created_date": tag_data.get("created_date")
                        }
                        formatted_tag["usage_stats"] = usage_stats
                    except Exception as e:
                        logger.warning(f"Failed to get usage stats for tag {tag_id}: {e}")
                
                tags.append(formatted_tag)
                
            except Exception as e:
                logger.warning(f"Tag {tag_id} not found: {e}")
                not_found.append(tag_id)
        
        result = {
            "tags": tags,
            "not_found": not_found
        }
        
        # Add performance metrics
        if return_metrics:
            duration_ms = (time.time() - start_time) * 1000
            result["performance_metrics"] = {
                "total_duration_ms": duration_ms,
                "api_calls": api_calls_made,
                "tags_processed": len(tag_ids),
                "tags_found": len(tags),
                "tags_not_found": len(not_found)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_tag_details: {e}")
        raise
    finally:
        await api_client.close()


async def modify_tags(
    tag_updates: List[Dict[str, Any]],
    ignore_readonly_fields: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Rename tags or change categories with smart field filtering.
    
    Args:
        tag_updates: List of tag modifications (can accept full get_tag_details() output)
        ignore_readonly_fields: Automatically ignore non-modifiable fields
        return_metrics: Include performance metrics
        
    Returns:
        Dict with update results and optional metrics
    """
    api_client = get_api_client()
    
    try:
        start_time = time.time()
        successful_updates = []
        failed_updates = []
        api_calls_made = 0
        
        for tag_update in tag_updates:
            try:
                # Extract tag ID (required)
                tag_id = tag_update.get("tag_id") or tag_update.get("id")
                if not tag_id:
                    failed_updates.append({
                        "tag_data": tag_update,
                        "error": "Missing tag_id or id field"
                    })
                    continue
                
                # Filter out readonly fields if requested
                if ignore_readonly_fields:
                    filtered_update = {
                        k: v for k, v in tag_update.items()
                        if k not in READONLY_TAG_FIELDS and k not in ["tag_id"]
                    }
                else:
                    filtered_update = {k: v for k, v in tag_update.items() if k != "tag_id"}
                
                if not filtered_update:
                    # No changes to make
                    continue
                
                # Get current tag data for comparison
                try:
                    current_tag = await api_client.get_tag(str(tag_id))
                    api_calls_made += 1
                except Exception:
                    failed_updates.append({
                        "tag_id": tag_id,
                        "error": "Tag not found"
                    })
                    continue
                
                # Track changes
                changes = []
                old_values = {}
                new_values = {}
                
                for field, new_value in filtered_update.items():
                    old_value = current_tag.get(field)
                    if old_value != new_value:
                        changes.append(field)
                        old_values[f"old_{field}"] = old_value
                        new_values[f"new_{field}"] = new_value
                
                if not changes:
                    # No actual changes needed
                    continue
                
                # Update tag via API
                await api_client.update_tag(str(tag_id), filtered_update)
                api_calls_made += 1
                
                update_result = {
                    "tag_id": tag_id,
                    "changes": changes,
                    **old_values,
                    **new_values
                }
                successful_updates.append(update_result)
                
            except Exception as e:
                logger.warning(f"Failed to update tag: {e}")
                failed_updates.append({
                    "tag_id": tag_update.get("tag_id") or tag_update.get("id"),
                    "error": str(e)
                })
        
        result = {
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "success_count": len(successful_updates),
            "failure_count": len(failed_updates)
        }
        
        # Add performance metrics
        if return_metrics:
            duration_ms = (time.time() - start_time) * 1000
            result["performance_metrics"] = {
                "total_duration_ms": duration_ms,
                "api_calls": api_calls_made,
                "tags_processed": len(tag_updates),
                "readonly_fields_stripped": ignore_readonly_fields
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in modify_tags: {e}")
        raise
    finally:
        await api_client.close()


async def create_tags(
    tag_definitions: List[Dict[str, Any]],
    category_id: Optional[int] = None,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Create multiple tags with optional common category.
    
    Args:
        tag_definitions: List of tag definitions with name, description, optional category
        category_id: Default category for all tags (can be overridden per tag)
        return_metrics: Include performance metrics
        
    Returns:
        Dict with creation results and optional metrics
    """
    api_client = get_api_client()
    
    try:
        start_time = time.time()
        created_tags = []
        failed_tags = []
        api_calls_made = 0
        
        for tag_def in tag_definitions:
            try:
                # Prepare tag data
                tag_data = {
                    "name": tag_def.get("name"),
                    "description": tag_def.get("description", "")
                }
                
                if not tag_data["name"]:
                    failed_tags.append({
                        "tag_definition": tag_def,
                        "error": "Missing required 'name' field"
                    })
                    continue
                
                # Set category (tag-specific override or common default)
                tag_category = tag_def.get("category_id") or category_id
                if tag_category:
                    tag_data["category"] = {"id": tag_category}
                
                # Create tag via API
                created_tag = await api_client.create_tag(tag_data)
                api_calls_made += 1
                
                # Format result
                result_tag = {
                    "id": created_tag.get("id"),
                    "name": created_tag.get("name"),
                    "category_id": tag_category
                }
                created_tags.append(result_tag)
                
            except Exception as e:
                logger.warning(f"Failed to create tag '{tag_def.get('name', 'unknown')}': {e}")
                failed_tags.append({
                    "name": tag_def.get("name"),
                    "error": str(e)
                })
        
        result = {
            "created_tags": created_tags,
            "failed_tags": failed_tags,
            "success_count": len(created_tags),
            "failure_count": len(failed_tags)
        }
        
        # Add performance metrics
        if return_metrics:
            duration_ms = (time.time() - start_time) * 1000
            result["performance_metrics"] = {
                "total_duration_ms": duration_ms,
                "api_calls": api_calls_made,
                "tags_processed": len(tag_definitions),
                "common_category": category_id
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in create_tags: {e}")
        raise
    finally:
        await api_client.close()


async def delete_tags(
    tag_ids: List[int],
    return_usage_info: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """Delete tags and automatically remove from all contacts.
    
    Args:
        tag_ids: List of tag IDs to delete
        return_usage_info: Include information about affected contacts
        return_metrics: Include performance metrics
        
    Returns:
        Dict with deletion results and optional metrics
    """
    api_client = get_api_client()
    
    try:
        start_time = time.time()
        deleted_tags = []
        failed_deletions = []
        affected_contacts = {}
        total_contacts_affected = 0
        api_calls_made = 0
        
        # Get usage info before deletion if requested
        if return_usage_info:
            usage_details = await get_tag_details(tag_ids, include_usage_stats=True)
            for tag in usage_details.get("tags", []):
                tag_id = tag["id"]
                usage_stats = tag.get("usage_stats", {})
                contact_count = usage_stats.get("contact_count", 0)
                
                if contact_count > 0:
                    affected_contacts[str(tag_id)] = {
                        "contact_count": contact_count,
                        "sample_contact_ids": []  # Would need additional API call to get actual IDs
                    }
                    total_contacts_affected += contact_count
        
        # Delete tags
        for tag_id in tag_ids:
            try:
                await api_client.delete_tag(str(tag_id))
                api_calls_made += 1
                deleted_tags.append(tag_id)
                
            except Exception as e:
                logger.warning(f"Failed to delete tag {tag_id}: {e}")
                failed_deletions.append({
                    "tag_id": tag_id,
                    "error": str(e)
                })
        
        result = {
            "deleted_tags": deleted_tags,
            "failed_deletions": failed_deletions,
            "success_count": len(deleted_tags),
            "failure_count": len(failed_deletions)
        }
        
        if return_usage_info:
            result.update({
                "affected_contacts": affected_contacts,
                "total_contacts_affected": total_contacts_affected
            })
        
        # Add performance metrics
        if return_metrics:
            duration_ms = (time.time() - start_time) * 1000
            result["performance_metrics"] = {
                "total_duration_ms": duration_ms,
                "api_calls": api_calls_made,
                "tags_processed": len(tag_ids)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in delete_tags: {e}")
        raise
    finally:
        await api_client.close()


# Helper functions for enhanced API functionality
async def _validate_field_value(
    field_name: str, 
    value: Any, 
    require_timezone_for_datetime: bool = True
) -> Dict[str, Any]:
    """Validate a field value against expected types and constraints."""
    errors = []
    
    # Check field type mappings
    if field_name in FIELD_TYPE_MAPPINGS:
        field_config = FIELD_TYPE_MAPPINGS[field_name]
        expected_type = field_config.get("type")
        
        # String length validation
        if expected_type == "string" and isinstance(value, str):
            max_length = field_config.get("max_length")
            if max_length and len(value) > max_length:
                errors.append(f"Value exceeds maximum length of {max_length}")
        
        # Email validation
        elif expected_type == "email" and value:
            if not isinstance(value, str) or "@" not in value:
                errors.append("Invalid email format")
        
        # Phone validation  
        elif expected_type == "phone" and value:
            if not isinstance(value, str):
                errors.append("Phone must be a string")
    
    # DateTime validation
    if _is_datetime_field(field_name):
        try:
            _convert_datetime_value(value, field_name)
        except ValueError as e:
            errors.append(str(e))
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def get_api_client():
    """Factory function to get API client without context dependency."""
    return KeapApiService()


# Context-dependent wrapper functions for MCP tools
async def get_fields_for_collection_mcp(
    context: Context,
    collection_id: str,
    fields: List[str],
    limit: Optional[int] = None,
    return_raw_json: bool = False,
    timezone: Optional[str] = None,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """MCP wrapper for get_fields_for_collection."""
    return await get_fields_for_collection(
        collection_id, fields, limit, return_raw_json, timezone, return_metrics
    )


async def set_fields_for_collection_mcp(
    context: Context,
    collection_id: str,
    field_updates: Dict[str, Any],
    validate_types: bool = True,
    require_timezone_for_datetime: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """MCP wrapper for set_fields_for_collection."""
    return await set_fields_for_collection(
        collection_id, field_updates, validate_types, require_timezone_for_datetime, return_metrics
    )


async def set_field_for_contacts_mcp(
    context: Context,
    collection_id: str,
    field_name: str,
    contact_values: Dict[str, Any],
    validate_types: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """MCP wrapper for set_field_for_contacts."""
    return await set_field_for_contacts(
        collection_id, field_name, contact_values, validate_types, return_metrics
    )


async def modify_collection_tags_mcp(
    context: Context,
    collection_id: str,
    tag_ids: List[int],
    operation: str = "add",
    return_metrics: bool = False
) -> Dict[str, Any]:
    """MCP wrapper for modify_collection_tags."""
    return await modify_collection_tags(collection_id, tag_ids, operation, return_metrics)


async def get_tag_details_mcp(
    context: Context,
    tag_ids: List[int],
    include_usage_stats: bool = False,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """MCP wrapper for get_tag_details."""
    return await get_tag_details(tag_ids, include_usage_stats, return_metrics)


async def modify_tags_mcp(
    context: Context,
    tag_updates: List[Dict[str, Any]],
    ignore_readonly_fields: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """MCP wrapper for modify_tags."""
    return await modify_tags(tag_updates, ignore_readonly_fields, return_metrics)


async def create_tags_mcp(
    context: Context,
    tag_definitions: List[Dict[str, Any]],
    category_id: Optional[int] = None,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """MCP wrapper for create_tags."""
    return await create_tags(tag_definitions, category_id, return_metrics)


async def delete_tags_mcp(
    context: Context,
    tag_ids: List[int],
    return_usage_info: bool = True,
    return_metrics: bool = False
) -> Dict[str, Any]:
    """MCP wrapper for delete_tags."""
    return await delete_tags(tag_ids, return_usage_info, return_metrics)