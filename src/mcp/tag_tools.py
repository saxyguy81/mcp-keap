"""
Tag-related MCP tools for Keap CRM integration.
"""

import time
import logging
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import Context

from src.api.client import KeapApiService
from src.cache.manager import CacheManager

logger = logging.getLogger(__name__)


async def get_tags(
    context: Context,
    filters: Optional[List[Dict[str, Any]]] = None,
    include_categories: bool = True,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Get tags from Keap CRM with optional filtering.
    
    Args:
        context: MCP context
        filters: List of filter conditions for tags
        include_categories: Whether to include category information
        limit: Maximum number of tags to return
        
    Returns:
        List of tag records
    """
    start_time = time.time()
    
    try:
        # Get API client
        api_client = getattr(context, 'api_client', KeapApiService())
        
        # Get cache manager
        cache_manager = getattr(context, 'cache_manager', CacheManager())
        
        # Create cache key
        cache_key = f"tags:{include_categories}:{limit}:{hash(str(filters))}"
        cached_tags = await cache_manager.get(cache_key)
        
        if cached_tags:
            logger.info(f"Retrieved {len(cached_tags)} tags from cache")
            return cached_tags
        
        # Fetch tags from API
        response = await api_client.get_tags(limit=limit)
        tags = response.get('tags', [])
        
        # Apply filters if specified
        if filters:
            tags = _apply_tag_filters(tags, filters)
        
        # Enhance with category information if requested
        if include_categories:
            tags = await _enhance_tags_with_categories(api_client, tags)
        
        # Cache the result for 1 hour
        await cache_manager.set(cache_key, tags, ttl=3600)
        
        execution_time = time.time() - start_time
        logger.info(f"Retrieved {len(tags)} tags in {execution_time:.2f}s")
        
        return tags
        
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise


async def get_tag_by_id(
    context: Context,
    tag_id: str,
    include_category: bool = True
) -> Dict[str, Any]:
    """
    Get a specific tag by ID.
    
    Args:
        context: MCP context
        tag_id: Tag ID to retrieve
        include_category: Whether to include category information
        
    Returns:
        Tag record
    """
    try:
        # Get API client
        api_client = getattr(context, 'api_client', KeapApiService())
        
        # Get cache manager  
        cache_manager = getattr(context, 'cache_manager', CacheManager())
        
        # Check cache first
        cache_key = f"tag:{tag_id}"
        cached_tag = await cache_manager.get(cache_key)
        
        if cached_tag:
            tag = cached_tag
        else:
            # Fetch from API
            tag = await api_client.get_tag(tag_id)
            
            # Cache for 1 hour
            await cache_manager.set(cache_key, tag, ttl=3600)
        
        # Enhance with category if requested
        if include_category and 'category' not in tag:
            tag = await _enhance_tags_with_categories(api_client, [tag])
            tag = tag[0] if tag else {}
        
        return tag
        
    except Exception as e:
        logger.error(f"Error getting tag {tag_id}: {e}")
        raise


async def search_tags(
    context: Context,
    search_term: str,
    include_categories: bool = True
) -> List[Dict[str, Any]]:
    """
    Search tags by name.
    
    Args:
        context: MCP context
        search_term: Term to search for in tag names
        include_categories: Whether to include category information
        
    Returns:
        List of matching tags
    """
    try:
        # Create name filter
        filters = [{
            "field": "name",
            "operator": "CONTAINS",
            "value": search_term
        }]
        
        return await get_tags(
            context=context,
            filters=filters,
            include_categories=include_categories
        )
        
    except Exception as e:
        logger.error(f"Error searching tags for '{search_term}': {e}")
        raise


async def get_contacts_with_tag(
    context: Context,
    tag_id: str,
    limit: int = 200,
    include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get all contacts that have a specific tag.
    
    Args:
        context: MCP context
        tag_id: Tag ID to search for
        limit: Maximum number of contacts to return
        include: Fields to include in contact response
        
    Returns:
        List of contacts with the specified tag
    """
    try:
        # Import contact tools to avoid circular import
        from src.mcp.contact_tools import list_contacts
        
        # Create tag filter
        filters = [{
            "field": "tags",
            "operator": "CONTAINS",
            "value": tag_id
        }]
        
        return await list_contacts(
            context=context,
            filters=filters,
            limit=limit,
            include=include
        )
        
    except Exception as e:
        logger.error(f"Error getting contacts with tag {tag_id}: {e}")
        raise


def _apply_tag_filters(tags: List[Dict[str, Any]], 
                      filters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply filters to tag list."""
    filtered_tags = []
    
    for tag in tags:
        include_tag = True
        
        for filter_condition in filters:
            field = filter_condition.get('field')
            operator = filter_condition.get('operator')
            value = filter_condition.get('value', '').lower()
            
            if field == 'name':
                tag_name = tag.get('name', '').lower()
                
                if operator == 'CONTAINS':
                    if value not in tag_name:
                        include_tag = False
                        break
                elif operator == 'EQUALS':
                    if value != tag_name:
                        include_tag = False
                        break
                elif operator == 'STARTS_WITH':
                    if not tag_name.startswith(value):
                        include_tag = False
                        break
            
            elif field == 'category':
                category_name = tag.get('category', {}).get('name', '').lower()
                
                if operator == 'EQUALS':
                    if value != category_name:
                        include_tag = False
                        break
                elif operator == 'CONTAINS':
                    if value not in category_name:
                        include_tag = False
                        break
        
        if include_tag:
            filtered_tags.append(tag)
    
    return filtered_tags


async def _enhance_tags_with_categories(api_client: KeapApiService, 
                                       tags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enhance tags with category information."""
    # For now, return tags as-is since category info is typically included
    # This can be enhanced to fetch additional category details if needed
    return tags


# MCP tool definitions for tag operations
TAG_TOOLS = [
    {
        "name": "get_tags",
        "description": "Get tags from Keap CRM with optional filtering",
        "function": get_tags
    },
    {
        "name": "get_tag_by_id",
        "description": "Get a specific tag by ID", 
        "function": get_tag_by_id
    },
    {
        "name": "search_tags",
        "description": "Search tags by name",
        "function": search_tags
    },
    {
        "name": "get_contacts_with_tag",
        "description": "Get all contacts that have a specific tag",
        "function": get_contacts_with_tag
    }
]