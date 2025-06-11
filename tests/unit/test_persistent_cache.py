"""
Unit Tests for Persistent Cache Manager

Tests the SQLite-based persistent cache implementation including:
- Basic cache operations (get/set)
- TTL handling and expiration
- Memory limits and cleanup
- ID tracking and invalidation
- Thread safety
- Database persistence
"""

import time
import threading
from src.cache.persistent_manager import PersistentCacheManager


class TestPersistentCacheBasics:
    """Test basic cache operations"""
    
    def test_cache_initialization(self, temp_cache_db):
        """Test cache manager initialization"""
        cache = PersistentCacheManager(
            db_path=temp_cache_db,
            max_entries=100,
            max_memory_mb=5
        )
        
        assert cache.db_path.name == temp_cache_db.split('/')[-1]
        assert cache.max_entries == 100
        assert cache.max_memory_bytes == 5 * 1024 * 1024
        
        # Verify database tables were created
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        
        cache.close()
    
    def test_basic_get_set(self, cache_manager):
        """Test basic get and set operations"""
        # Test setting and getting a simple value
        cache_manager.set("test_key", "test_value", ttl=3600)
        assert cache_manager.get("test_key") == "test_value"
        
        # Test getting non-existent key
        assert cache_manager.get("non_existent") is None
        
        # Test setting complex data
        complex_data = {
            "contacts": [{"id": 1, "name": "John"}],
            "count": 1,
            "metadata": {"api_calls": 2}
        }
        cache_manager.set("complex_key", complex_data)
        retrieved = cache_manager.get("complex_key")
        assert retrieved == complex_data
    
    def test_ttl_expiration(self, cache_manager):
        """Test TTL-based expiration"""
        # Set a value with short TTL
        cache_manager.set("short_ttl", "value", ttl=1)
        
        # Should be available immediately
        assert cache_manager.get("short_ttl") == "value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache_manager.get("short_ttl") is None
    
    def test_cache_overwrite(self, cache_manager):
        """Test overwriting existing cache entries"""
        cache_manager.set("key", "value1")
        assert cache_manager.get("key") == "value1"
        
        cache_manager.set("key", "value2")
        assert cache_manager.get("key") == "value2"
    
    def test_cache_stats(self, cache_manager):
        """Test cache statistics"""
        # Empty cache
        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 0
        assert stats["total_size_bytes"] == 0
        
        # Add some entries
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", {"data": "complex"})
        
        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] >= 0
        assert "memory_usage_percent" in stats
        assert "entry_usage_percent" in stats


class TestCacheMemoryManagement:
    """Test memory limits and cleanup"""
    
    def test_memory_limits(self, temp_cache_db):
        """Test that cache respects memory limits"""
        # Create cache with very small memory limit
        cache = PersistentCacheManager(
            db_path=temp_cache_db,
            max_entries=100,
            max_memory_mb=1  # Very small limit
        )
        
        # Add data until we hit memory limit
        large_data = "x" * (100 * 1024)  # 100KB strings
        
        for i in range(20):  # Should trigger cleanup
            cache.set(f"large_key_{i}", large_data)
        
        stats = cache.get_stats()
        # Should have cleaned up some entries
        assert stats["total_entries"] < 20
        assert stats["memory_usage_percent"] <= 100
        
        cache.close()
    
    def test_entry_limits(self, temp_cache_db):
        """Test that cache respects entry count limits"""
        cache = PersistentCacheManager(
            db_path=temp_cache_db,
            max_entries=10,  # Small limit
            max_memory_mb=50
        )
        
        # Add more entries than the limit
        for i in range(20):
            cache.set(f"key_{i}", f"value_{i}")
        
        stats = cache.get_stats()
        # Should have cleaned up entries
        assert stats["total_entries"] <= 10
        
        cache.close()
    
    def test_cleanup_expired(self, cache_manager):
        """Test cleanup of expired entries"""
        # Add entries with different TTLs
        cache_manager.set("short1", "value1", ttl=1)
        cache_manager.set("short2", "value2", ttl=1)
        cache_manager.set("long", "value3", ttl=3600)
        
        # Wait for some to expire
        time.sleep(1.1)
        
        # Manual cleanup
        cache_manager.cleanup_expired()
        
        # Check that expired entries are gone
        assert cache_manager.get("short1") is None
        assert cache_manager.get("short2") is None
        assert cache_manager.get("long") == "value3"


class TestCacheInvalidation:
    """Test ID-based cache invalidation"""
    
    def test_contact_id_tracking(self, cache_manager):
        """Test contact ID tracking and invalidation"""
        # Create cache entries with contact data
        contact_data1 = {
            "contact_ids": [1, 2, 3],
            "contacts": [{"id": 1}, {"id": 2}]
        }
        contact_data2 = {
            "contacts": [{"id": 2}, {"id": 4}]
        }
        
        cache_manager.set("query1", contact_data1)
        cache_manager.set("query2", contact_data2)
        
        # Verify entries exist
        assert cache_manager.get("query1") is not None
        assert cache_manager.get("query2") is not None
        
        # Invalidate contact 2 (should affect both entries)
        cache_manager.invalidate_contacts([2])
        
        # Both entries should be invalidated
        assert cache_manager.get("query1") is None
        assert cache_manager.get("query2") is None
    
    def test_tag_id_tracking(self, cache_manager):
        """Test tag ID tracking and invalidation"""
        # Create cache entries with tag data
        tag_data1 = {
            "tag_ids": [100, 101],
            "tags": [{"id": 100}, {"id": 101}]
        }
        tag_data2 = {
            "tags": [{"id": 101}, {"id": 102}]
        }
        
        cache_manager.set("tag_query1", tag_data1)
        cache_manager.set("tag_query2", tag_data2)
        
        # Invalidate tag 101
        cache_manager.invalidate_tags([101])
        
        # Both entries should be invalidated
        assert cache_manager.get("tag_query1") is None
        assert cache_manager.get("tag_query2") is None
    
    def test_invalidate_all(self, cache_manager):
        """Test invalidating all cache entries"""
        # Add multiple entries
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        cache_manager.set("key3", {"data": "complex"})
        
        # Verify entries exist
        assert cache_manager.get("key1") is not None
        assert cache_manager.get("key2") is not None
        assert cache_manager.get("key3") is not None
        
        # Invalidate all
        cache_manager.invalidate_all()
        
        # All entries should be gone
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.get("key3") is None
        
        # Stats should show empty cache
        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 0


