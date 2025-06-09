"""
Service Container

Minimal service container for dependency injection.
"""

from typing import Type, TypeVar

T = TypeVar('T')

class ServiceRegistry:
    """Simple service registry"""
    
    def __init__(self):
        self._services = {}
    
    def register(self, service_type: Type[T], instance: T):
        self._services[service_type] = instance
    
    def get(self, service_type: Type[T]) -> T:
        return self._services.get(service_type)

class ServiceContainer:
    """Minimal service container"""
    
    def __init__(self):
        self.registry = ServiceRegistry()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the container"""
        self._initialized = True
    
    def get_service(self, service_type: Type[T]) -> T:
        """Get a service by type"""
        return self.registry.get(service_type)
    
    async def close(self):
        """Close the container"""
        self._initialized = False

# Global container instance
_global_container = None

def get_service_container() -> ServiceContainer:
    """Get the global service container"""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container

async def close_global_container():
    """Close the global service container"""
    global _global_container
    if _global_container:
        await _global_container.close()
        _global_container = None

__all__ = [
    'ServiceContainer',
    'ServiceRegistry', 
    'get_service_container',
    'close_global_container'
]