"""
Filter Utilities

Provides utility functions for filtering data with pattern matching,
including wildcard support, complex filters, and optimization.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def filter_by_name_pattern(items: List[Dict[str, Any]], pattern: str) -> List[Dict[str, Any]]:
    """Filter items by name pattern with wildcard support.
    
    Args:
        items: List of dictionaries with 'name' key
        pattern: Pattern to match (supports * wildcards)
        
    Returns:
        Filtered list of items matching the pattern
    """
    if items is None:
        return None
    if not pattern:
        return items
    
    # Convert wildcard pattern to regex
    regex_pattern = pattern.replace('*', '.*')
    regex_pattern = f'^{regex_pattern}$'
    
    try:
        compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)
    except re.error:
        logger.warning(f"Invalid pattern: {pattern}")
        return []
    
    filtered_items = []
    for item in items:
        if 'name' in item and compiled_pattern.match(item['name']):
            filtered_items.append(item)
    
    return filtered_items


def apply_complex_filters(
    contacts: List[Dict[str, Any]], 
    filters: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Apply complex filters to contact list.
    
    This function works with the email extraction that happens in tools_collections.py
    and applies the same filtering logic that _contact_matches_filters uses.
    
    Args:
        contacts: List of contact dictionaries
        filters: List of filter conditions
        
    Returns:
        Filtered contact list
    """
    from src.mcp.tools_collections import _contact_matches_filters, _extract_email
    
    if not filters:
        return contacts
    
    filtered_contacts = []
    for contact in contacts:
        # Ensure email extraction for consistency
        if 'email' not in contact or contact['email'] is None:
            contact['email'] = _extract_email(contact)
        
        if _contact_matches_filters(contact, filters):
            filtered_contacts.append(contact)
    
    return filtered_contacts


