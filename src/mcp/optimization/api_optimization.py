"""
API Parameter Optimization

Intelligent server-side filtering and parameter optimization for maximum
performance and data reduction when interacting with the Keap API.
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of API parameter optimization."""
    optimization_strategy: str
    server_side_filters: Dict[str, Any]
    client_side_filters: List[Dict[str, Any]]
    estimated_data_reduction_ratio: float
    optimization_score: float


class ApiParameterOptimizer:
    """
    Optimizes API parameters to maximize server-side filtering and minimize
    data transfer and client-side processing.
    """
    
    def __init__(self):
        # Keap API field mappings and capabilities
        self.contact_field_mappings = {
            'id': {'api_field': 'id', 'operators': ['EQUALS', 'IN'], 'reduction': 0.95},
            'email': {'api_field': 'email', 'operators': ['EQUALS', 'CONTAINS'], 'reduction': 0.80},
            'given_name': {'api_field': 'given_name', 'operators': ['EQUALS', 'CONTAINS'], 'reduction': 0.60},
            'family_name': {'api_field': 'family_name', 'operators': ['EQUALS', 'CONTAINS'], 'reduction': 0.60},
            'phone1': {'api_field': 'phone', 'operators': ['EQUALS'], 'reduction': 0.70},
            'city': {'api_field': 'city', 'operators': ['EQUALS'], 'reduction': 0.40},
            'state': {'api_field': 'state', 'operators': ['EQUALS'], 'reduction': 0.50},
            'country': {'api_field': 'country', 'operators': ['EQUALS'], 'reduction': 0.60},
            'postal_code': {'api_field': 'postal_code', 'operators': ['EQUALS'], 'reduction': 0.30},
            'date_created': {'api_field': 'date_created', 'operators': ['SINCE', 'UNTIL'], 'reduction': 0.85},
            'last_updated': {'api_field': 'last_updated', 'operators': ['SINCE', 'UNTIL'], 'reduction': 0.70},
            'tag_id': {'api_field': 'tag_id', 'operators': ['EQUALS'], 'reduction': 0.90}
        }
        
        self.tag_field_mappings = {
            'id': {'api_field': 'id', 'operators': ['EQUALS', 'IN'], 'reduction': 0.95},
            'name': {'api_field': 'name', 'operators': ['EQUALS', 'CONTAINS'], 'reduction': 0.70},
            'category': {'api_field': 'category', 'operators': ['EQUALS'], 'reduction': 0.80}
        }
    
    def optimize_contact_query_parameters(self, filters: List[Dict[str, Any]], 
                                        limit: int = 200, 
                                        offset: int = 0) -> OptimizationResult:
        """
        Optimize contact query parameters for maximum server-side filtering.
        
        Args:
            filters: List of filter conditions
            limit: Query limit
            offset: Query offset
            
        Returns:
            OptimizationResult with optimized parameters
        """
        server_filters = {}
        client_filters = []
        total_reduction = 1.0
        optimization_score = 0.0
        
        for filter_condition in filters:
            # Skip logical groups - they must be handled client-side
            if 'operator' in filter_condition and 'conditions' in filter_condition:
                client_filters.append(filter_condition)
                continue
            
            field = filter_condition.get('field')
            operator = filter_condition.get('operator', '').upper()
            value = filter_condition.get('value')
            
            # Check if field can be optimized server-side
            if field in self.contact_field_mappings:
                field_config = self.contact_field_mappings[field]
                
                if operator in field_config['operators']:
                    # Can be optimized server-side
                    api_field = field_config['api_field']
                    
                    if operator == 'EQUALS':
                        server_filters[api_field] = value
                    elif operator == 'CONTAINS' and field in ['email', 'given_name', 'family_name']:
                        if field == 'email':
                            server_filters[api_field] = f"*{value}*"
                        else:
                            server_filters[api_field] = value
                    elif operator == 'IN' and isinstance(value, list):
                        # For IN operator, we might need to use multiple API calls or client-side filtering
                        if len(value) <= 5:  # Small lists can be handled server-side
                            server_filters[api_field] = value[0]  # Use first value for now
                            if len(value) > 1:
                                client_filters.append(filter_condition)  # Rest handled client-side
                        else:
                            client_filters.append(filter_condition)
                    else:
                        server_filters[api_field] = value
                    
                    # Update reduction estimate
                    total_reduction *= field_config['reduction']
                    optimization_score += 1.0
                else:
                    # Operator not supported server-side
                    client_filters.append(filter_condition)
            else:
                # Field not supported server-side
                client_filters.append(filter_condition)
        
        # Calculate final optimization metrics
        total_filters = len(filters)
        server_filter_count = len(server_filters)
        
        if total_filters > 0:
            optimization_score = server_filter_count / total_filters
        
        # Determine optimization strategy
        if optimization_score >= 0.8:
            strategy = "highly_optimized"
        elif optimization_score >= 0.5:
            strategy = "moderately_optimized"
        elif optimization_score >= 0.2:
            strategy = "partially_optimized"
        else:
            strategy = "minimal_optimization"
        
        return OptimizationResult(
            optimization_strategy=strategy,
            server_side_filters=server_filters,
            client_side_filters=client_filters,
            estimated_data_reduction_ratio=total_reduction,
            optimization_score=optimization_score
        )
    
    def optimize_tag_query_parameters(self, filters: List[Dict[str, Any]], 
                                    limit: int = 1000) -> OptimizationResult:
        """
        Optimize tag query parameters for maximum server-side filtering.
        
        Args:
            filters: List of filter conditions
            limit: Query limit
            
        Returns:
            OptimizationResult with optimized parameters
        """
        server_filters = {}
        client_filters = []
        total_reduction = 1.0
        optimization_score = 0.0
        
        for filter_condition in filters:
            # Skip logical groups
            if 'operator' in filter_condition and 'conditions' in filter_condition:
                client_filters.append(filter_condition)
                continue
            
            field = filter_condition.get('field')
            operator = filter_condition.get('operator', '').upper()
            value = filter_condition.get('value')
            
            # Check if field can be optimized server-side
            if field in self.tag_field_mappings:
                field_config = self.tag_field_mappings[field]
                
                if operator in field_config['operators']:
                    api_field = field_config['api_field']
                    
                    if operator == 'EQUALS':
                        server_filters[api_field] = value
                    elif operator == 'CONTAINS' and field == 'name':
                        server_filters[api_field] = f"*{value}*"
                    else:
                        server_filters[api_field] = value
                    
                    total_reduction *= field_config['reduction']
                    optimization_score += 1.0
                else:
                    client_filters.append(filter_condition)
            else:
                client_filters.append(filter_condition)
        
        # Calculate optimization metrics
        total_filters = len(filters)
        if total_filters > 0:
            optimization_score = len(server_filters) / total_filters
        
        # Determine strategy
        if optimization_score >= 0.8:
            strategy = "highly_optimized"
        elif optimization_score >= 0.5:
            strategy = "moderately_optimized"
        else:
            strategy = "minimal_optimization"
        
        return OptimizationResult(
            optimization_strategy=strategy,
            server_side_filters=server_filters,
            client_side_filters=client_filters,
            estimated_data_reduction_ratio=total_reduction,
            optimization_score=optimization_score
        )
    
    def get_field_optimization_info(self, query_type: str = 'contact') -> Dict[str, Any]:
        """
        Get information about which fields can be optimized server-side.
        
        Args:
            query_type: Type of query ('contact' or 'tag')
            
        Returns:
            Dictionary with field optimization capabilities
        """
        if query_type == 'contact':
            mappings = self.contact_field_mappings
        elif query_type == 'tag':
            mappings = self.tag_field_mappings
        else:
            return {}
        
        optimization_info = {}
        for field, config in mappings.items():
            optimization_info[field] = {
                'api_field': config['api_field'],
                'supported_operators': config['operators'],
                'estimated_reduction': config['reduction']
            }
        
        return optimization_info
    
    def analyze_filter_performance(self, filters: List[Dict[str, Any]], 
                                 query_type: str = 'contact') -> Dict[str, Any]:
        """
        Analyze the performance characteristics of a set of filters.
        
        Args:
            filters: List of filter conditions
            query_type: Type of query
            
        Returns:
            Performance analysis
        """
        if query_type == 'contact':
            result = self.optimize_contact_query_parameters(filters)
        else:
            result = self.optimize_tag_query_parameters(filters)
        
        return {
            "total_filters": len(filters),
            "server_side_filters": len(result.server_side_filters),
            "client_side_filters": len(result.client_side_filters),
            "optimization_strategy": result.optimization_strategy,
            "optimization_score": result.optimization_score,
            "estimated_data_reduction": result.estimated_data_reduction_ratio,
            "performance_rating": self._get_performance_rating(result.optimization_score)
        }
    
    def _get_performance_rating(self, optimization_score: float) -> str:
        """Get human-readable performance rating."""
        if optimization_score >= 0.8:
            return "Excellent"
        elif optimization_score >= 0.6:
            return "Good"
        elif optimization_score >= 0.4:
            return "Fair"
        elif optimization_score >= 0.2:
            return "Poor"
        else:
            return "Very Poor"