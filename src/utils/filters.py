"""
Filter Processor

Provides advanced filtering capabilities for Keap MCP queries,
supporting complex logical operations, pattern matching, and more.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple, Callable

logger = logging.getLogger(__name__)

class FilterProcessor:
    """Processor for handling complex filter expressions"""
    
    # Operator mappings
    STRING_OPERATORS = {
        "=": "equals",
        "!=": "not_equals",
        "pattern": "pattern",
        "starts_with": "starts_with",
        "ends_with": "ends_with",
        "contains": "contains",
        "in": "in"
    }
    
    NUMERIC_OPERATORS = {
        "=": "equals",
        "!=": "not_equals",
        "<": "less_than",
        "<=": "less_than_equals",
        ">": "greater_than",
        ">=": "greater_than_equals",
        "in": "in",
        "between": "between"
    }
    
    DATE_OPERATORS = {
        "=": "equals",
        "!=": "not_equals",
        "<": "before",
        "<=": "before_on",
        ">": "after",
        ">=": "after_on",
        "between": "between",
        "before": "before",
        "after": "after",
        "on": "on"
    }
    
    # Field type mappings
    FIELD_TYPES = {
        "first_name": "string",
        "last_name": "string",
        "email": "string",
        "id": "numeric",
        "date_created": "date",
        "date_updated": "date",
        "tag": "tag",
        "tag_applied": "tag_date",
        "custom_field": "custom"
    }
    
    # Keap API field mappings
    KEAP_FIELD_MAPPINGS = {
        "first_name": "given_name",
        "last_name": "family_name",
        "email": "email_addresses.email",
        "id": "id",
        "date_created": "create_time",
        "date_updated": "update_time"
    }
    
    def __init__(self):
        """Initialize the filter processor"""
        # Store the applied filters for reporting
        self.applied_filters = []
        # Store the filter functions for client-side filtering
        self.filter_functions = []
        # Store tag expressions for post-processing
        self.tag_expressions = []
        # Store sort specifications
        self.sort_specs = []
    
    def process_filters(self, filters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a list of filters into API parameters
        
        Args:
            filters: List of filter conditions
            
        Returns:
            Dict of Keap API parameters
        """
        if not filters:
            return {}
            
        api_params = {}
        
        # First pass: process the filters to build API parameters
        # Handle the filters that can be directly mapped to API parameters
        for filter_item in filters:
            # Check if it's a logical group or field filter
            if 'operator' in filter_item and filter_item['operator'] in ['AND', 'OR', 'NOT']:
                self._process_logical_group(filter_item)
                continue
                
            # Process field filters
            field = filter_item.get('field')
            operator = filter_item.get('operator')
            value = filter_item.get('value')
            
            if not field or not operator:
                continue
            
            self._process_field_filter(field, operator, value, api_params)
        
        return api_params
    
    def _process_logical_group(self, group: Dict[str, Any]):
        """Process a logical group of filters
        
        Args:
            group: Logical group definition
        """
        operator = group.get('operator')
        conditions = group.get('conditions', [])
        
        if not conditions:
            return
            
        self.applied_filters.append(f"logical_{operator}")
        
        # Create filter functions for client-side filtering
        filter_funcs = []
        
        for condition in conditions:
            if 'operator' in condition and condition['operator'] in ['AND', 'OR', 'NOT']:
                # Nested logical group
                sub_processor = FilterProcessor()
                sub_processor._process_logical_group(condition)
                filter_funcs.extend(sub_processor.filter_functions)
                self.tag_expressions.extend(sub_processor.tag_expressions)
            else:
                # Field filter
                field = condition.get('field')
                operator = condition.get('operator')
                value = condition.get('value')
                
                if field and operator:
                    filter_func = self._create_filter_function(field, operator, value)
                    if filter_func:
                        filter_funcs.append(filter_func)
                    
                    # Special handling for tag expressions
                    if field == 'tag' and operator == 'expression':
                        self.tag_expressions.append(value)
        
        # Combine the filter functions based on the logical operator
        if filter_funcs:
            if operator == 'AND':
                def combined_func(contact):
                    return all(func(contact) for func in filter_funcs)
            elif operator == 'OR':
                def combined_func(contact):
                    return any(func(contact) for func in filter_funcs)
            elif operator == 'NOT':
                # NOT only applies to the first condition in the list
                if len(filter_funcs) > 0:
                    def combined_func(contact):
                        return not filter_funcs[0](contact)
                else:
                    def combined_func(contact):
                        return True
            else:
                def combined_func(contact):
                    return True
                
            self.filter_functions.append(combined_func)
    
    def _process_field_filter(self, field: str, operator: str, value: Any, api_params: Dict[str, Any]):
        """Process a field filter into API parameters and filter functions
        
        Args:
            field: Field name
            operator: Operator name
            value: Filter value
            api_params: API parameters to update
        """
        self.applied_filters.append(field)
        
        # Handle special fields
        if field == 'tag' and operator == 'expression':
            # Tag expressions are handled separately
            self.tag_expressions.append(value)
            return
        
        # Create filter function for client-side filtering
        filter_func = self._create_filter_function(field, operator, value)
        if filter_func:
            self.filter_functions.append(filter_func)
        
        # Map field and operator to Keap API parameters where possible
        if field in self.KEAP_FIELD_MAPPINGS:
            keap_field = self.KEAP_FIELD_MAPPINGS[field]
            field_type = self.FIELD_TYPES.get(field, "string")
            
            if field_type == "string":
                if operator == 'pattern':
                    # Convert pattern to closest available API parameter
                    if isinstance(value, str):
                        if value.startswith('*') and value.endswith('*'):
                            # Contains
                            api_params[keap_field] = value.strip('*')
                        elif value.startswith('*'):
                            # Ends with - not directly supported, use client-side filtering
                            pass
                        elif value.endswith('*'):
                            # Starts with
                            api_params[keap_field] = value.rstrip('*')
                        else:
                            # Exact match
                            api_params[keap_field] = value
                else:
                    # Direct mapping for exact match
                    api_params[keap_field] = value
            
            elif field_type == "numeric":
                if field == 'id' and operator == 'in' and isinstance(value, list):
                    # Special handling for ID lists
                    api_params['ids'] = ','.join(map(str, value))
                elif operator == '=':
                    # Exact match for ID
                    api_params['ids'] = str(value)
            
            elif field_type == "date":
                if field == 'date_created':
                    if operator == '>=':
                        api_params['since'] = value
                    elif operator == '<=':
                        api_params['until'] = value
                    elif operator == 'between' and isinstance(value, list) and len(value) >= 2:
                        api_params['since'] = value[0]
                        api_params['until'] = value[1]
                    elif operator == 'after':
                        api_params['since'] = value
                    elif operator == 'before':
                        api_params['until'] = value
    
    def _create_filter_function(self, field: str, operator: str, value: Any) -> Optional[Callable[[Dict[str, Any]], bool]]:
        """Create a filter function for client-side filtering
        
        Args:
            field: Field name
            operator: Operator name
            value: Filter value
            
        Returns:
            Filter function or None if not applicable
        """
        field_type = self.FIELD_TYPES.get(field, "string")
        
        if field_type == "string":
            return self._create_string_filter(field, operator, value)
        elif field_type == "numeric":
            return self._create_numeric_filter(field, operator, value)
        elif field_type == "date":
            return self._create_date_filter(field, operator, value)
        elif field_type == "tag":
            return self._create_tag_filter(field, operator, value)
        elif field_type == "tag_date":
            return self._create_tag_date_filter(field, operator, value)
        elif field_type == "custom":
            return self._create_custom_field_filter(field, operator, value)
        
        return None
    
    def _create_string_filter(self, field: str, operator: str, value: Any) -> Optional[Callable[[Dict[str, Any]], bool]]:
        """Create a string filter function
        
        Args:
            field: Field name
            operator: Operator name
            value: Filter value
            
        Returns:
            Filter function
        """
        keap_field = self.KEAP_FIELD_MAPPINGS.get(field)
        if not keap_field:
            return None
            
        if operator == '=':
            return lambda contact: self._get_field_value(contact, keap_field) == value
        elif operator == '!=':
            return lambda contact: self._get_field_value(contact, keap_field) != value
        elif operator == 'pattern':
            pattern = self._pattern_to_regex(value)
            return lambda contact: bool(pattern.match(str(self._get_field_value(contact, keap_field))))
        elif operator == 'starts_with':
            return lambda contact: str(self._get_field_value(contact, keap_field)).startswith(value)
        elif operator == 'ends_with':
            return lambda contact: str(self._get_field_value(contact, keap_field)).endswith(value)
        elif operator == 'contains':
            return lambda contact: value in str(self._get_field_value(contact, keap_field))
        elif operator == 'in' and isinstance(value, list):
            return lambda contact: self._get_field_value(contact, keap_field) in value
        
        return None
    
    def _create_numeric_filter(self, field: str, operator: str, value: Any) -> Optional[Callable[[Dict[str, Any]], bool]]:
        """Create a numeric filter function
        
        Args:
            field: Field name
            operator: Operator name
            value: Filter value
            
        Returns:
            Filter function
        """
        keap_field = self.KEAP_FIELD_MAPPINGS.get(field)
        if not keap_field:
            return None
            
        if operator == '=':
            return lambda contact: self._get_field_value(contact, keap_field) == value
        elif operator == '!=':
            return lambda contact: self._get_field_value(contact, keap_field) != value
        elif operator == '<':
            return lambda contact: self._get_field_value(contact, keap_field) < value
        elif operator == '<=':
            return lambda contact: self._get_field_value(contact, keap_field) <= value
        elif operator == '>':
            return lambda contact: self._get_field_value(contact, keap_field) > value
        elif operator == '>=':
            return lambda contact: self._get_field_value(contact, keap_field) >= value
        elif operator == 'in' and isinstance(value, list):
            return lambda contact: self._get_field_value(contact, keap_field) in value
        elif operator == 'between' and isinstance(value, list) and len(value) >= 2:
            return lambda contact: value[0] <= self._get_field_value(contact, keap_field) <= value[1]
        
        return None
    
    def _create_date_filter(self, field: str, operator: str, value: Any) -> Optional[Callable[[Dict[str, Any]], bool]]:
        """Create a date filter function
        
        Args:
            field: Field name
            operator: Operator name
            value: Filter value
            
        Returns:
            Filter function
        """
        keap_field = self.KEAP_FIELD_MAPPINGS.get(field)
        if not keap_field:
            return None
            
        if operator == '=':
            return lambda contact: self._parse_date(self._get_field_value(contact, keap_field)) == self._parse_date(value)
        elif operator == '!=':
            return lambda contact: self._parse_date(self._get_field_value(contact, keap_field)) != self._parse_date(value)
        elif operator == '<' or operator == 'before':
            return lambda contact: self._parse_date(self._get_field_value(contact, keap_field)) < self._parse_date(value)
        elif operator == '<=' or operator == 'before_on':
            return lambda contact: self._parse_date(self._get_field_value(contact, keap_field)) <= self._parse_date(value)
        elif operator == '>' or operator == 'after':
            return lambda contact: self._parse_date(self._get_field_value(contact, keap_field)) > self._parse_date(value)
        elif operator == '>=' or operator == 'after_on':
            return lambda contact: self._parse_date(self._get_field_value(contact, keap_field)) >= self._parse_date(value)
        elif operator == 'between' and isinstance(value, list) and len(value) >= 2:
            return lambda contact: self._parse_date(value[0]) <= self._parse_date(self._get_field_value(contact, keap_field)) <= self._parse_date(value[1])
        elif operator == 'on':
            return lambda contact: self._parse_date(self._get_field_value(contact, keap_field)).date() == self._parse_date(value).date()
        
        return None
    
    def _create_tag_filter(self, field: str, operator: str, value: Any) -> Optional[Callable[[Dict[str, Any]], bool]]:
        """Create a tag filter function
        
        Args:
            field: Field name
            operator: Operator name
            value: Filter value
            
        Returns:
            Filter function
        """
        if field == 'tag':
            if operator == '=':
                # Single tag ID match
                return lambda contact: value in self._get_tag_ids(contact)
            elif operator == 'in' and isinstance(value, list):
                # Multiple tag IDs match (any)
                return lambda contact: any(tag_id in self._get_tag_ids(contact) for tag_id in value)
        
        return None
    
    def _create_tag_date_filter(self, field: str, operator: str, value: Any) -> Optional[Callable[[Dict[str, Any]], bool]]:
        """Create a tag application date filter function
        
        Args:
            field: Field name
            operator: Operator name
            value: Filter value
            
        Returns:
            Filter function
        """
        if field == 'tag_applied' and 'tag_id' in value:
            tag_id = value.get('tag_id')
            date_value = value.get('value')
            
            if operator == 'before':
                return lambda contact: self._check_tag_date(contact, tag_id, lambda d: d < self._parse_date(date_value))
            elif operator == 'after':
                return lambda contact: self._check_tag_date(contact, tag_id, lambda d: d > self._parse_date(date_value))
            elif operator == 'on':
                return lambda contact: self._check_tag_date(contact, tag_id, lambda d: d.date() == self._parse_date(date_value).date())
            elif operator == 'between' and isinstance(date_value, list) and len(date_value) >= 2:
                return lambda contact: self._check_tag_date(
                    contact, 
                    tag_id, 
                    lambda d: self._parse_date(date_value[0]) <= d <= self._parse_date(date_value[1])
                )
        
        return None
    
    def _create_custom_field_filter(self, field: str, operator: str, value: Any) -> Optional[Callable[[Dict[str, Any]], bool]]:
        """Create a custom field filter function
        
        Args:
            field: Field name
            operator: Operator name
            value: Filter value
            
        Returns:
            Filter function
        """
        if field == 'custom_field' and 'id' in value:
            field_id = value.get('id')
            field_value = value.get('value')
            field_operator = value.get('operator', '=')
            
            return lambda contact: self._check_custom_field(contact, field_id, field_operator, field_value)
        
        return None
    
    def process_sort(self, sort_specs: Optional[List[Dict[str, str]]]) -> List[Tuple[str, bool]]:
        """Process sort specifications
        
        Args:
            sort_specs: List of sort specifications
            
        Returns:
            List of (field_name, descending) tuples
        """
        if not sort_specs:
            return []
            
        result = []
        
        for spec in sort_specs:
            field = spec.get('field')
            direction = spec.get('direction', 'asc')
            
            if field in self.KEAP_FIELD_MAPPINGS:
                keap_field = self.KEAP_FIELD_MAPPINGS[field]
                descending = direction.lower() == 'desc'
                result.append((keap_field, descending))
        
        return result
    
    def apply_filters(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply client-side filters to contacts
        
        Args:
            contacts: List of contacts
            
        Returns:
            Filtered list of contacts
        """
        if not self.filter_functions and not self.tag_expressions:
            return contacts
        
        filtered_contacts = []
        
        for contact in contacts:
            # Apply regular filters
            if all(filter_func(contact) for filter_func in self.filter_functions):
                # Apply tag expression filters if any
                if not self.tag_expressions or self._evaluate_tag_expressions(contact):
                    filtered_contacts.append(contact)
        
        return filtered_contacts
    
    def apply_sort(self, contacts: List[Dict[str, Any]], sort_specs: List[Tuple[str, bool]]) -> List[Dict[str, Any]]:
        """Apply sorting to contacts
        
        Args:
            contacts: List of contacts
            sort_specs: List of (field_name, descending) tuples
            
        Returns:
            Sorted list of contacts
        """
        if not sort_specs:
            return contacts
        
        # Copy the list to avoid modifying the original
        result = list(contacts)
        
        # Sort in reverse order (last sort spec has highest precedence)
        for field, descending in reversed(sort_specs):
            result.sort(
                key=lambda contact: self._get_sort_key(contact, field),
                reverse=descending
            )
        
        return result
    
    def _get_sort_key(self, contact: Dict[str, Any], field: str) -> Any:
        """Get a sort key from a contact
        
        Args:
            contact: Contact dictionary
            field: Field name
            
        Returns:
            Sort key value
        """
        value = self._get_field_value(contact, field)
        
        # For dates, convert to datetime for comparison
        if field in ['create_time', 'update_time'] and isinstance(value, str):
            try:
                return self._parse_date(value)
            except (ValueError, TypeError):
                return value
        
        # For names, convert to lowercase for case-insensitive sorting
        if field in ['given_name', 'family_name'] and isinstance(value, str):
            return value.lower()
        
        return value
    
    def _evaluate_tag_expressions(self, contact: Dict[str, Any]) -> bool:
        """Evaluate tag expressions for a contact
        
        Args:
            contact: Contact dictionary
            
        Returns:
            True if all tag expressions match, False otherwise
        """
        if not self.tag_expressions:
            return True
            
        tag_ids = self._get_tag_ids(contact)
        
        for expression in self.tag_expressions:
            if not self._evaluate_tag_expression(expression, tag_ids):
                return False
        
        return True
    
    def _evaluate_tag_expression(self, expression: Dict[str, Any], tag_ids: Set[int]) -> bool:
        """Evaluate a single tag expression
        
        Args:
            expression: Tag expression object
            tag_ids: Set of tag IDs
            
        Returns:
            True if the expression matches, False otherwise
        """
        # Simple tag ID check
        if 'tag_id' in expression:
            return expression['tag_id'] in tag_ids
            
        # Logical operator
        if 'operator' in expression and 'conditions' in expression:
            operator = expression['operator']
            conditions = expression['conditions']
            
            if operator == 'AND':
                return all(self._evaluate_tag_expression(cond, tag_ids) for cond in conditions)
            elif operator == 'OR':
                return any(self._evaluate_tag_expression(cond, tag_ids) for cond in conditions)
            elif operator == 'NOT':
                # NOT applies to the first condition only
                if conditions:
                    return not self._evaluate_tag_expression(conditions[0], tag_ids)
        
        return False
    
    def _get_field_value(self, obj: Dict[str, Any], field_path: str) -> Any:
        """Get a value from an object using a dot-notation path
        
        Args:
            obj: Object to get value from
            field_path: Field path with dot notation
            
        Returns:
            Field value
        """
        if '.' not in field_path:
            return obj.get(field_path)
            
        parts = field_path.split('.')
        current = obj
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                # Handle lists (e.g., email_addresses)
                results = []
                for item in current:
                    if isinstance(item, dict) and part in item:
                        results.append(item[part])
                return results if results else None
            else:
                return None
            
            if current is None:
                return None
                
        return current
    
    def _get_tag_ids(self, contact: Dict[str, Any]) -> Set[int]:
        """Get tag IDs from a contact
        
        Args:
            contact: Contact dictionary
            
        Returns:
            Set of tag IDs
        """
        tag_ids = set()
        
        # Check for tag_ids field
        if 'tag_ids' in contact and isinstance(contact['tag_ids'], list):
            for tag_id in contact['tag_ids']:
                try:
                    tag_ids.add(int(tag_id))
                except (ValueError, TypeError):
                    pass
        
        # Check for tags field
        if 'tags' in contact and isinstance(contact['tags'], list):
            for tag in contact['tags']:
                if isinstance(tag, dict) and 'id' in tag:
                    try:
                        tag_ids.add(int(tag['id']))
                    except (ValueError, TypeError):
                        pass
        
        return tag_ids
    
    def _check_tag_date(self, contact: Dict[str, Any], tag_id: int, date_check: Callable[[datetime], bool]) -> bool:
        """Check if a tag was applied on a specific date
        
        Args:
            contact: Contact dictionary
            tag_id: Tag ID
            date_check: Function to check the date
            
        Returns:
            True if the tag was applied on the specified date, False otherwise
        """
        if 'tags' in contact and isinstance(contact['tags'], list):
            for tag in contact['tags']:
                if (isinstance(tag, dict) and 
                    'id' in tag and 
                    tag['id'] == tag_id and 
                    'date_applied' in tag):
                    try:
                        tag_date = self._parse_date(tag['date_applied'])
                        return date_check(tag_date)
                    except (ValueError, TypeError):
                        pass
        
        return False
    
    def _check_custom_field(self, contact: Dict[str, Any], field_id: int, operator: str, value: Any) -> bool:
        """Check a custom field value
        
        Args:
            contact: Contact dictionary
            field_id: Custom field ID
            operator: Operator to use
            value: Value to compare
            
        Returns:
            True if the field matches, False otherwise
        """
        if 'custom_fields' not in contact:
            return False
            
        custom_fields = contact['custom_fields']
        if not isinstance(custom_fields, dict):
            return False
            
        # Find the field by ID
        field_key = str(field_id)
        if field_key not in custom_fields:
            return False
            
        field = custom_fields[field_key]
        if not isinstance(field, dict) or 'value' not in field:
            return False
            
        field_value = field['value']
        
        # Apply the operator
        if operator == '=':
            return field_value == value
        elif operator == '!=':
            return field_value != value
        elif operator == '<':
            return field_value < value
        elif operator == '<=':
            return field_value <= value
        elif operator == '>':
            return field_value > value
        elif operator == '>=':
            return field_value >= value
        elif operator == 'pattern' and isinstance(field_value, str):
            pattern = self._pattern_to_regex(value)
            return bool(pattern.match(field_value))
        elif operator == 'in' and isinstance(value, list):
            return field_value in value
        elif operator == 'between' and isinstance(value, list) and len(value) >= 2:
            return value[0] <= field_value <= value[1]
        
        return False
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse a date string to a datetime object
        
        Args:
            date_str: Date string
            
        Returns:
            Datetime object
        """
        if not date_str:
            return datetime.min
            
        if isinstance(date_str, datetime):
            return date_str
            
        try:
            # Handle ISO format with Z
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
                
            return datetime.fromisoformat(date_str)
        except ValueError:
            # Fallback for other formats
            try:
                import dateutil.parser
                return dateutil.parser.parse(date_str)
            except (ImportError, ValueError, TypeError):
                return datetime.min
    
    def _pattern_to_regex(self, pattern: str) -> re.Pattern:
        """Convert a wildcard pattern to a regex pattern
        
        Args:
            pattern: Wildcard pattern
            
        Returns:
            Compiled regex pattern
        """
        if not pattern:
            return re.compile('.*')
            
        # Escape regex special characters except * which we'll convert
        escaped = re.escape(pattern).replace('\\*', '.*')
        
        # Add start and end anchors
        regex_pattern = f"^{escaped}$"
        
        return re.compile(regex_pattern, re.IGNORECASE)
