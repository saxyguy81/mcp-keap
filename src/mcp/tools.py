"""
Simplified MCP Tools for Keap CRM integration.

This module provides the main MCP tool interface, combining contact and tag tools
with optimization strategies for better performance.
"""

import logging
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import Context

from src.api.client import KeapApiService
from src.cache.manager import CacheManager

logger = logging.getLogger(__name__)


# Initialize shared components
def get_api_client() -> KeapApiService:
    """Get or create API client instance."""
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
    include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """List contacts with optional filtering and pagination."""
    from src.mcp.contact_tools import list_contacts as _list_contacts
    
    # Set up context with shared components
    if not hasattr(context, 'api_client'):
        context.api_client = get_api_client()
    if not hasattr(context, 'cache_manager'):
        context.cache_manager = get_cache_manager()
    
    return await _list_contacts(
        context=context,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_direction=order_direction,
        include=include
    )


async def get_tags(
    context: Context,
    filters: Optional[List[Dict[str, Any]]] = None,
    include_categories: bool = True,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """Get tags with optional filtering."""
    from src.mcp.tag_tools import get_tags as _get_tags
    
    # Set up context with shared components
    if not hasattr(context, 'api_client'):
        context.api_client = get_api_client()
    if not hasattr(context, 'cache_manager'):
        context.cache_manager = get_cache_manager()
    
    return await _get_tags(
        context=context,
        filters=filters,
        include_categories=include_categories,
        limit=limit
    )


async def search_contacts_by_email(
    context: Context,
    email: str,
    include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search contacts by email address."""
    from src.mcp.contact_tools import search_contacts_by_email as _search_by_email
    
    # Set up context
    if not hasattr(context, 'api_client'):
        context.api_client = get_api_client()
    if not hasattr(context, 'cache_manager'):
        context.cache_manager = get_cache_manager()
    
    return await _search_by_email(
        context=context,
        email=email,
        include=include
    )


async def search_contacts_by_name(
    context: Context,
    name: str,
    include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search contacts by name."""
    from src.mcp.contact_tools import search_contacts_by_name as _search_by_name
    
    # Set up context
    if not hasattr(context, 'api_client'):
        context.api_client = get_api_client()
    if not hasattr(context, 'cache_manager'):
        context.cache_manager = get_cache_manager()
    
    return await _search_by_name(
        context=context,
        name=name,
        include=include
    )


async def get_contacts_with_tag(
    context: Context,
    tag_id: str,
    limit: int = 200,
    include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Get contacts that have a specific tag."""
    from src.mcp.tag_tools import get_contacts_with_tag as _get_contacts_with_tag
    
    # Set up context
    if not hasattr(context, 'api_client'):
        context.api_client = get_api_client()
    if not hasattr(context, 'cache_manager'):
        context.cache_manager = get_cache_manager()
    
    return await _get_contacts_with_tag(
        context=context,
        tag_id=tag_id,
        limit=limit,
        include=include
    )


async def modify_tags(
    context: Context,
    contact_ids: List[str],
    tag_ids: List[str],
    action: str = "add"
) -> Dict[str, Any]:
    """Add or remove tags from contacts."""
    # Set up context
    if not hasattr(context, 'api_client'):
        context.api_client = get_api_client()
    if not hasattr(context, 'cache_manager'):
        context.cache_manager = get_cache_manager()
    
    try:
        if action == "add":
            for tag_id in tag_ids:
                result = await context.api_client.apply_tag_to_contacts(tag_id, contact_ids)
                if not result.get("success", False):
                    return {"success": False, "error": f"Failed to apply tag {tag_id}"}
        elif action == "remove":
            for tag_id in tag_ids:
                result = await context.api_client.remove_tag_from_contacts(tag_id, contact_ids)
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
                    "items": {"type": "object"}
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of contacts to return",
                    "default": 200
                },
                "offset": {
                    "type": "integer", 
                    "description": "Number of contacts to skip",
                    "default": 0
                },
                "order_by": {
                    "type": "string",
                    "description": "Field to order by"
                },
                "order_direction": {
                    "type": "string",
                    "enum": ["ASC", "DESC"],
                    "default": "ASC"
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"}
                }
            }
        }
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
                    "items": {"type": "object"}
                },
                "include_categories": {
                    "type": "boolean",
                    "description": "Include category information",
                    "default": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of tags to return",
                    "default": 1000
                }
            }
        }
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
                    "description": "Email address to search for"
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"}
                }
            },
            "required": ["email"]
        }
    },
    {
        "name": "search_contacts_by_name",
        "description": "Search contacts by name (first or last)",
        "function": search_contacts_by_name,
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to search for"
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"}
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_contacts_with_tag",
        "description": "Get contacts that have a specific tag",
        "function": get_contacts_with_tag,
        "parameters": {
            "type": "object",
            "properties": {
                "tag_id": {
                    "type": "string",
                    "description": "Tag ID to search for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of contacts to return",
                    "default": 200
                },
                "include": {
                    "type": "array",
                    "description": "Fields to include in response",
                    "items": {"type": "string"}
                }
            },
            "required": ["tag_id"]
        }
    }
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