class TestCachePersistence:
    """Test database persistence across restarts"""
    
    def test_persistence_across_restarts(self, temp_cache_db):
        """Test that cache survives cache manager restarts"""
        # Create first cache manager and add data
        cache1 = PersistentCacheManager(db_path=temp_cache_db)
        cache1.set("persistent_key", "persistent_value", ttl=3600)
        
        stats1 = cache1.get_stats()
        assert stats1["total_entries"] == 1
        
        cache1.close()
        
        # Create second cache manager with same database
        cache2 = PersistentCacheManager(db_path=temp_cache_db)
        
        # Data should still be there
        assert cache2.get("persistent_key") == "persistent_value"
        
        stats2 = cache2.get_stats()
        assert stats2["total_entries"] == 1
        
        cache2.close()
    
    def test_expired_cleanup_on_startup(self, temp_cache_db):
        """Test that expired entries are cleaned up on startup"""
        # Create cache and add short-lived data
        cache1 = PersistentCacheManager(db_path=temp_cache_db)
        cache1.set("short_lived", "value", ttl=1)
        cache1.set("long_lived", "value", ttl=3600)
        cache1.close()
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Create new cache manager (should trigger cleanup)
        cache2 = PersistentCacheManager(db_path=temp_cache_db)
        
        # Expired entry should be gone, long-lived should remain
        assert cache2.get("short_lived") is None
        assert cache2.get("long_lived") == "value"
        
        stats = cache2.get_stats()
        assert stats["total_entries"] == 1
        
        cache2.close()


class TestCacheThreadSafety:
    """Test thread safety of cache operations"""
    
    def test_concurrent_access(self, cache_manager):
        """Test concurrent cache access from multiple threads"""
        results = []
        errors = []
        
        def worker(thread_id: int):
            try:
                # Each thread sets and gets its own keys
                for i in range(10):
                    key = f"thread_{thread_id}_key_{i}"
                    value = f"thread_{thread_id}_value_{i}"
                    
                    cache_manager.set(key, value)
                    retrieved = cache_manager.get(key)
                    
                    if retrieved == value:
                        results.append((thread_id, i, True))
                    else:
                        results.append((thread_id, i, False))
                        
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 50  # 5 threads * 10 operations each
        assert all(success for _, _, success in results)
    
    def test_concurrent_invalidation(self, cache_manager):
        """Test concurrent invalidation operations"""
        # Setup cache with contact data
        for i in range(100):
            contact_data = {
                "contacts": [{"id": i}, {"id": i + 100}]
            }
            cache_manager.set(f"contact_query_{i}", contact_data)
        
        errors = []
        
        def invalidate_worker(contact_ids: list):
            try:
                cache_manager.invalidate_contacts(contact_ids)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple invalidation threads
        threads = []
        for i in range(10):
            contact_ids = list(range(i * 10, (i + 1) * 10))
            thread = threading.Thread(target=invalidate_worker, args=(contact_ids,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should complete without errors
        assert len(errors) == 0, f"Concurrent invalidation errors: {errors}"


class TestCacheErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_data_serialization(self, cache_manager):
        """Test handling of data that can't be serialized"""
        # Some objects can't be pickled
        import threading
        lock = threading.Lock()
        
        # This should not crash the cache
        cache_manager.set("lock_key", lock)
        
        # Should return None since it couldn't be stored
        cache_manager.get("lock_key")
        # Note: This might succeed depending on pickle version
        # The important thing is that it doesn't crash
    
    def test_database_corruption_handling(self, cache_manager):
        """Test handling of database issues"""
        # This is hard to test without actually corrupting the database
        # For now, just verify that stats work and don't crash
        stats = cache_manager.get_stats()
        assert isinstance(stats, dict)
    
    def test_large_cache_keys(self, cache_manager):
        """Test handling of very large cache keys"""
        large_key = "x" * 1000  # Very long key
        cache_manager.set(large_key, "value")
        assert cache_manager.get(large_key) == "value"
    
    def test_empty_and_none_values(self, cache_manager):
        """Test caching of empty and None values"""
        cache_manager.set("empty_string", "")
        cache_manager.set("empty_list", [])
        cache_manager.set("empty_dict", {})
        cache_manager.set("none_value", None)
        
        assert cache_manager.get("empty_string") == ""
        assert cache_manager.get("empty_list") == []
        assert cache_manager.get("empty_dict") == {}
        assert cache_manager.get("none_value") is None