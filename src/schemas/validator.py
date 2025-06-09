"""
Schema Validator

Minimal schema validation for Keap MCP Server.
Provides basic validation for contact and tag data.
"""

import logging
from typing import Dict, List, Any, Union

logger = logging.getLogger(__name__)


class SchemaValidator:
    """
    Simple schema validator for MCP requests and responses
    """
    
    @staticmethod
    def validate_contact_data(contact_data: Dict[str, Any]) -> bool:
        """
        Validate basic contact data structure
        
        Args:
            contact_data: Contact data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(contact_data, dict):
                return False
                
            # Basic required fields check
            if 'id' in contact_data:
                if not isinstance(contact_data['id'], (int, str)):
                    return False
                    
            # Validate email structure if present
            if 'email_addresses' in contact_data:
                emails = contact_data['email_addresses']
                if not isinstance(emails, list):
                    return False
                for email in emails:
                    if not isinstance(email, dict) or 'email' not in email:
                        return False
                        
            return True
            
        except Exception as e:
            logger.warning(f"Contact validation error: {e}")
            return False
    
    @staticmethod
    def validate_tag_data(tag_data: Dict[str, Any]) -> bool:
        """
        Validate basic tag data structure
        
        Args:
            tag_data: Tag data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(tag_data, dict):
                return False
                
            # Basic required fields check
            if 'id' not in tag_data:
                return False
                
            if not isinstance(tag_data['id'], (int, str)):
                return False
                
            if 'name' in tag_data and not isinstance(tag_data['name'], str):
                return False
                
            return True
            
        except Exception as e:
            logger.warning(f"Tag validation error: {e}")
            return False
    
    @staticmethod
    def validate_filter_expression(filter_expr: Union[Dict, List]) -> bool:
        """
        Validate filter expression structure
        
        Args:
            filter_expr: Filter expression
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if isinstance(filter_expr, list):
                return all(SchemaValidator.validate_filter_condition(f) for f in filter_expr)
            elif isinstance(filter_expr, dict):
                return SchemaValidator.validate_filter_condition(filter_expr)
            return False
            
        except Exception as e:
            logger.warning(f"Filter validation error: {e}")
            return False
    
    @staticmethod
    def validate_filter_condition(condition: Dict[str, Any]) -> bool:
        """
        Validate individual filter condition
        
        Args:
            condition: Filter condition dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(condition, dict):
                return False
                
            # Check for required fields
            if 'field' in condition:
                if not isinstance(condition['field'], str):
                    return False
                if 'operator' not in condition:
                    return False
                if 'value' not in condition:
                    return False
                    
            # Check for group conditions
            elif 'type' in condition and condition['type'] == 'group':
                if 'operator' not in condition or 'filters' not in condition:
                    return False
                if not isinstance(condition['filters'], list):
                    return False
                    
            return True
            
        except Exception as e:
            logger.warning(f"Filter condition validation error: {e}")
            return False
    
    @staticmethod
    def sanitize_contact_response(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sanitize contact response data
        
        Args:
            contacts: List of contact dictionaries
            
        Returns:
            Sanitized contact list
        """
        sanitized = []
        for contact in contacts:
            if SchemaValidator.validate_contact_data(contact):
                sanitized.append(contact)
            else:
                logger.warning(f"Skipping invalid contact: {contact.get('id', 'unknown')}")
        return sanitized
    
    @staticmethod
    def sanitize_tag_response(tags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sanitize tag response data
        
        Args:
            tags: List of tag dictionaries
            
        Returns:
            Sanitized tag list
        """
        sanitized = []
        for tag in tags:
            if SchemaValidator.validate_tag_data(tag):
                sanitized.append(tag)
            else:
                logger.warning(f"Skipping invalid tag: {tag.get('id', 'unknown')}")
        return sanitized