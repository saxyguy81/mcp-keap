"""
Schema Validation

Provides validation for MCP request and response schemas.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Validates request and response schemas for MCP tools"""
    
    @staticmethod
    def validate_query_contacts_request(params: Dict[str, Any]) -> bool:
        """Validate query_contacts request parameters
        
        Args:
            params: Request parameters
            
        Returns:
            True if valid, False otherwise
        """
        # Check required field
        if 'filters' not in params:
            logger.error("Missing required field 'filters' in query_contacts request")
            return False
            
        filters = params.get('filters', [])
        if not isinstance(filters, list):
            logger.error("'filters' must be a list in query_contacts request")
            return False
            
        # Validate filters
        for filter_item in filters:
            if not isinstance(filter_item, dict):
                logger.error("Each filter item must be an object")
                return False
                
            # Check if it's a logical group
            if 'operator' in filter_item and filter_item['operator'] in ['AND', 'OR', 'NOT']:
                if 'conditions' not in filter_item or not isinstance(filter_item['conditions'], list):
                    logger.error("Logical group must have 'conditions' as list")
                    return False
            # Or a field filter
            elif 'field' in filter_item and 'operator' in filter_item:
                if 'value' not in filter_item:
                    logger.error(f"Filter for field '{filter_item['field']}' missing 'value'")
                    return False
            else:
                logger.error(f"Invalid filter format: {filter_item}")
                return False
                
        # Validate sort
        sort = params.get('sort')
        if sort is not None:
            if not isinstance(sort, list):
                logger.error("'sort' must be a list in query_contacts request")
                return False
                
            for sort_item in sort:
                if not isinstance(sort_item, dict):
                    logger.error("Each sort item must be an object")
                    return False
                    
                if 'field' not in sort_item:
                    logger.error("Sort item missing 'field'")
                    return False
                    
                direction = sort_item.get('direction', 'asc')
                if direction not in ['asc', 'desc']:
                    logger.error(f"Invalid sort direction: {direction}")
                    return False
        
        # Validate max_results
        max_results = params.get('max_results')
        if max_results is not None:
            if not isinstance(max_results, int) or max_results <= 0:
                logger.error("'max_results' must be a positive integer")
                return False
        
        return True
    
    @staticmethod
    def validate_get_contact_details_request(params: Dict[str, Any]) -> bool:
        """Validate get_contact_details request parameters
        
        Args:
            params: Request parameters
            
        Returns:
            True if valid, False otherwise
        """
        # Check required field
        if 'contact_ids' not in params:
            logger.error("Missing required field 'contact_ids' in get_contact_details request")
            return False
            
        contact_ids = params.get('contact_ids', [])
        if not isinstance(contact_ids, list):
            logger.error("'contact_ids' must be a list in get_contact_details request")
            return False
            
        if not contact_ids:
            logger.error("'contact_ids' must not be empty")
            return False
            
        # Validate include
        include = params.get('include')
        if include is not None and not isinstance(include, dict):
            logger.error("'include' must be an object in get_contact_details request")
            return False
        
        return True
    
    @staticmethod
    def validate_query_tags_request(params: Dict[str, Any]) -> bool:
        """Validate query_tags request parameters
        
        Args:
            params: Request parameters
            
        Returns:
            True if valid, False otherwise
        """
        # Validate filters
        filters = params.get('filters')
        if filters is not None:
            if not isinstance(filters, list):
                logger.error("'filters' must be a list in query_tags request")
                return False
                
            for filter_item in filters:
                if not isinstance(filter_item, dict):
                    logger.error("Each filter item must be an object")
                    return False
        
        # Validate sort
        sort = params.get('sort')
        if sort is not None:
            if not isinstance(sort, list):
                logger.error("'sort' must be a list in query_tags request")
                return False
                
            for sort_item in sort:
                if not isinstance(sort_item, dict):
                    logger.error("Each sort item must be an object")
                    return False
                    
                if 'field' not in sort_item:
                    logger.error("Sort item missing 'field'")
                    return False
        
        # Validate max_results
        max_results = params.get('max_results')
        if max_results is not None:
            if not isinstance(max_results, int) or max_results <= 0:
                logger.error("'max_results' must be a positive integer")
                return False
        
        return True
    
    @staticmethod
    def validate_modify_tags_request(params: Dict[str, Any]) -> bool:
        """Validate modify_tags request parameters
        
        Args:
            params: Request parameters
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ['operation', 'tag_ids', 'contact_ids']
        for field in required_fields:
            if field not in params:
                logger.error(f"Missing required field '{field}' in modify_tags request")
                return False
                
        # Validate operation
        operation = params.get('operation')
        if operation not in ['add', 'remove']:
            logger.error(f"Invalid operation: {operation}. Must be 'add' or 'remove'")
            return False
            
        # Validate tag_ids
        tag_ids = params.get('tag_ids', [])
        if not isinstance(tag_ids, list) or not tag_ids:
            logger.error("'tag_ids' must be a non-empty list")
            return False
            
        # Validate contact_ids
        contact_ids = params.get('contact_ids', [])
        if not isinstance(contact_ids, list) or not contact_ids:
            logger.error("'contact_ids' must be a non-empty list")
            return False
        
        return True
    
    @staticmethod
    def validate_get_tag_details_request(params: Dict[str, Any]) -> bool:
        """Validate get_tag_details request parameters
        
        Args:
            params: Request parameters
            
        Returns:
            True if valid, False otherwise
        """
        # Check required field
        if 'tag_ids' not in params:
            logger.error("Missing required field 'tag_ids' in get_tag_details request")
            return False
            
        tag_ids = params.get('tag_ids', [])
        if not isinstance(tag_ids, list):
            logger.error("'tag_ids' must be a list in get_tag_details request")
            return False
            
        if not tag_ids:
            logger.error("'tag_ids' must not be empty")
            return False
        
        # Validate include
        include = params.get('include')
        if include is not None and not isinstance(include, dict):
            logger.error("'include' must be an object in get_tag_details request")
            return False
        
        return True
    
    @staticmethod
    def validate_intersect_contact_lists_request(params: Dict[str, Any]) -> bool:
        """Validate intersect_contact_lists request parameters
        
        Args:
            params: Request parameters
            
        Returns:
            True if valid, False otherwise
        """
        # Check required field
        if 'lists' not in params:
            logger.error("Missing required field 'lists' in intersect_contact_lists request")
            return False
            
        lists = params.get('lists', [])
        if not isinstance(lists, list):
            logger.error("'lists' must be a list in intersect_contact_lists request")
            return False
            
        if not lists:
            logger.error("'lists' must not be empty")
            return False
            
        # Validate each list
        for list_item in lists:
            if not isinstance(list_item, dict):
                logger.error("Each list item must be an object")
                return False
                
            if 'list_id' not in list_item:
                logger.error("List item missing 'list_id'")
                return False
                
            if 'contact_ids' not in list_item or not isinstance(list_item['contact_ids'], list):
                logger.error("List item missing 'contact_ids' as list")
                return False
        
        return True
