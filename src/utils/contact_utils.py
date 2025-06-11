"""
Contact Utilities

Provides utility functions for working with Keap contact data.
"""

import logging
from typing import Dict, List, Any, Union

logger = logging.getLogger(__name__)


def get_primary_email(contact: Dict[str, Any]) -> str:
    """Get the primary email address from a contact

    Args:
        contact: Contact data from Keap API

    Returns:
        Primary email address or empty string
    """
    if not contact or "email_addresses" not in contact:
        return ""

    email_addresses = contact.get("email_addresses", [])

    # Try to find the primary email first
    for email in email_addresses:
        if email.get("field") == "EMAIL" and email.get("is_primary", False):
            return email.get("email", "")

    # Fall back to the first email address
    for email in email_addresses:
        if email.get("field") == "EMAIL":
            return email.get("email", "")

    return ""


def get_full_name(contact: Dict[str, Any]) -> str:
    """Get the full name from a contact

    Args:
        contact: Contact data from Keap API

    Returns:
        Full name as a string
    """
    if not contact:
        return ""

    first_name = contact.get("given_name", "")
    last_name = contact.get("family_name", "")

    return f"{first_name} {last_name}".strip()


def get_tag_ids(contact: Dict[str, Any]) -> List[int]:
    """Get tag IDs from a contact

    Args:
        contact: Contact data from Keap API

    Returns:
        List of tag IDs
    """
    if not contact:
        return []

    # Try to get from tag_ids field
    tag_ids = []
    if "tag_ids" in contact and isinstance(contact["tag_ids"], list):
        for tag_id in contact["tag_ids"]:
            try:
                tag_ids.append(int(tag_id))
            except (ValueError, TypeError):
                pass

    # Also check the tags list if available
    if "tags" in contact and isinstance(contact["tags"], list):
        for tag in contact["tags"]:
            if isinstance(tag, dict) and "id" in tag:
                try:
                    tag_id = int(tag["id"])
                    if tag_id not in tag_ids:
                        tag_ids.append(tag_id)
                except (ValueError, TypeError):
                    pass

    return tag_ids


def get_custom_field_value(contact: Dict[str, Any], field_id: Union[int, str]) -> Any:
    """Get a custom field value from a contact

    Args:
        contact: Contact data from Keap API
        field_id: Custom field ID

    Returns:
        Custom field value or None if not found
    """
    if not contact or "custom_fields" not in contact:
        return None

    custom_fields = contact.get("custom_fields", [])
    field_id_str = str(field_id)

    # Check list format (newer Keap API)
    if isinstance(custom_fields, list):
        for field in custom_fields:
            if isinstance(field, dict) and str(field.get("id")) == field_id_str:
                return field.get("content")

    # Check dict format (older Keap API)
    elif isinstance(custom_fields, dict) and field_id_str in custom_fields:
        field = custom_fields[field_id_str]
        if isinstance(field, dict):
            return field.get("value")

    return None


def format_contact_summary(contact: Dict[str, Any]) -> Dict[str, Any]:
    """Format a contact summary with key information

    Args:
        contact: Contact data from Keap API

    Returns:
        Formatted contact summary
    """
    if not contact:
        return {}

    return {
        "id": contact.get("id"),
        "first_name": contact.get("given_name", ""),
        "last_name": contact.get("family_name", ""),
        "email": get_primary_email(contact),
        "created": contact.get("create_time"),
        "updated": contact.get("update_time"),
        "tag_count": len(get_tag_ids(contact)),
    }


def format_contact_data(contact: Dict[str, Any]) -> Dict[str, Any]:
    """Format contact data for consistent output

    Args:
        contact: Raw contact data from Keap API

    Returns:
        Formatted contact data
    """
    if not contact:
        return {}

    return {
        "id": contact.get("id"),
        "given_name": contact.get("given_name", ""),
        "family_name": contact.get("family_name", ""),
        "full_name": get_full_name(contact),
        "email": get_primary_email(contact),
        "email_addresses": contact.get("email_addresses", []),
        "phone_numbers": contact.get("phone_numbers", []),
        "addresses": contact.get("addresses", []),
        "custom_fields": contact.get("custom_fields", []),
        "tag_ids": get_tag_ids(contact),
        "date_created": contact.get("date_created"),
        "last_updated": contact.get("last_updated"),
    }


def process_contact_include_fields(
    contact: Dict[str, Any], include_fields: List[str] = None
) -> Dict[str, Any]:
    """Process contact to include only specified fields

    Args:
        contact: Contact data
        include_fields: List of fields to include (if None, include all)

    Returns:
        Filtered contact data
    """
    if not contact:
        return {}

    if not include_fields:
        return format_contact_data(contact)

    formatted = format_contact_data(contact)
    return {
        field: formatted.get(field) for field in include_fields if field in formatted
    }
