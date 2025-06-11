"""
Cache Manager

Provides caching functionality for MCP server operations
to reduce API calls and improve response times.

This module now uses the new SQLite-based persistent cache for better
performance and persistence across restarts.
"""

import logging
from typing import Dict, List, Any, Optional, Union

from .persistent_manager import PersistentCacheManager

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching for Keap MCP server

    This is now a wrapper around PersistentCacheManager for backward compatibility.
    """

    def __init__(
        self,
        db_path: str = "keap_cache.db",
        max_entries: int = 10000,
        max_memory_mb: int = 100,
    ):
        """Initialize the cache manager

        Args:
            db_path: Path to SQLite database file
            max_entries: Maximum number of cache entries
            max_memory_mb: Maximum memory usage in MB
        """
        self._persistent_cache = PersistentCacheManager(
            db_path, max_entries, max_memory_mb
        )
        logger.info(
            f"Initialized persistent cache at {db_path} with {max_entries} max entries and {max_memory_mb}MB memory limit"
        )

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        return self._persistent_cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set a value in the cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        return self._persistent_cache.set(key, value, ttl)

    def invalidate_contacts(self, contact_ids: List[Union[int, str]]) -> None:
        """Invalidate cache entries for specific contacts

        Args:
            contact_ids: List of contact IDs to invalidate
        """
        return self._persistent_cache.invalidate_contacts(contact_ids)

    def invalidate_tags(self, tag_ids: List[Union[int, str]]) -> None:
        """Invalidate cache entries for specific tags

        Args:
            tag_ids: List of tag IDs to invalidate
        """
        return self._persistent_cache.invalidate_tags(tag_ids)

    def invalidate_all(self) -> None:
        """Invalidate all cache entries"""
        return self._persistent_cache.invalidate_all()

    def cleanup(self) -> None:
        """Remove expired cache entries"""
        return self._persistent_cache.cleanup_expired()

    def cleanup_expired(self) -> None:
        """Remove expired cache entries (alias for cleanup)"""
        return self._persistent_cache.cleanup_expired()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        return self._persistent_cache.get_stats()

    def close(self) -> None:
        """Close the cache manager and clean up resources"""
        return self._persistent_cache.close()
