"""
Cache Service

Simplified cache service that wraps the existing CacheManager.
"""

from src.cache.manager import CacheManager

class CacheService:
    """Simplified cache service wrapper"""
    
    def __init__(self, cache_manager: CacheManager = None):
        self.cache_manager = cache_manager or CacheManager()
    
    def get(self, key: str):
        return self.cache_manager.get(key)
    
    def set(self, key: str, value, ttl: int = 3600):
        return self.cache_manager.set(key, value, ttl)
    
    def invalidate(self, key: str):
        return self.cache_manager.set(key, None, ttl=0)
    
    def clear(self):
        return self.cache_manager.invalidate_all()

__all__ = ['CacheService']