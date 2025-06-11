"""
Tag-specific MCP tools for Keap CRM integration.

This module provides tag-related operations including listing, filtering,
and managing contact-tag relationships.
"""

import logging
from typing import Dict, List, Any, Optional

from src.api.client import KeapApiService
from src.cache.manager import CacheManager
from src.utils.contact_utils import format_contact_data, process_contact_include_fields

logger = logging.getLogger(__name__)


async def get_tags(
    context,
    filters: Optional[List[Dict[str, Any]]] = None,
    include_categories: bool = True,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Get tags with optional filtering."""
    try:
        api_client: KeapApiService = context.api_client
        cache_manager: CacheManager = context.cache_manager

        cache_key = f"get_tags:{hash(str(filters))}:{include_categories}:{limit}"

        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for get_tags: {cache_key}")
            return cached_result

        # Get tags from API
        response = await api_client.get_tags(limit=limit)
        tags = response.get("tags", [])

        # Apply filters if provided
        if filters:
            filtered_tags = []
            for tag in tags:
                include_tag = True

                for filter_condition in filters:
                    field = filter_condition.get("field")
                    value = filter_condition.get("value")
                    operator = filter_condition.get("operator", "equals")

                    if field and value:
                        tag_value = tag.get(field)
                        if not tag_value:
                            include_tag = False
                            break

                        if operator == "contains":
                            if value.lower() not in str(tag_value).lower():
                                include_tag = False
                                break
                        elif operator == "equals":
                            if str(tag_value).lower() != str(value).lower():
                                include_tag = False
                                break

                if include_tag:
                    filtered_tags.append(tag)

            tags = filtered_tags

        # Format tags
        formatted_tags = []
        for tag in tags:
            formatted_tag = {
                "id": tag.get("id"),
                "name": tag.get("name"),
                "description": tag.get("description"),
            }

            if include_categories and "category" in tag:
                formatted_tag["category"] = tag["category"]

            formatted_tags.append(formatted_tag)

        # Cache result
        await cache_manager.set(cache_key, formatted_tags, ttl=3600)  # 1 hour

        logger.info(f"Retrieved {len(formatted_tags)} tags")
        return formatted_tags

    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise


async def get_contacts_with_tag(
    context, tag_id: str, limit: int = 200, include: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Get contacts that have a specific tag."""
    try:
        api_client: KeapApiService = context.api_client
        cache_manager: CacheManager = context.cache_manager

        cache_key = f"contacts_with_tag:{tag_id}:{limit}:{hash(str(include))}"

        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        # Get contacts with tag
        contacts = await api_client.get_contacts_by_tag(tag_id, limit=limit)

        # Process include fields
        if include:
            contacts = [
                process_contact_include_fields(contact, include) for contact in contacts
            ]

        # Format contacts
        formatted_contacts = [format_contact_data(contact) for contact in contacts]

        # Cache result
        await cache_manager.set(cache_key, formatted_contacts, ttl=1800)  # 30 minutes

        logger.info(f"Found {len(formatted_contacts)} contacts with tag {tag_id}")
        return formatted_contacts

    except Exception as e:
        logger.error(f"Error getting contacts with tag: {e}")
        raise


async def get_tag_details(context, tag_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific tag."""
    try:
        api_client: KeapApiService = context.api_client
        cache_manager: CacheManager = context.cache_manager

        cache_key = f"tag_details:{tag_id}"

        # Check cache
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        # Get tag details
        tag = await api_client.get_tag(tag_id)

        # Format tag
        formatted_tag = {
            "id": tag.get("id"),
            "name": tag.get("name"),
            "description": tag.get("description"),
        }

        if "category" in tag:
            formatted_tag["category"] = tag["category"]

        # Cache result
        await cache_manager.set(cache_key, formatted_tag, ttl=3600)  # 1 hour

        logger.info(f"Retrieved details for tag: {tag_id}")
        return formatted_tag

    except Exception as e:
        logger.error(f"Error getting tag details: {e}")
        raise


async def create_tag(
    context,
    name: str,
    description: Optional[str] = None,
    category_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new tag."""
    try:
        api_client: KeapApiService = context.api_client

        tag_data = {"name": name}

        if description:
            tag_data["description"] = description
        if category_id:
            tag_data["category"] = {"id": category_id}

        # Create tag
        new_tag = await api_client.create_tag(tag_data)

        logger.info(f"Created new tag: {name} (ID: {new_tag.get('id')})")
        return new_tag

    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        raise


async def apply_tags_to_contacts(
    context, tag_ids: List[str], contact_ids: List[str]
) -> Dict[str, Any]:
    """Apply multiple tags to multiple contacts using batch operations."""
    try:
        api_client: KeapApiService = context.api_client

        # Use batch API if available
        try:
            await api_client.apply_tags_to_contacts(tag_ids, contact_ids)
            success_count = len(contact_ids) * len(tag_ids)

            logger.info(f"Applied {len(tag_ids)} tags to {len(contact_ids)} contacts")
            return {
                "success": True,
                "message": "Successfully applied tags to contacts",
                "operations_completed": success_count,
                "tag_ids": tag_ids,
                "contact_ids": contact_ids,
            }

        except ValueError:
            # Fallback to individual operations for v1 API
            success_count = 0
            failed_operations = []

            for contact_id in contact_ids:
                for tag_id in tag_ids:
                    try:
                        await api_client.apply_tag_to_contact(contact_id, tag_id)
                        success_count += 1
                    except Exception as e:
                        failed_operations.append(
                            {
                                "contact_id": contact_id,
                                "tag_id": tag_id,
                                "error": str(e),
                            }
                        )

            logger.info(
                f"Applied tags individually: {success_count} successful, {len(failed_operations)} failed"
            )
            return {
                "success": success_count > 0,
                "message": f"Completed {success_count} operations",
                "operations_completed": success_count,
                "failed_operations": failed_operations,
            }

    except Exception as e:
        logger.error(f"Error applying tags to contacts: {e}")
        raise


async def remove_tags_from_contacts(
    context, tag_ids: List[str], contact_ids: List[str]
) -> Dict[str, Any]:
    """Remove multiple tags from multiple contacts."""
    try:
        api_client: KeapApiService = context.api_client

        success_count = 0
        failed_operations = []

        for contact_id in contact_ids:
            for tag_id in tag_ids:
                try:
                    await api_client.remove_tag_from_contact(contact_id, tag_id)
                    success_count += 1
                except Exception as e:
                    failed_operations.append(
                        {"contact_id": contact_id, "tag_id": tag_id, "error": str(e)}
                    )

        logger.info(
            f"Removed tags: {success_count} successful, {len(failed_operations)} failed"
        )
        return {
            "success": success_count > 0,
            "message": f"Completed {success_count} operations",
            "operations_completed": success_count,
            "failed_operations": failed_operations,
        }

    except Exception as e:
        logger.error(f"Error removing tags from contacts: {e}")
        raise
