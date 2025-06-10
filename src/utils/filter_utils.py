"""
Filter Utilities

Provides comprehensive utility functions for filtering data with pattern matching,
logical operations, and complex filter evaluation.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def filter_by_name_pattern(items: List[Dict[str, Any]], pattern: str) -> List[Dict[str, Any]]:
    """Filter items by name pattern with wildcard support
    
    Args:
        items: List of items with 'name' key
        pattern: Pattern string with optional wildcards (*)
        
    Returns:
        Filtered list of items
    """
    if not pattern or not items:
        return items
        
    # Convert wildcard pattern to regex
    regex_pattern = pattern.replace('*', '.*')
    regex_pattern = f"^{regex_pattern}$"
    
    regex = re.compile(regex_pattern, re.IGNORECASE)
    
    return [item for item in items if 'name' in item and regex.match(item['name'])]


def validate_filter_conditions(filters: List[Dict[str, Any]]) -> None:
    """Validate filter conditions for proper structure and values.
    
    Args:
        filters: List of filter condition dictionaries
        
    Raises:
        ValueError: If any filter condition is invalid
    """
    if not filters:
        return
    
    for i, filter_condition in enumerate(filters):
        if not isinstance(filter_condition, dict):
            raise ValueError(f"Filter {i} must be a dictionary")
        
        # Check if this is a logical group
        if 'operator' in filter_condition and 'conditions' in filter_condition:
            # Validate logical group
            operator = filter_condition['operator']
            if operator not in ['AND', 'OR', 'NOT']:
                raise ValueError(f"Filter {i} has invalid logical operator '{operator}'")
            
            conditions = filter_condition.get('conditions', [])
            if not conditions:
                raise ValueError(f"Filter {i} logical group must have conditions")
            
            # Recursively validate nested conditions
            validate_filter_conditions(conditions)
            continue
        
        # Check for required fields in regular filter conditions
        if 'field' not in filter_condition:
            raise ValueError(f"Filter {i} missing required 'field' property")
        
        if 'operator' not in filter_condition:
            raise ValueError(f"Filter {i} missing required 'operator' property")
        
        if 'value' not in filter_condition and filter_condition.get('operator') not in ['IS_NULL', 'IS_NOT_NULL']:
            raise ValueError(f"Filter {i} missing required 'value' property")
        
        # Validate field name
        field = filter_condition['field']
        if not isinstance(field, str) or not field.strip():
            raise ValueError(f"Filter {i} 'field' must be a non-empty string")
        
        # Validate operator
        operator = filter_condition['operator']
        valid_operators = [
            'EQUALS', 'NOT_EQUALS', 'CONTAINS', 'NOT_CONTAINS',
            'STARTS_WITH', 'ENDS_WITH', 'GREATER_THAN', 'LESS_THAN',
            'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL',
            'BETWEEN', 'IN', 'NOT_IN', 'SINCE', 'UNTIL',
            'equals', 'contains', 'starts_with', 'ends_with',  # lowercase variants
            # Shorthand operators
            '=', '!=', '>', '<', '>=', '<=', 'like', 'not_like'
        ]
        
        if operator not in valid_operators:
            raise ValueError(f"Filter {i} has invalid operator '{operator}'. Valid operators: {valid_operators}")
        
        # Validate value for specific operators
        value = filter_condition.get('value')
        if operator in ['IN', 'NOT_IN'] and not isinstance(value, list):
            raise ValueError(f"Filter {i} with operator '{operator}' requires a list value")
        
        if operator == 'BETWEEN' and (not isinstance(value, list) or len(value) != 2):
            raise ValueError(f"Filter {i} with operator 'BETWEEN' requires a list of exactly 2 values")


def evaluate_filter_condition(item: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    """Evaluate a single filter condition against an item.
    
    Args:
        item: The item to test
        condition: Filter condition dictionary with field, operator, value
        
    Returns:
        True if item matches the condition, False otherwise
    """
    try:
        field = condition['field']
        operator = condition['operator'].upper()
        filter_value = condition.get('value')
        
        # Get item value - support nested fields with dot notation
        item_value = get_nested_value(item, field)
        
        # Handle null/missing values
        if item_value is None:
            return operator in ['IS_NULL', 'NOT_EQUALS'] or (operator == 'EQUALS' and filter_value is None)
        
        # Convert to string for text operations
        item_str = str(item_value).lower() if item_value is not None else ""
        filter_str = str(filter_value).lower() if filter_value is not None else ""
        
        # Evaluate based on operator (normalize shorthand operators)
        if operator in ['EQUALS', 'EQUAL', '=']:
            return str(item_value) == str(filter_value)
        
        elif operator in ['NOT_EQUALS', 'NOT_EQUAL', '!=']:
            return str(item_value) != str(filter_value)
        
        elif operator == 'CONTAINS':
            return filter_str in item_str
        
        elif operator == 'NOT_CONTAINS':
            return filter_str not in item_str
        
        elif operator == 'STARTS_WITH':
            return item_str.startswith(filter_str)
        
        elif operator == 'ENDS_WITH':
            return item_str.endswith(filter_str)
        
        elif operator in ['GREATER_THAN', 'GT', '>']:
            return float(item_value) > float(filter_value)
        
        elif operator in ['LESS_THAN', 'LT', '<']:
            return float(item_value) < float(filter_value)
        
        elif operator in ['GREATER_THAN_OR_EQUAL', 'GTE', '>=']:
            return float(item_value) >= float(filter_value)
        
        elif operator in ['LESS_THAN_OR_EQUAL', 'LTE', '<=']:
            return float(item_value) <= float(filter_value)
        
        elif operator == 'BETWEEN':
            if isinstance(filter_value, list) and len(filter_value) == 2:
                return float(filter_value[0]) <= float(item_value) <= float(filter_value[1])
            return False
        
        elif operator == 'IN':
            if isinstance(filter_value, list):
                return str(item_value) in [str(v) for v in filter_value]
            return str(item_value) == str(filter_value)
        
        elif operator == 'NOT_IN':
            if isinstance(filter_value, list):
                return str(item_value) not in [str(v) for v in filter_value]
            return str(item_value) != str(filter_value)
        
        elif operator == 'SINCE':
            return parse_date_value(item_value) >= parse_date_value(filter_value)
        
        elif operator == 'UNTIL':
            return parse_date_value(item_value) <= parse_date_value(filter_value)
        
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
            
    except (ValueError, TypeError) as e:
        logger.warning(f"Error evaluating filter condition: {e}")
        return False


def evaluate_logical_group(item: Dict[str, Any], group: Dict[str, Any]) -> bool:
    """Evaluate a logical group of filter conditions.
    
    Args:
        item: The item to test
        group: Logical group with operator and conditions
        
    Returns:
        True if item matches the group logic, False otherwise
    """
    operator = group.get('operator', 'AND').upper()
    conditions = group.get('conditions', [])
    
    if not conditions:
        return True
    
    results = []
    for condition in conditions:
        if 'operator' in condition and 'conditions' in condition:
            # Nested logical group
            result = evaluate_logical_group(item, condition)
        else:
            # Regular filter condition
            result = evaluate_filter_condition(item, condition)
        results.append(result)
    
    if operator == 'AND':
        return all(results)
    elif operator == 'OR':
        return any(results)
    elif operator == 'NOT':
        # NOT operator applies to the first condition only
        return not results[0] if results else True
    else:
        logger.warning(f"Unknown logical operator: {operator}")
        return False


def apply_complex_filters(items: List[Dict[str, Any]], filters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply complex filters to a list of items.
    
    Args:
        items: List of items to filter
        filters: List of filter conditions and logical groups
        
    Returns:
        Filtered list of items
    """
    if not filters or not items:
        return items
    
    filtered_items = []
    
    for item in items:
        item_matches = True
        
        for filter_def in filters:
            if 'operator' in filter_def and 'conditions' in filter_def:
                # Logical group
                if not evaluate_logical_group(item, filter_def):
                    item_matches = False
                    break
            else:
                # Simple filter condition
                if not evaluate_filter_condition(item, filter_def):
                    item_matches = False
                    break
        
        if item_matches:
            filtered_items.append(item)
    
    return filtered_items


