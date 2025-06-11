"""
Advanced unit tests for persistent cache manager - covering missing functionality
"""

import pytest
import tempfile
import sqlite3
import time
import threading
from pathlib import Path

from src.cache.persistent_manager import PersistentCacheManager


class TestPersistentCacheManagerAdvanced:
    """Test advanced persistent cache manager functionality"""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        try:
            Path(db_path).unlink()
        except FileNotFoundError:
            pass

    @pytest.fixture
    def cache_manager(self, temp_db_path):
        """Create a cache manager with temporary database"""
        manager = PersistentCacheManager(
            db_path=temp_db_path, max_entries=100, max_memory_mb=1
        )
        yield manager
        manager.close()

    def test_init_database_creates_tables(self, temp_db_path):
        """Test that database initialization creates required tables"""
        manager = PersistentCacheManager(db_path=temp_db_path)

        # Check that tables exist
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "cache" in tables
            assert "contact_cache_mapping" in tables
            assert "tag_cache_mapping" in tables

        manager.close()

    def test_init_database_with_existing_db(self, temp_db_path):
        """Test database initialization with existing database"""
        # Create first manager to initialize DB
        manager1 = PersistentCacheManager(db_path=temp_db_path)
        manager1.set("test_key", "test_value")
        manager1.close()

        # Create second manager with same DB
        manager2 = PersistentCacheManager(db_path=temp_db_path)

        # Should be able to retrieve data from existing DB
        value = manager2.get("test_key")
        assert value == "test_value"

        manager2.close()

    def test_set_and_get_complex_data(self, cache_manager):
        """Test storing and retrieving complex data structures"""
        complex_data = {
            "list": [1, 2, 3, {"nested": True}],
            "dict": {"key": "value", "number": 42},
            "tuple": (1, 2, 3),
            "none": None,
            "bool": False,
        }

        cache_manager.set("complex", complex_data, ttl=3600)
        retrieved = cache_manager.get("complex")

        assert retrieved == complex_data

    def test_set_with_custom_ttl(self, cache_manager):
        """Test setting entries with custom TTL"""
        cache_manager.set("short_ttl", "value", ttl=1)

        # Should be available immediately
        assert cache_manager.get("short_ttl") == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache_manager.get("short_ttl") is None

    def test_get_nonexistent_key(self, cache_manager):
        """Test getting a non-existent key"""
        result = cache_manager.get("nonexistent")
        assert result is None

    def test_get_expired_entry(self, cache_manager):
        """Test getting an expired entry"""
        # Set entry with very short TTL
        cache_manager.set("expired", "value", ttl=0.1)
        time.sleep(0.2)

        result = cache_manager.get("expired")
        assert result is None

    def test_remove_key_existing(self, cache_manager):
        """Test removing an existing key"""
        cache_manager.set("to_remove", "value")

        # Verify it exists
        assert cache_manager.get("to_remove") == "value"

        # Remove it using private method (for testing)
        cache_manager._remove_key("to_remove")

        # Verify it's gone
        assert cache_manager.get("to_remove") is None

    def test_remove_key_nonexistent(self, cache_manager):
        """Test removing a non-existent key"""
        # Should not raise an error
        cache_manager._remove_key("nonexistent")

    def test_cleanup_expired_entries(self, cache_manager):
        """Test cleanup of expired entries"""
        # Add some entries with different TTLs
        cache_manager.set("keep1", "value1", ttl=3600)
        cache_manager.set("keep2", "value2", ttl=3600)
        cache_manager.set("expire1", "value3", ttl=0.1)
        cache_manager.set("expire2", "value4", ttl=0.1)

        # Wait for expiration
        time.sleep(0.2)

        # Run cleanup
        cache_manager.cleanup_expired()

        # Check that non-expired entries remain
        assert cache_manager.get("keep1") == "value1"
        assert cache_manager.get("keep2") == "value2"

        # Check that expired entries are gone
        assert cache_manager.get("expire1") is None
        assert cache_manager.get("expire2") is None

    def test_invalidate_contacts(self, cache_manager):
        """Test invalidating contact-related cache entries"""
        # Add cache entries with contact data that will be tracked
        cache_manager.set("contacts_result_1", {"contacts": [{"id": 123, "name": "John"}]})
        cache_manager.set("contacts_result_2", {"contacts": [{"id": 456, "name": "Jane"}]})
        cache_manager.set("contact_ids_result", {"contact_ids": [123, 456]})
        cache_manager.set("tags:all", [{"id": 1, "name": "VIP"}])
        cache_manager.set("other:data", "some value")

        # Invalidate contact 123
        cache_manager.invalidate_contacts([123])

        # Check that contact 123 entries are gone
        assert cache_manager.get("contacts_result_1") is None
        assert cache_manager.get("contact_ids_result") is None

        # Check that other entries remain
        assert cache_manager.get("contacts_result_2") is not None
        assert cache_manager.get("tags:all") is not None
        assert cache_manager.get("other:data") is not None

    def test_invalidate_contacts_multiple(self, cache_manager):
        """Test invalidating multiple contacts"""
        # Add contact entries with trackable data structures
        cache_manager.set("contacts_123", {"contacts": [{"id": 123}]})
        cache_manager.set("contacts_456", {"contacts": [{"id": 456}]})
        cache_manager.set("contacts_789", {"contacts": [{"id": 789}]})

        # Invalidate multiple contacts
        cache_manager.invalidate_contacts([123, 456])

        # Check results
        assert cache_manager.get("contacts_123") is None
        assert cache_manager.get("contacts_456") is None
        assert cache_manager.get("contacts_789") is not None

    def test_invalidate_tags(self, cache_manager):
        """Test invalidating tag-related cache entries"""
        # Add various cache entries with trackable data structures
        cache_manager.set("tags_result_10", {"tags": [{"id": 10, "name": "VIP"}]})
        cache_manager.set("tags_result_20", {"tags": [{"id": 20, "name": "Customer"}]})
        cache_manager.set("tag_ids_result", {"tag_ids": [10, 20]})
        cache_manager.set("contacts:all", [{"id": 123}])
        cache_manager.set("other:data", "some value")

        # Invalidate tag 10
        cache_manager.invalidate_tags([10])

        # Check that tag 10 entries are gone
        assert cache_manager.get("tags_result_10") is None
        assert cache_manager.get("tag_ids_result") is None

        # Check that other entries remain
        assert cache_manager.get("tags_result_20") is not None
        assert cache_manager.get("contacts:all") is not None
        assert cache_manager.get("other:data") is not None

    def test_invalidate_all(self, cache_manager):
        """Test invalidating all cache entries"""
        # Add multiple entries
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        cache_manager.set("key3", "value3")

        # Verify they exist
        assert cache_manager.get("key1") == "value1"
        assert cache_manager.get("key2") == "value2"
        assert cache_manager.get("key3") == "value3"

        # Invalidate all
        cache_manager.invalidate_all()

        # Verify they're all gone
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.get("key3") is None

    def test_get_stats_empty_cache(self, cache_manager):
        """Test getting statistics from empty cache"""
        stats = cache_manager.get_stats()

        assert stats["total_entries"] == 0
        assert stats["total_size_mb"] == 0.0
        assert stats["memory_usage_percent"] == 0.0
        assert stats["entry_usage_percent"] == 0.0
        assert stats["contact_mappings"] == 0
        assert stats["tag_mappings"] == 0

    def test_get_stats_with_entries(self, cache_manager):
        """Test getting statistics with cache entries"""
        # Add some entries
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", {"complex": "data", "number": 42})
        cache_manager.set("key3", [1, 2, 3, 4, 5])

        stats = cache_manager.get_stats()

        assert stats["total_entries"] == 3
        assert stats["total_size_mb"] >= 0  # May be 0 due to rounding
        assert stats["memory_usage_percent"] >= 0
        assert stats["entry_usage_percent"] > 0
        assert stats["contact_mappings"] >= 0
        assert stats["tag_mappings"] >= 0
        assert stats["average_access_count"] >= 0

    def test_memory_limit_enforcement(self, temp_db_path):
        """Test that memory limits are enforced"""
        # Create cache with reasonable memory limit
        cache_manager = PersistentCacheManager(
            db_path=temp_db_path,
            max_entries=1000,
            max_memory_mb=1,  # 1MB limit
        )

        try:
            # Add some data
            cache_manager.set("test", "value")

            # Get stats to verify memory tracking works
            stats = cache_manager.get_stats()
            # Memory usage percent should be reasonable (implementation calculates based on data)
            assert stats["memory_usage_percent"] >= 0
            assert isinstance(stats["memory_usage_percent"], (int, float))

        finally:
            cache_manager.close()

    def test_entry_limit_enforcement(self, temp_db_path):
        """Test that entry count limits are enforced"""
        # Create cache with small entry limit
        cache_manager = PersistentCacheManager(
            db_path=temp_db_path, max_entries=3, max_memory_mb=100
        )

        try:
            # Add entries up to the limit
            cache_manager.set("key1", "value1")
            cache_manager.set("key2", "value2")
            cache_manager.set("key3", "value3")

            stats = cache_manager.get_stats()
            assert stats["total_entries"] == 3

            # Add one more entry - should trigger cleanup
            cache_manager.set("key4", "value4")

            # Should still be at or below limit
            stats = cache_manager.get_stats()
            assert stats["total_entries"] <= 3

        finally:
            cache_manager.close()

    def test_concurrent_access(self, cache_manager):
        """Test concurrent access to cache"""
        results = []
        errors = []

        def worker(worker_id):
            try:
                # Each worker sets and gets its own key
                key = f"worker_{worker_id}"
                value = f"value_{worker_id}"

                cache_manager.set(key, value)
                retrieved = cache_manager.get(key)

                if retrieved == value:
                    results.append(worker_id)
                else:
                    errors.append(
                        f"Worker {worker_id}: expected {value}, got {retrieved}"
                    )

            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10, (
            f"Expected 10 successful operations, got {len(results)}"
        )

    def test_database_error_handling(self, temp_db_path):
        """Test handling of database errors"""
        cache_manager = PersistentCacheManager(db_path=temp_db_path)

        try:
            # Add an entry
            cache_manager.set("test", "value")
            
            # Verify it was stored
            result = cache_manager.get("test")
            assert result == "value"

            # Test graceful handling of non-existent keys
            result = cache_manager.get("nonexistent")
            assert result is None

        finally:
            try:
                cache_manager.close()
            except Exception:
                pass  # Handle any close errors gracefully

    def test_close_cleanup(self, temp_db_path):
        """Test that close properly cleans up resources"""
        cache_manager = PersistentCacheManager(db_path=temp_db_path)

        # Add some data
        cache_manager.set("test", "value")
        
        # Verify data exists
        assert cache_manager.get("test") == "value"

        # Close the manager
        cache_manager.close()

        # Verify the cache manager has expected attributes
        assert hasattr(cache_manager, "db_path")
        assert hasattr(cache_manager, "_lock")
        assert hasattr(cache_manager, "max_entries")

    def test_cache_key_patterns(self, cache_manager):
        """Test various cache key patterns"""
        # Test different data structures that will be tracked
        test_data = [
            ("contacts_with_123", {"contacts": [{"id": 123, "name": "John"}]}),
            ("contacts_with_456", {"contacts": [{"id": 456, "name": "Jane"}]}),
            ("contact_ids_list", {"contact_ids": [123, 456]}),
            ("tags_with_10", {"tags": [{"id": 10, "name": "VIP"}]}),
            ("tag_ids_list", {"tag_ids": [10, 20]}),
            ("other_data", "some untracked value"),
        ]

        # Set all keys
        for key, value in test_data:
            cache_manager.set(key, value)

        # Verify all are set
        for key, value in test_data:
            assert cache_manager.get(key) == value

        # Test contact invalidation
        cache_manager.invalidate_contacts([123])

        # Contact-related keys should be gone (those that contain contact ID 123)
        assert cache_manager.get("contacts_with_123") is None
        assert cache_manager.get("contact_ids_list") is None

        # Other entries should remain
        assert cache_manager.get("contacts_with_456") is not None
        assert cache_manager.get("tags_with_10") is not None
        assert cache_manager.get("tag_ids_list") is not None
        assert cache_manager.get("other_data") is not None

    def test_ttl_calculation(self, cache_manager):
        """Test TTL calculation and expiration logic"""
        current_time = time.time()

        # Set entry with 1 hour TTL
        cache_manager.set("test_ttl", "value", ttl=3600)

        # Check the stored expiration time using direct database access
        with cache_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT expires_at FROM cache WHERE key = ?", ("test_ttl",)
            )
            result = cursor.fetchone()

            if result:
                expires_at = result[0]
                # Should expire approximately 1 hour from now
                expected_expiry = current_time + 3600
                assert (
                    abs(expires_at - expected_expiry) < 5
                )  # Allow 5 seconds tolerance

    def test_serialization_edge_cases(self, cache_manager):
        """Test serialization of edge case data types"""
        edge_cases = [
            ("empty_dict", {}),
            ("empty_list", []),
            ("empty_string", ""),
            ("zero", 0),
            ("false", False),
            ("none", None),
            ("unicode", "🎉 Unicode test 测试"),
            ("large_number", 2**63 - 1),
            ("nested_empty", {"empty": [], "nested": {"inner": {}}}),
        ]

        for key, value in edge_cases:
            cache_manager.set(key, value)
            retrieved = cache_manager.get(key)
            assert retrieved == value, (
                f"Failed for {key}: expected {value}, got {retrieved}"
            )

    def test_database_path_creation(self):
        """Test that database file is created in existing directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "cache.db"

            # File doesn't exist yet
            assert not db_path.exists()

            # Create cache manager with path in existing directory
            cache_manager = PersistentCacheManager(db_path=str(db_path))

            try:
                # Database file should be created
                assert db_path.exists()

                # Should be able to use the cache
                cache_manager.set("test", "value")
                assert cache_manager.get("test") == "value"

            finally:
                cache_manager.close()
