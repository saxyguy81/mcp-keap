"""
Filter Utilities

Provides utility functions for filtering data with pattern matching.
"""

import re
from typing import Dict, List, Any

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
