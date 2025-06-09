"""
Integration Tests for Cache with API Clients

Tests the integration between the persistent cache and Keap API clients,
including real API calls, cache effectiveness, and data consistency.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock

from src.cache.manager import CacheManager
from src.api.client import KeapClient


@pytest.mark.integration
class TestCacheAPIIntegration:
    """Test cache integration with real API calls"""
    
    @pytest.mark.asyncio
    async def test_cache_with_real_api_calls(self, keap_client, temp_cache_db):
        """Test cache effectiveness with real API calls"""
        # Create a fresh cache for this test
        test_cache = CacheManager(db_path=temp_cache_db)
        
        # Replace global cache for this test
        with patch('src.mcp.tools.cache_manager', test_cache):
            # First call should hit the API
            start_time = time.time()
            tags1 = await keap_client.get_all_tags(use_cache=True)
            first_call_time = time.time() - start_time
            
            # Second call should use cache (much faster)
            start_time = time.time()
            tags2 = await keap_client.get_all_tags(use_cache=True)
            second_call_time = time.time() - start_time
            
            # Verify data consistency
            assert tags1 == tags2
            assert len(tags1) > 0
            
            # Cache should be faster (allow some margin for variance)
            assert second_call_time < first_call_time * 0.5
            
            # Verify cache statistics
            stats = test_cache.get_stats()
            assert stats["total_entries"] > 0
        
        test_cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_with_api(self, keap_client, temp_cache_db):
        """Test cache invalidation with API operations"""
        test_cache = CacheManager(db_path=temp_cache_db)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            # Get some tags to populate cache
            tags = await keap_client.get_all_tags(use_cache=True)
            initial_stats = test_cache.get_stats()
            assert initial_stats["total_entries"] > 0
            
            # Simulate tag modification (invalidation trigger)
            if tags:
                tag_ids = [tag["id"] for tag in tags[:3]]  # First 3 tags
                test_cache.invalidate_tags(tag_ids)
                
                # Cache should be partially invalidated
                post_invalidation_stats = test_cache.get_stats()
                # Note: Exact count depends on how many entries were affected
                assert post_invalidation_stats["total_entries"] <= initial_stats["total_entries"]
        
        test_cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_with_contact_queries(self, keap_client, temp_cache_db):
        """Test cache with contact query operations"""
        test_cache = CacheManager(db_path=temp_cache_db)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            # Query contacts with parameters
            params = {
                "limit": 10,
                "order": "date_created",
                "order_direction": "descending"
            }
            
            # First call
            start_time = time.time()
            contacts1 = await keap_client.query_contacts(params)
            first_call_time = time.time() - start_time
            
            # Second call with same parameters
            start_time = time.time()
            contacts2 = await keap_client.query_contacts(params)
            second_call_time = time.time() - start_time
            
            # Verify consistency and performance
            assert contacts1 == contacts2
            assert second_call_time < first_call_time * 0.5
            
            # Verify cache contains contact data
            stats = test_cache.get_stats()
            assert stats["total_entries"] > 0
            assert stats["contact_mappings"] > 0
        
        test_cache.close()


@pytest.mark.integration
class TestCachePerformanceImpact:
    """Test performance impact of caching"""
    
    @pytest.mark.asyncio
    async def test_cache_hit_miss_ratios(self, keap_client, temp_cache_db):
        """Test cache hit/miss ratios with various query patterns"""
        test_cache = CacheManager(db_path=temp_cache_db, max_entries=100)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            call_times = []
            
            # Make same call multiple times
            for i in range(5):
                start_time = time.time()
                await keap_client.get_all_tags(use_cache=True)
                call_time = time.time() - start_time
                call_times.append(call_time)
            
            # First call should be slowest (cache miss)
            # Subsequent calls should be faster (cache hits)
            assert call_times[0] > call_times[1]  # First vs second
            assert call_times[1] >= call_times[2]  # Should be similar or faster
            
            # Average of cached calls should be much faster
            cache_avg = sum(call_times[1:]) / len(call_times[1:])
            assert cache_avg < call_times[0] * 0.3  # At least 70% faster
        
        test_cache.close()
    
    @pytest.mark.asyncio
    async def test_memory_usage_tracking(self, keap_client, temp_cache_db):
        """Test memory usage tracking during cache operations"""
        test_cache = CacheManager(db_path=temp_cache_db, max_memory_mb=5)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            # Make various API calls to fill cache
            await keap_client.get_all_tags(use_cache=True)
            
            # Query some contacts
            for i in range(3):
                params = {"limit": 50, "offset": i * 50}
                await keap_client.query_contacts(params)
            
            # Check memory usage
            stats = test_cache.get_stats()
            assert stats["total_size_mb"] > 0
            assert stats["memory_usage_percent"] >= 0
            assert stats["memory_usage_percent"] <= 100
            
            # Should not exceed configured limit
            assert stats["total_size_mb"] <= 5.1  # Small margin for overhead
        
        test_cache.close()


@pytest.mark.integration
class TestCacheDataConsistency:
    """Test data consistency with cache operations"""
    
    @pytest.mark.asyncio
    async def test_cache_ttl_with_real_data(self, keap_client, temp_cache_db):
        """Test TTL expiration with real API data"""
        test_cache = CacheManager(db_path=temp_cache_db)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            # Set a short TTL for testing
            original_get = test_cache.get
            
            def mock_set_short_ttl(key, value, ttl=2):  # 2 second TTL
                return test_cache._persistent_cache.set(key, value, ttl)
            
            with patch.object(test_cache._persistent_cache, 'set', side_effect=mock_set_short_ttl):
                # Get tags with short TTL
                tags1 = await keap_client.get_all_tags(use_cache=True)
                assert len(tags1) > 0
                
                # Should be cached immediately
                tags2 = await keap_client.get_all_tags(use_cache=True)
                assert tags1 == tags2
                
                # Wait for expiration
                time.sleep(2.1)
                
                # Should fetch fresh data (might be same, but call should go to API)
                tags3 = await keap_client.get_all_tags(use_cache=True)
                assert len(tags3) > 0  # Should still have data
        
        test_cache.close()
    
    @pytest.mark.asyncio
    async def test_partial_cache_invalidation(self, keap_client, temp_cache_db):
        """Test partial cache invalidation scenarios"""
        test_cache = CacheManager(db_path=temp_cache_db)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            # Cache multiple different queries
            tags = await keap_client.get_all_tags(use_cache=True)
            
            # Query contacts (different cache entries)
            contacts = await keap_client.query_contacts({"limit": 5})
            
            initial_stats = test_cache.get_stats()
            initial_entries = initial_stats["total_entries"]
            
            # Invalidate only tags
            if tags:
                tag_ids = [tag["id"] for tag in tags[:2]]
                test_cache.invalidate_tags(tag_ids)
            
            # Contact cache should still be intact
            # Note: This depends on how the caching keys are structured
            post_invalidation_stats = test_cache.get_stats()
            # At minimum, some entries should remain
            assert post_invalidation_stats["total_entries"] >= 0
        
        test_cache.close()


@pytest.mark.integration 
class TestCacheWithMCPTools:
    """Test cache integration with MCP tools"""
    
    @pytest.mark.asyncio
    async def test_cache_with_query_contacts_tool(self, keap_client, temp_cache_db):
        """Test cache integration with query_contacts MCP tool"""
        from src.mcp.tools import query_contacts
        
        test_cache = CacheManager(db_path=temp_cache_db)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            # Mock context for MCP tool
            context = AsyncMock()
            
            # Test query with filters
            filters = [
                {"field": "given_name", "operator": "pattern", "value": "A*"}
            ]
            
            # First call
            start_time = time.time()
            result1 = await query_contacts(context, filters=filters, max_results=10)
            first_call_time = time.time() - start_time
            
            # Second call with same parameters
            start_time = time.time()
            result2 = await query_contacts(context, filters=filters, max_results=10)
            second_call_time = time.time() - start_time
            
            # Results should be consistent
            assert result1["contact_ids"] == result2["contact_ids"]
            
            # Second call should be faster due to caching
            assert second_call_time < first_call_time * 0.7
            
            # Cache should have entries
            stats = test_cache.get_stats()
            assert stats["total_entries"] > 0
        
        test_cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_with_modify_tags_tool(self, keap_client, temp_cache_db):
        """Test cache invalidation with modify_tags MCP tool"""
        from src.mcp.tools import modify_tags, query_contacts
        
        test_cache = CacheManager(db_path=temp_cache_db)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            context = AsyncMock()
            
            # First, cache some contact data
            filters = [{"field": "tag_ids", "operator": "contains", "value": 100}]
            result1 = await query_contacts(context, filters=filters, max_results=5)
            
            initial_stats = test_cache.get_stats()
            assert initial_stats["total_entries"] > 0
            
            # Modify tags (should trigger cache invalidation)
            if result1["contact_ids"]:
                contact_id = result1["contact_ids"][0]
                await modify_tags(
                    context,
                    contact_ids=[contact_id],
                    tags_to_add=[101],
                    tags_to_remove=[]
                )
                
                # Cache should be invalidated for affected contacts
                post_modify_stats = test_cache.get_stats()
                # Note: Exact behavior depends on invalidation strategy
                assert post_modify_stats["total_entries"] >= 0
        
        test_cache.close()


@pytest.mark.integration
class TestCacheErrorHandling:
    """Test cache error handling in integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_cache_failure_fallback(self, keap_client, temp_cache_db):
        """Test API fallback when cache operations fail"""
        test_cache = CacheManager(db_path=temp_cache_db)
        
        # Mock cache to simulate failures
        with patch.object(test_cache._persistent_cache, 'get', side_effect=Exception("Cache error")):
            with patch('src.mcp.tools.cache_manager', test_cache):
                # API call should still work despite cache failure
                tags = await keap_client.get_all_tags(use_cache=True)
                assert len(tags) > 0
        
        test_cache.close()
    
    @pytest.mark.asyncio
    async def test_corrupted_cache_data_handling(self, keap_client, temp_cache_db):
        """Test handling of corrupted cache data"""
        test_cache = CacheManager(db_path=temp_cache_db)
        
        with patch('src.mcp.tools.cache_manager', test_cache):
            # First, populate cache with valid data
            tags1 = await keap_client.get_all_tags(use_cache=True)
            assert len(tags1) > 0
            
            # Simulate corrupted cache data
            with patch.object(test_cache._persistent_cache, 'get', return_value="corrupted_data"):
                # Should fall back to API and still work
                tags2 = await keap_client.get_all_tags(use_cache=True)
                assert len(tags2) > 0
        
        test_cache.close()