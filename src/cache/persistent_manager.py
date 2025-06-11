"""
Persistent Cache Manager

Provides SQLite-based persistent caching functionality for MCP server operations
to reduce API calls, improve response times, and survive restarts.
"""

import time
import sqlite3
import logging
import pickle
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PersistentCacheManager:
    """
    SQLite-based persistent cache manager for Keap MCP server
    Features:
    - Persistent storage across restarts
    - Memory limits and cleanup
    - Efficient ID-based invalidation
    - Thread-safe operations
    """

    def __init__(
        self,
        db_path: str = "keap_cache.db",
        max_entries: int = 10000,
        max_memory_mb: int = 100,
    ):
        """Initialize the persistent cache manager

        Args:
            db_path: Path to SQLite database file
            max_entries: Maximum number of cache entries
            max_memory_mb: Maximum memory usage in MB
        """
        self.db_path = Path(db_path)
        self.max_entries = max_entries
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._lock = threading.RLock()

        # Initialize database
        self._init_database()

        # Clean up expired entries on startup
        self.cleanup_expired()

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables"""
        with self._get_connection() as conn:
            # Main cache table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    expires_at REAL NOT NULL,
                    created_at REAL NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL NOT NULL
                )
            """)

            # Contact ID mapping table for efficient invalidation
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contact_cache_mapping (
                    contact_id INTEGER NOT NULL,
                    cache_key TEXT NOT NULL,
                    PRIMARY KEY (contact_id, cache_key),
                    FOREIGN KEY (cache_key) REFERENCES cache(key) ON DELETE CASCADE
                )
            """)

            # Tag ID mapping table for efficient invalidation
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tag_cache_mapping (
                    tag_id INTEGER NOT NULL,
                    cache_key TEXT NOT NULL,
                    PRIMARY KEY (tag_id, cache_key),
                    FOREIGN KEY (cache_key) REFERENCES cache(key) ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_last_accessed ON cache(last_accessed)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_contact_mapping_id ON contact_cache_mapping(contact_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tag_mapping_id ON tag_cache_mapping(tag_id)"
            )

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT value, expires_at FROM cache WHERE key = ? AND expires_at > ?",
                        (key, time.time()),
                    )
                    row = cursor.fetchone()

                    if row is None:
                        return None

                    # Update access statistics
                    conn.execute(
                        "UPDATE cache SET access_count = access_count + 1, last_accessed = ? WHERE key = ?",
                        (time.time(), key),
                    )

                    # Deserialize value
                    try:
                        return pickle.loads(row[0])  # nosec B301 - Controlled pickle usage in cache
                    except (pickle.PickleError, TypeError) as e:
                        logger.warning(
                            f"Failed to deserialize cached value for key {key}: {e}"
                        )
                        self._remove_key(key)
                        return None

            except sqlite3.Error as e:
                logger.error(f"Cache get error for key {key}: {e}")
                return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set a value in the cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        with self._lock:
            try:
                # Serialize value
                try:
                    serialized_value = pickle.dumps(value)
                except (pickle.PickleError, TypeError) as e:
                    logger.warning(f"Cannot serialize value for key '{key}': {e}")
                    return  # Skip caching if value cannot be serialized

                value_size = len(serialized_value)
                current_time = time.time()
                expires_at = current_time + ttl

                # Check if we need to make space
                self._ensure_space(value_size)

                with self._get_connection() as conn:
                    # Insert or replace cache entry
                    conn.execute(
                        """INSERT OR REPLACE INTO cache 
                           (key, value, expires_at, created_at, size_bytes, last_accessed) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            key,
                            serialized_value,
                            expires_at,
                            current_time,
                            value_size,
                            current_time,
                        ),
                    )

                    # Remove old ID mappings for this key
                    conn.execute(
                        "DELETE FROM contact_cache_mapping WHERE cache_key = ?", (key,)
                    )
                    conn.execute(
                        "DELETE FROM tag_cache_mapping WHERE cache_key = ?", (key,)
                    )

                    # Track IDs for invalidation
                    self._track_ids(conn, key, value)

            except (sqlite3.Error, pickle.PickleError) as e:
                logger.error(f"Cache set error for key {key}: {e}")

    def _ensure_space(self, required_bytes: int) -> None:
        """Ensure there's enough space for new cache entry

        Args:
            required_bytes: Bytes needed for new entry
        """
        try:
            with self._get_connection() as conn:
                # Check current cache size
                cursor = conn.execute(
                    "SELECT COUNT(*), SUM(size_bytes) FROM cache WHERE expires_at > ?",
                    (time.time(),),
                )
                count, total_size = cursor.fetchone()
                total_size = total_size or 0

                # Remove entries if we exceed limits
                if (
                    count >= self.max_entries
                    or (total_size + required_bytes) > self.max_memory_bytes
                ):
                    # Remove least recently used entries
                    entries_to_remove = max(
                        1, int(self.max_entries * 0.1)
                    )  # Remove 10% of max entries
                    cursor = conn.execute(
                        "SELECT key FROM cache ORDER BY last_accessed ASC LIMIT ?",
                        (entries_to_remove,),
                    )
                    keys_to_remove = [row[0] for row in cursor.fetchall()]

                    for key in keys_to_remove:
                        self._remove_key_with_conn(conn, key)

                    logger.debug(
                        f"Removed {len(keys_to_remove)} cache entries to make space"
                    )

        except sqlite3.Error as e:
            logger.error(f"Error ensuring cache space: {e}")

    def _track_ids(self, conn: sqlite3.Connection, key: str, value: Any) -> None:
        """Track IDs for invalidation

        Args:
            conn: Database connection
            key: Cache key
            value: Value to track
        """
        # Extract contact IDs
        contact_ids = set()

        if isinstance(value, dict):
            # Handle query_contacts result
            if "contact_ids" in value and isinstance(value["contact_ids"], list):
                contact_ids.update(value["contact_ids"])

            # Handle get_contact_details result
            if "contacts" in value and isinstance(value["contacts"], list):
                for contact in value["contacts"]:
                    if isinstance(contact, dict) and "id" in contact:
                        contact_ids.add(contact["id"])

        # Insert contact mappings
        for contact_id in contact_ids:
            if isinstance(contact_id, (int, str)):
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO contact_cache_mapping (contact_id, cache_key) VALUES (?, ?)",
                        (int(contact_id), key),
                    )
                except (ValueError, sqlite3.Error) as e:
                    logger.warning(f"Failed to track contact ID {contact_id}: {e}")

        # Extract tag IDs
        tag_ids = set()

        if isinstance(value, dict):
            # Handle query_tags result
            if "tag_ids" in value and isinstance(value["tag_ids"], list):
                tag_ids.update(value["tag_ids"])

            # Handle get_tag_details result
            if "tags" in value and isinstance(value["tags"], list):
                for tag in value["tags"]:
                    if isinstance(tag, dict) and "id" in tag:
                        tag_ids.add(tag["id"])

        # Insert tag mappings
        for tag_id in tag_ids:
            if isinstance(tag_id, (int, str)):
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO tag_cache_mapping (tag_id, cache_key) VALUES (?, ?)",
                        (int(tag_id), key),
                    )
                except (ValueError, sqlite3.Error) as e:
                    logger.warning(f"Failed to track tag ID {tag_id}: {e}")

    def _remove_key(self, key: str) -> None:
        """Remove a key from the cache

        Args:
            key: Cache key
        """
        try:
            with self._get_connection() as conn:
                self._remove_key_with_conn(conn, key)
        except sqlite3.Error as e:
            logger.error(f"Error removing cache key {key}: {e}")

    def _remove_key_with_conn(self, conn: sqlite3.Connection, key: str) -> None:
        """Remove a key from the cache using existing connection

        Args:
            conn: Database connection
            key: Cache key
        """
        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.execute("DELETE FROM contact_cache_mapping WHERE cache_key = ?", (key,))
        conn.execute("DELETE FROM tag_cache_mapping WHERE cache_key = ?", (key,))

    def invalidate_contacts(self, contact_ids: List[Union[int, str]]) -> None:
        """Invalidate cache entries for specific contacts

        Args:
            contact_ids: List of contact IDs to invalidate
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    # Get all cache keys associated with these contacts
                    placeholders = ",".join("?" * len(contact_ids))
                    cursor = conn.execute(
                        f"SELECT DISTINCT cache_key FROM contact_cache_mapping WHERE contact_id IN ({placeholders})",  # nosec B608 - Controlled parameterized query
                        [
                            int(cid)
                            for cid in contact_ids
                            if isinstance(cid, (int, str))
                        ],
                    )
                    keys_to_invalidate = [row[0] for row in cursor.fetchall()]

                    # Remove cache entries
                    for key in keys_to_invalidate:
                        self._remove_key_with_conn(conn, key)
                        logger.debug(f"Invalidated cache key: {key}")

                    logger.info(
                        f"Invalidated {len(keys_to_invalidate)} cache entries for {len(contact_ids)} contacts"
                    )

            except (sqlite3.Error, ValueError) as e:
                logger.error(f"Error invalidating contacts {contact_ids}: {e}")

    def invalidate_tags(self, tag_ids: List[Union[int, str]]) -> None:
        """Invalidate cache entries for specific tags

        Args:
            tag_ids: List of tag IDs to invalidate
        """
        with self._lock:
            try:
                with self._get_connection() as conn:
                    # Get all cache keys associated with these tags
                    placeholders = ",".join("?" * len(tag_ids))
                    cursor = conn.execute(
                        f"SELECT DISTINCT cache_key FROM tag_cache_mapping WHERE tag_id IN ({placeholders})",  # nosec B608 - Controlled parameterized query
                        [int(tid) for tid in tag_ids if isinstance(tid, (int, str))],
                    )
                    keys_to_invalidate = [row[0] for row in cursor.fetchall()]

                    # Remove cache entries
                    for key in keys_to_invalidate:
                        self._remove_key_with_conn(conn, key)
                        logger.debug(f"Invalidated cache key: {key}")

                    logger.info(
                        f"Invalidated {len(keys_to_invalidate)} cache entries for {len(tag_ids)} tags"
                    )

            except (sqlite3.Error, ValueError) as e:
                logger.error(f"Error invalidating tags {tag_ids}: {e}")

    def invalidate_all(self) -> None:
        """Invalidate all cache entries"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("DELETE FROM cache")
                    conn.execute("DELETE FROM contact_cache_mapping")
                    conn.execute("DELETE FROM tag_cache_mapping")
                    logger.info("Invalidated all cache entries")
            except sqlite3.Error as e:
                logger.error(f"Error invalidating all cache entries: {e}")

    def cleanup_expired(self) -> None:
        """Remove expired cache entries"""
        with self._lock:
            try:
                with self._get_connection() as conn:
                    current_time = time.time()
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM cache WHERE expires_at < ?",
                        (current_time,),
                    )
                    expired_count = cursor.fetchone()[0]

                    if expired_count > 0:
                        conn.execute(
                            "DELETE FROM cache WHERE expires_at < ?", (current_time,)
                        )
                        # Mappings are automatically cleaned up by foreign key constraints
                        logger.debug(
                            f"Cleaned up {expired_count} expired cache entries"
                        )

            except sqlite3.Error as e:
                logger.error(f"Error cleaning up expired entries: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        try:
            with self._get_connection() as conn:
                # Basic stats
                cursor = conn.execute(
                    "SELECT COUNT(*), SUM(size_bytes), AVG(access_count) FROM cache WHERE expires_at > ?",
                    (time.time(),),
                )
                count, total_size, avg_access = cursor.fetchone()

                # Hit rate calculation (requires tracking hits/misses)
                cursor = conn.execute("SELECT COUNT(*) FROM contact_cache_mapping")
                contact_mappings = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM tag_cache_mapping")
                tag_mappings = cursor.fetchone()[0]

                return {
                    "total_entries": count or 0,
                    "total_size_bytes": total_size or 0,
                    "total_size_mb": round((total_size or 0) / (1024 * 1024), 2),
                    "average_access_count": round(avg_access or 0, 2),
                    "contact_mappings": contact_mappings,
                    "tag_mappings": tag_mappings,
                    "memory_usage_percent": round(
                        ((total_size or 0) / self.max_memory_bytes) * 100, 2
                    ),
                    "entry_usage_percent": round(
                        ((count or 0) / self.max_entries) * 100, 2
                    ),
                }
        except sqlite3.Error as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    def close(self) -> None:
        """Close the cache manager and clean up resources"""
        self.cleanup_expired()
        logger.info("Cache manager closed")