def get_nested_value(item: Dict[str, Any], field_path: str) -> Any:
    """Get value from nested dictionary using dot notation.
    
    Args:
        item: Dictionary to search
        field_path: Field path like 'user.profile.name'
        
    Returns:
        The value if found, None otherwise
    """
    try:
        current = item
        for field in field_path.split('.'):
            if isinstance(current, dict) and field in current:
                current = current[field]
            elif isinstance(current, list) and field.isdigit():
                index = int(field)
                current = current[index] if 0 <= index < len(current) else None
            else:
                return None
        return current
    except (KeyError, IndexError, TypeError):
        return None


def parse_date_value(value: Any) -> datetime:
    """Parse various date formats into datetime object.
    
    Args:
        value: Date value (string, datetime, or timestamp)
        
    Returns:
        Parsed datetime object
    """
    if value is None:
        raise ValueError(f"Cannot parse date value: {value}")
        
    if isinstance(value, datetime):
        return value
    
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    
    if isinstance(value, str):
        # Try common date formats including ISO formats
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',  # ISO with Z
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        
        # Try parsing ISO format with dateutil if available
        try:
            from dateutil.parser import parse as dateutil_parse
            return dateutil_parse(value)
        except ImportError:
            pass
        except Exception:
            pass
        
        # Try relative dates
        if value.lower() == 'today':
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif value.lower() == 'yesterday':
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    
    raise ValueError(f"Cannot parse date value: {value}")


def optimize_filters_for_api(filters: List[Dict[str, Any]]) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Optimize filters by separating server-side and client-side filters.
    
    Args:
        filters: List of filter conditions
        
    Returns:
        Tuple of (server_side_params, client_side_filters)
    """
    server_params = {}
    client_filters = []
    
    # Fields that can be handled server-side by Keap API
    server_side_fields = {
        'email': 'email',
        'given_name': 'given_name', 
        'family_name': 'family_name',
        'id': 'id',
        'date_created': 'date_created'
    }
    
    for filter_condition in filters:
        if 'operator' in filter_condition and 'conditions' in filter_condition:
            # Complex logical groups must be handled client-side
            client_filters.append(filter_condition)
            continue
        
        field = filter_condition.get('field')
        operator = filter_condition.get('operator', '')
        value = filter_condition.get('value')
        
        # Normalize operator to check against valid server-side operators
        normalized_operator = operator.upper() if isinstance(operator, str) else operator
        if operator == '=':
            normalized_operator = 'EQUALS'
        elif operator == 'contains' or operator == 'CONTAINS':
            normalized_operator = 'CONTAINS'
        
        # Check if this can be optimized for server-side
        if field in server_side_fields and normalized_operator in ['EQUALS', 'CONTAINS']:
            api_field = server_side_fields[field]
            
            if normalized_operator == 'EQUALS':
                server_params[api_field] = value
            elif normalized_operator == 'CONTAINS' and field == 'email':
                server_params[api_field] = f"*{value}*"
            else:
                client_filters.append(filter_condition)
        else:
            # Must be handled client-side
            client_filters.append(filter_condition)
    
    return server_params, client_filters
