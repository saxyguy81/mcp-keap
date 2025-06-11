"""
Contact-specific MCP tools for Keap CRM integration.

This module provides contact-related operations including listing, searching,
and filtering contacts with comprehensive error handling.
"""

import logging
from typing import Dict, List, Any, Optional

from src.api.client import KeapApiService
from src.cache.manager import CacheManager
from src.utils.contact_utils import format_contact_data, process_contact_include_fields
from src.utils.filter_utils import (
    validate_filter_conditions,
    optimize_filters_for_api,
    apply_complex_filters,
)

logger = logging.getLogger(__name__)


async def list_contacts(
    context,
    filters: Optional[List[Dict[str, Any]]] = None,
    limit: int = 200,
    offset: int = 0,
    order_by: Optional[str] = None,
    order_direction: str = "ASC",
    include: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """List contacts with optional filtering and pagination."""
    try:
        api_client: KeapApiService = context.api_client
        cache_manager: CacheManager = context.cache_manager

        # Build cache key
        cache_key = f"list_contacts:{hash(str(filters))}{limit}:{offset}:{order_by}:{order_direction}:{hash(str(include))}"

        # Check cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for list_contacts: {cache_key}")
            return cached_result

        # Validate filters if provided
        if filters:
            validate_filter_conditions(filters)

        # Optimize filters - separate server-side vs client-side
        server_params, client_filters = (
            optimize_filters_for_api(filters) if filters else ({}, [])
        )

        # Build API parameters
        params = {
            "limit": limit,
            "offset": offset,
            **server_params,  # Add optimized server-side parameters
        }

        if order_by:
            params["order"] = f"{order_by}.{order_direction.upper()}"

        # Get contacts from API (with server-side filtering applied)
        response = await api_client.get_contacts(**params)
        contacts = response.get("contacts", [])

        # Apply client-side filters for complex conditions
        if client_filters:
            logger.debug(f"Applying {len(client_filters)} client-side filters")
            contacts = apply_complex_filters(contacts, client_filters)

        # Process include fields
        if include:
            contacts = [
                process_contact_include_fields(contact, include) for contact in contacts
            ]

        # Format contact data
        formatted_contacts = [format_contact_data(contact) for contact in contacts]

        # Cache result
        await cache_manager.set(cache_key, formatted_contacts, ttl=1800)  # 30 minutes

        logger.info(f"Retrieved {len(formatted_contacts)} contacts")
        return formatted_contacts

    except Exception as e:
        logger.error(f"Error listing contacts: {e}")
        raise


async def search_contacts_by_email(
    context, email: str, include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search contacts by email address."""
    try:
        api_client: KeapApiService = context.api_client
        cache_manager: CacheManager = context.cache_manager

        cache_key = f"search_email:{email}:{hash(str(include))}"

        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        # Search by email
        params = {"email": email}
        response = await api_client.get_contacts(**params)
        contacts = response.get("contacts", [])

        # Process include fields
        if include:
            contacts = [
                process_contact_include_fields(contact, include) for contact in contacts
            ]

        # Format contacts
        formatted_contacts = [format_contact_data(contact) for contact in contacts]

        # Cache result
        await cache_manager.set(cache_key, formatted_contacts, ttl=1800)

        logger.info(f"Found {len(formatted_contacts)} contacts for email: {email}")
        return formatted_contacts

    except Exception as e:
        logger.error(f"Error searching contacts by email: {e}")
        raise


async def search_contacts_by_name(
    context, name: str, include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search contacts by name (first or last)."""
    try:
        api_client: KeapApiService = context.api_client
        cache_manager: CacheManager = context.cache_manager

        cache_key = f"search_name:{name}:{hash(str(include))}"

        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        # Search by name - try both first and last name
        all_contacts = []

        # Search by first name
        response = await api_client.get_contacts(given_name=name)
        contacts = response.get("contacts", [])
        all_contacts.extend(contacts)

        # Search by last name
        response = await api_client.get_contacts(family_name=name)
        contacts = response.get("contacts", [])
        all_contacts.extend(contacts)

        # Remove duplicates based on ID
        unique_contacts = []
        seen_ids = set()
        for contact in all_contacts:
            contact_id = contact.get("id")
            if contact_id and contact_id not in seen_ids:
                seen_ids.add(contact_id)
                unique_contacts.append(contact)

        # Process include fields
        if include:
            unique_contacts = [
                process_contact_include_fields(contact, include)
                for contact in unique_contacts
            ]

        # Format contacts
        formatted_contacts = [
            format_contact_data(contact) for contact in unique_contacts
        ]

        # Cache result
        await cache_manager.set(cache_key, formatted_contacts, ttl=1800)

        logger.info(f"Found {len(formatted_contacts)} contacts for name: {name}")
        return formatted_contacts

    except Exception as e:
        logger.error(f"Error searching contacts by name: {e}")
        raise


async def get_contact_details(
    context, contact_id: str, include: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get detailed information about a specific contact."""
    try:
        api_client: KeapApiService = context.api_client
        cache_manager: CacheManager = context.cache_manager

        cache_key = f"contact_details:{contact_id}:{hash(str(include))}"

        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        # Get contact details
        contact = await api_client.get_contact(contact_id)

        # Process include fields
        if include:
            contact = process_contact_include_fields(contact, include)

        # Format contact
        formatted_contact = format_contact_data(contact)

        # Cache result
        await cache_manager.set(cache_key, formatted_contact, ttl=3600)  # 1 hour

        logger.info(f"Retrieved details for contact: {contact_id}")
        return formatted_contact

    except Exception as e:
        logger.error(f"Error getting contact details: {e}")
        raise
