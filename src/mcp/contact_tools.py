"""
Contact-related MCP tools for Keap CRM integration.
"""

import time
import logging
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import Context

from src.api.client import KeapApiService
from src.cache.manager import CacheManager
from src.utils.filters import FilterProcessor
from src.schemas.definitions import ContactQueryRequest

logger = logging.getLogger(__name__)


async def list_contacts(
    context: Context,
    filters: Optional[List[Dict[str, Any]]] = None,
    limit: int = 200,
    offset: int = 0,
    order_by: Optional[str] = None,
    order_direction: str = "ASC",
    include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    List contacts from Keap CRM with optional filtering and pagination.
    
    Args:
        context: MCP context
        filters: List of filter conditions
        limit: Maximum number of contacts to return
        offset: Number of contacts to skip
        order_by: Field to order by
        order_direction: ASC or DESC
        include: Fields to include in response
        
    Returns:
        List of contact records
    """
    start_time = time.time()
    
    try:
        # Get API client from context or create new one
        api_client = getattr(context, 'api_client', None)
        if not api_client:
            api_client = KeapApiService()
        
        # Get cache manager
        cache_manager = getattr(context, 'cache_manager', CacheManager())
        
        # Create query request
        query_request = ContactQueryRequest(
            filters=filters or [],
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_direction=order_direction,
            include=include
        )
        
        # Check cache first
        cache_key = f"contacts:{hash(str(query_request.dict()))}"
        cached_result = await cache_manager.get(cache_key)
        
        if cached_result:
            logger.info(f"Retrieved {len(cached_result)} contacts from cache")
            return cached_result
        
        # Process filters if any
        if filters:
            filter_processor = FilterProcessor()
            contacts = await filter_processor.process_contact_filters(
                api_client, filters, limit, offset
            )
        else:
            # Simple query without filters
            response = await api_client.get_contacts(
                limit=limit,
                offset=offset
            )
            contacts = response.get('contacts', [])
        
        # Apply field selection if specified
        if include:
            contacts = _select_contact_fields(contacts, include)
        
        # Apply ordering if specified
        if order_by:
            contacts = _sort_contacts(contacts, order_by, order_direction)
        
        # Cache the result
        await cache_manager.set(cache_key, contacts, ttl=300)  # 5 minutes
        
        execution_time = time.time() - start_time
        logger.info(f"Retrieved {len(contacts)} contacts in {execution_time:.2f}s")
        
        return contacts
        
    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        raise


async def get_contact_by_id(
    context: Context,
    contact_id: str,
    include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Get a specific contact by ID.
    
    Args:
        context: MCP context
        contact_id: Contact ID to retrieve
        include: Fields to include in response
        
    Returns:
        Contact record
    """
    try:
        # Get API client
        api_client = getattr(context, 'api_client', KeapApiService())
        
        # Get cache manager
        cache_manager = getattr(context, 'cache_manager', CacheManager())
        
        # Check cache first
        cache_key = f"contact:{contact_id}"
        cached_contact = await cache_manager.get(cache_key)
        
        if cached_contact:
            contact = cached_contact
        else:
            # Fetch from API
            contact = await api_client.get_contact(contact_id)
            
            # Cache for 10 minutes
            await cache_manager.set(cache_key, contact, ttl=600)
        
        # Apply field selection if specified
        if include:
            contact = _select_contact_fields([contact], include)[0]
        
        return contact
        
    except Exception as e:
        logger.error(f"Error getting contact {contact_id}: {e}")
        raise


async def search_contacts_by_email(
    context: Context,
    email: str,
    include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search contacts by email address.
    
    Args:
        context: MCP context
        email: Email address to search for
        include: Fields to include in response
        
    Returns:
        List of matching contacts
    """
    try:
        # Create email filter
        filters = [{
            "field": "email",
            "operator": "EQUALS",
            "value": email
        }]
        
        return await list_contacts(
            context=context,
            filters=filters,
            include=include
        )
        
    except Exception as e:
        logger.error(f"Error searching contacts by email {email}: {e}")
        raise


async def search_contacts_by_name(
    context: Context,
    name: str,
    include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Search contacts by name (first or last).
    
    Args:
        context: MCP context
        name: Name to search for
        include: Fields to include in response
        
    Returns:
        List of matching contacts
    """
    try:
        # Create name filters (OR condition)
        filters = [{
            "operator": "OR",
            "conditions": [
                {
                    "field": "given_name",
                    "operator": "CONTAINS",
                    "value": name
                },
                {
                    "field": "family_name", 
                    "operator": "CONTAINS",
                    "value": name
                }
            ]
        }]
        
        return await list_contacts(
            context=context,
            filters=filters,
            include=include
        )
        
    except Exception as e:
        logger.error(f"Error searching contacts by name {name}: {e}")
        raise


def _select_contact_fields(contacts: List[Dict[str, Any]], 
                          include: List[str]) -> List[Dict[str, Any]]:
    """Select specific fields from contact records."""
    if not include:
        return contacts
    
    filtered_contacts = []
    for contact in contacts:
        filtered_contact = {}
        for field in include:
            if field in contact:
                filtered_contact[field] = contact[field]
        filtered_contacts.append(filtered_contact)
    
    return filtered_contacts


def _sort_contacts(contacts: List[Dict[str, Any]], 
                  order_by: str, 
                  order_direction: str) -> List[Dict[str, Any]]:
    """Sort contacts by specified field and direction."""
    reverse = order_direction.upper() == "DESC"
    
    try:
        return sorted(
            contacts,
            key=lambda x: x.get(order_by, ""),
            reverse=reverse
        )
    except (TypeError, KeyError):
        logger.warning(f"Could not sort by field: {order_by}")
        return contacts


# MCP tool definitions for contact operations
CONTACT_TOOLS = [
    {
        "name": "list_contacts",
        "description": "List contacts from Keap CRM with optional filtering",
        "function": list_contacts
    },
    {
        "name": "get_contact_by_id", 
        "description": "Get a specific contact by ID",
        "function": get_contact_by_id
    },
    {
        "name": "search_contacts_by_email",
        "description": "Search contacts by email address",
        "function": search_contacts_by_email
    },
    {
        "name": "search_contacts_by_name",
        "description": "Search contacts by name",
        "function": search_contacts_by_name
    }
]