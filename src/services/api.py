"""
API Service

Simplified API service that wraps the existing KeapApiService.
"""

from src.api.client import KeapApiService

# Create simple error classes for backward compatibility
class ApiError(Exception):
    """Base API error"""
    pass

class RateLimitError(ApiError):
    """Rate limit exceeded error"""
    pass

__all__ = [
    'KeapApiService',
    'ApiError', 
    'RateLimitError'
]