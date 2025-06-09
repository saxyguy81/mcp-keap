"""
Services Package

Minimal services for MCP server functionality.
These are simplified versions to support existing tests.
"""

from .container import get_service_container, close_global_container

__all__ = [
    'get_service_container',
    'close_global_container'
]