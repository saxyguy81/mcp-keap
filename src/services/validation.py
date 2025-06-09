"""
Validation Services

Simplified validation services for request validation.
"""

from typing import Dict, Any
from src.schemas.validator import SchemaValidator

class RequestValidationService:
    """Simplified request validation service"""
    
    def __init__(self):
        self.validator = SchemaValidator()
    
    def validate_contact_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate contact query parameters"""
        try:
            if 'filters' in query_params:
                return self.validator.validate_filter_expression(query_params['filters'])
            return True
        except Exception:
            return False
    
    def validate_tag_query(self, query_params: Dict[str, Any]) -> bool:
        """Validate tag query parameters"""
        try:
            if 'filters' in query_params:
                return self.validator.validate_filter_expression(query_params['filters'])
            return True
        except Exception:
            return False
    
    def validate_contact_data(self, contact_data: Dict[str, Any]) -> bool:
        """Validate contact data"""
        return self.validator.validate_contact_data(contact_data)
    
    def validate_tag_data(self, tag_data: Dict[str, Any]) -> bool:
        """Validate tag data"""
        return self.validator.validate_tag_data(tag_data)

__all__ = ['RequestValidationService']