def validate_filter_conditions(filters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate filter conditions for correctness.
    
    Args:
        filters: List of filter conditions to validate
        
    Returns:
        Dict with validation results
    """
    if not filters:
        return {"valid": True, "errors": []}
    
    errors = []
    valid_operators = {
        "equals", "not_equals", "contains", "not_contains",
        "starts_with", "ends_with", "greater_than", "less_than",
        "between", "in", "not_in", "is_null", "is_not_null"
    }
    
    for i, filter_condition in enumerate(filters):
        if not isinstance(filter_condition, dict):
            errors.append(f"Filter {i}: Must be a dictionary")
            continue
        
        if "field" not in filter_condition and "field_id" not in filter_condition:
            errors.append(f"Filter {i}: Must have 'field' or 'field_id'")
        
        if "operator" not in filter_condition:
            errors.append(f"Filter {i}: Must have 'operator'")
        elif filter_condition["operator"] not in valid_operators:
            errors.append(f"Filter {i}: Invalid operator '{filter_condition['operator']}'")
        
        if "value" not in filter_condition and filter_condition.get("operator") not in ["is_null", "is_not_null"]:
            errors.append(f"Filter {i}: Must have 'value' for operator '{filter_condition.get('operator')}'")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def optimize_filters_for_api(filters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Optimize filters for API efficiency.
    
    Args:
        filters: List of filter conditions
        
    Returns:
        Dict with optimized filters and suggestions
    """
    if not filters:
        return {
            "server_side_filters": [],
            "client_side_filters": [],
            "optimization_notes": []
        }
    
    # Fields that can be optimized server-side in Keap API
    server_optimizable_fields = {
        "given_name", "family_name", "email", "company", "date_created", "last_updated"
    }
    
    server_side = []
    client_side = []
    notes = []
    
    for filter_condition in filters:
        field = filter_condition.get("field", "")
        
        # Custom fields and complex email filtering should be client-side
        if field.startswith("custom_fields.") or field == "email":
            client_side.append(filter_condition)
            if field == "email":
                notes.append("Email filtering uses client-side due to email_addresses array structure")
        elif field in server_optimizable_fields:
            server_side.append(filter_condition)
        else:
            client_side.append(filter_condition)
            notes.append(f"Field '{field}' requires client-side filtering")
    
    return {
        "server_side_filters": server_side,
        "client_side_filters": client_side,
        "optimization_notes": notes
    }


def evaluate_filter_condition(
    value: Any, 
    operator: str, 
    filter_value: Any
) -> bool:
    """Evaluate a single filter condition.
    
    Args:
        value: The actual value to test
        operator: The comparison operator
        filter_value: The value to compare against
        
    Returns:
        True if condition matches
    """
    if value is None:
        return operator in ["is_null", "not_equals"]
    
    if operator == "equals":
        return str(value).lower() == str(filter_value).lower()
    elif operator == "not_equals":
        return str(value).lower() != str(filter_value).lower()
    elif operator == "contains":
        return str(filter_value).lower() in str(value).lower()
    elif operator == "not_contains":
        return str(filter_value).lower() not in str(value).lower()
    elif operator == "starts_with":
        return str(value).lower().startswith(str(filter_value).lower())
    elif operator == "ends_with":
        return str(value).lower().endswith(str(filter_value).lower())
    elif operator == "is_null":
        return value is None
    elif operator == "is_not_null":
        return value is not None
    elif operator == "greater_than":
        try:
            return float(value) > float(filter_value)
        except (ValueError, TypeError):
            return False
    elif operator == "less_than":
        try:
            return float(value) < float(filter_value)
        except (ValueError, TypeError):
            return False
    elif operator == "between":
        try:
            if isinstance(filter_value, (list, tuple)) and len(filter_value) == 2:
                return float(filter_value[0]) <= float(value) <= float(filter_value[1])
            return False
        except (ValueError, TypeError):
            return False
    elif operator == "in":
        if isinstance(filter_value, (list, tuple)):
            return str(value).lower() in [str(v).lower() for v in filter_value]
        return False
    elif operator == "not_in":
        if isinstance(filter_value, (list, tuple)):
            return str(value).lower() not in [str(v).lower() for v in filter_value]
        return True
    
    return False


def evaluate_logical_group(
    item: Dict[str, Any], 
    conditions: List[Dict[str, Any]], 
    logic: str = "AND"
) -> bool:
    """Evaluate a logical group of conditions.
    
    Args:
        item: The item to test
        conditions: List of conditions to evaluate
        logic: Logic operator ("AND" or "OR")
        
    Returns:
        True if logical group matches
    """
    if not conditions:
        return True
    
    results = []
    for condition in conditions:
        field = condition.get("field", "")
        operator = condition.get("operator", "")
        value = condition.get("value", "")
        
        item_value = get_nested_value(item, field)
        result = evaluate_filter_condition(item_value, operator, value)
        results.append(result)
    
    if logic.upper() == "AND":
        return all(results)
    elif logic.upper() == "OR":
        return any(results)
    else:
        return False


def get_nested_value(item: Dict[str, Any], field_path: str) -> Any:
    """Get nested value from item using field path.
    
    Args:
        item: Dictionary to extract value from
        field_path: Dot-separated field path (e.g., "custom_fields.7")
        
    Returns:
        Value at the field path or None if not found
    """
    if not field_path:
        return None
    
    parts = field_path.split(".")
    current = item
    
    for part in parts:
        if isinstance(current, dict):
            if part == "custom_fields" and "custom_fields" in current:
                # Handle custom fields array structure
                current = current["custom_fields"]
            elif part.isdigit() and isinstance(current, list):
                # Handle array index or custom field ID
                field_id = int(part)
                if field_path.startswith("custom_fields."):
                    # Find custom field by ID
                    for cf in current:
                        if isinstance(cf, dict) and cf.get("id") == field_id:
                            return cf.get("content")
                    return None
                else:
                    # Regular array index
                    try:
                        current = current[field_id]
                    except IndexError:
                        return None
            else:
                current = current.get(part)
        else:
            return None
    
    return current


def parse_date_value(value: Any) -> Optional[datetime]:
    """Parse various date formats into datetime object.
    
    Args:
        value: Date value to parse (string, timestamp, or datetime)
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except (ValueError, OSError):
            return None
    
    if isinstance(value, str):
        # Try common date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    
    return None