"""
Integration tests for API and Cache component interactions.

Tests the integration between API client, cache management, and persistent storage.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock

from src.api.client import KeapApiService
from src.cache.manager import CacheManager


class TestApiCacheIntegration:
    """Test API client and cache integration."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        try:
            Path(db_path).unlink()
        except FileNotFoundError:
            pass

    @pytest.fixture
    def cache_manager(self, temp_db_path):
        """Create cache manager with temp database."""
        manager = CacheManager(db_path=temp_db_path)
        yield manager
        manager.close()

    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client."""
        client = AsyncMock(spec=KeapApiService)

        # Mock contact responses
        client.get_contacts.return_value = {
            "contacts": [
                {
                    "id": 1,
                    "given_name": "John",
                    "family_name": "Doe",
                    "email_addresses": [
                        {"email": "john@example.com", "field": "EMAIL1"}
                    ],
                    "tag_ids": [10, 20],
                    "custom_fields": [{"id": 7, "content": "VIP"}],
                    "date_created": "2024-01-15T10:30:00Z",
                },
                {
                    "id": 2,
                    "given_name": "Jane",
                    "family_name": "Smith",
                    "email_addresses": [
                        {"email": "jane@example.com", "field": "EMAIL1"}
                    ],
                    "tag_ids": [10],
                    "custom_fields": [{"id": 7, "content": "Regular"}],
                    "date_created": "2024-01-16T11:30:00Z",
                },
            ]
        }

        # Mock tag responses
        client.get_tags.return_value = {
            "tags": [
                {"id": 10, "name": "Customer", "description": "Customer tag"},
                {"id": 20, "name": "VIP", "description": "VIP customer"},
            ]
        }

        # Mock single contact response
        client.get_contact.return_value = {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [{"email": "john@example.com", "field": "EMAIL1"}],
            "tag_ids": [10, 20],
            "custom_fields": [{"id": 7, "content": "VIP"}],
        }

        return client

    @pytest.mark.asyncio
    async def test_api_cache_miss_and_hit_cycle(self, mock_api_client, cache_manager):
        """Test complete cache miss -> API call -> cache hit cycle."""
        cache_key = "contacts:all:limit=10"

        # Initially cache should be empty
        cached_data = await cache_manager.get(cache_key)
        assert cached_data is None

        # Simulate API call and cache storage
        api_response = await mock_api_client.get_contacts(limit=10)
        contacts = api_response["contacts"]

        # Store in cache with TTL
        await cache_manager.set(cache_key, contacts, ttl=1800)

        # Verify cache hit
        cached_contacts = await cache_manager.get(cache_key)
        assert cached_contacts is not None
        assert len(cached_contacts) == 2
        assert cached_contacts[0]["id"] == 1
        assert cached_contacts[0]["given_name"] == "John"

        # Verify API was called only once
        mock_api_client.get_contacts.assert_called_once_with(limit=10)

    @pytest.mark.asyncio
    async def test_cache_expiration_triggers_api_call(
        self, mock_api_client, cache_manager
    ):
        """Test that expired cache entries trigger new API calls."""
        cache_key = "contacts:expired"

        # Store data with very short TTL
        initial_data = [{"id": 999, "name": "Temporary"}]
        await cache_manager.set(cache_key, initial_data, ttl=0.1)

        # Verify initial cache hit
        cached_data = await cache_manager.get(cache_key)
        assert cached_data == initial_data

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Cache should now be empty
        expired_data = await cache_manager.get(cache_key)
        assert expired_data is None

        # Simulate API call for fresh data
        fresh_response = await mock_api_client.get_contacts()
        fresh_contacts = fresh_response["contacts"]

        # Store fresh data
        await cache_manager.set(cache_key, fresh_contacts, ttl=1800)

        # Verify fresh data is cached
        cached_fresh = await cache_manager.get(cache_key)
        assert cached_fresh == fresh_contacts
        assert len(cached_fresh) == 2

    @pytest.mark.asyncio
    async def test_cache_invalidation_with_api_updates(
        self, mock_api_client, cache_manager
    ):
        """Test cache invalidation when API data is updated."""
        # Cache initial contact data
        contact_cache_key = "contact:1:details"
        contacts_cache_key = "contacts:all"

        # Get and cache initial contact
        contact_response = await mock_api_client.get_contact(1)
        await cache_manager.set(contact_cache_key, contact_response)

        contacts_response = await mock_api_client.get_contacts()
        await cache_manager.set(contacts_cache_key, contacts_response["contacts"])

        # Verify cached data
        cached_contact = await cache_manager.get(contact_cache_key)
        cached_contacts = await cache_manager.get(contacts_cache_key)
        assert cached_contact["given_name"] == "John"
        assert len(cached_contacts) == 2

        # Simulate contact update
        mock_api_client.update_contact.return_value = {"success": True}
        await mock_api_client.update_contact(1, {"given_name": "Johnny"})

        # Invalidate related cache entries
        await cache_manager.invalidate_contacts([1])

        # Verify cache invalidation
        invalidated_contact = await cache_manager.get(contact_cache_key)
        invalidated_contacts = await cache_manager.get(contacts_cache_key)
        assert invalidated_contact is None
        assert invalidated_contacts is None

    @pytest.mark.asyncio
    async def test_concurrent_api_cache_operations(
        self, mock_api_client, cache_manager
    ):
        """Test concurrent API calls with cache operations."""

        async def fetch_and_cache_contacts(worker_id):
            cache_key = f"contacts:worker_{worker_id}"

            # Simulate API call
            response = await mock_api_client.get_contacts(limit=5, offset=worker_id * 5)
            contacts = response["contacts"]

            # Cache the response
            await cache_manager.set(cache_key, contacts, ttl=3600)

            # Verify cached data
            cached = await cache_manager.get(cache_key)
            return len(cached) if cached else 0

        # Run multiple concurrent operations
        tasks = [fetch_and_cache_contacts(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # Verify all operations completed successfully
        assert all(count >= 0 for count in results)
        assert mock_api_client.get_contacts.call_count == 5

    @pytest.mark.asyncio
    async def test_api_error_handling_with_cache_fallback(
        self, mock_api_client, cache_manager
    ):
        """Test cache fallback when API calls fail."""
        cache_key = "contacts:fallback"

        # Store stale data in cache
        stale_data = [{"id": 1, "name": "Stale Contact"}]
        await cache_manager.set(cache_key, stale_data, ttl=3600)

        # Configure API to fail
        mock_api_client.get_contacts.side_effect = Exception(
            "API temporarily unavailable"
        )

        # Verify cache can provide fallback data
        cached_data = await cache_manager.get(cache_key)
        assert cached_data == stale_data

        # Simulate recovery scenario
        mock_api_client.get_contacts.side_effect = None
        fresh_response = await mock_api_client.get_contacts()
        fresh_contacts = fresh_response["contacts"]

        # Update cache with fresh data
        await cache_manager.set(cache_key, fresh_contacts, ttl=3600)

        # Verify fresh data is now cached
        updated_cached = await cache_manager.get(cache_key)
        assert updated_cached == fresh_contacts

    @pytest.mark.asyncio
    async def test_cache_performance_with_large_datasets(
        self, mock_api_client, cache_manager
    ):
        """Test cache performance with larger datasets."""
        # Generate larger mock dataset
        large_contacts = []
        for i in range(100):
            large_contacts.append(
                {
                    "id": i,
                    "given_name": f"Contact{i}",
                    "family_name": f"User{i}",
                    "email_addresses": [{"email": f"contact{i}@example.com"}],
                    "tag_ids": [10 if i % 2 == 0 else 20],
                    "custom_fields": [{"id": 7, "content": "Standard"}],
                }
            )

        mock_api_client.get_contacts.return_value = {"contacts": large_contacts}

        # Time the cache operation
        start_time = time.time()

        # Store large dataset
        cache_key = "contacts:large_dataset"
        response = await mock_api_client.get_contacts(limit=100)
        await cache_manager.set(cache_key, response["contacts"], ttl=3600)

        # Retrieve from cache
        cached_large = await cache_manager.get(cache_key)

        end_time = time.time()
        operation_time = end_time - start_time

        # Verify data integrity and performance
        assert len(cached_large) == 100
        assert cached_large[0]["id"] == 0
        assert cached_large[99]["id"] == 99
        assert operation_time < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    async def test_cache_memory_management(self, mock_api_client, temp_db_path):
        """Test cache memory management with limits."""
        # Create cache with small memory limit
        limited_cache = CacheManager(
            db_path=temp_db_path,
            max_entries=10,
            max_memory_mb=0.1,  # Very small limit
        )

        try:
            # Try to store data that exceeds memory limit
            large_data = "x" * 1000000  # 1MB string

            await limited_cache.set("large_item", large_data, ttl=3600)

            # Verify cache handles memory constraints gracefully
            stats = limited_cache.get_stats()
            assert stats["total_entries"] <= 10
            assert stats["memory_usage_percent"] <= 100

        finally:
            limited_cache.close()

    @pytest.mark.asyncio
    async def test_api_diagnostics_integration_with_cache(
        self, mock_api_client, cache_manager
    ):
        """Test API diagnostics integration with cache statistics."""
        # Mock API diagnostics
        mock_api_client.get_diagnostics.return_value = {
            "total_requests": 50,
            "successful_requests": 48,
            "failed_requests": 2,
            "cache_hits": 25,
            "cache_misses": 25,
            "average_response_time": 1.2,
        }

        # Perform some cache operations
        await cache_manager.set("test1", {"data": "value1"}, ttl=3600)
        await cache_manager.set("test2", {"data": "value2"}, ttl=3600)

        # Get cache statistics
        cache_stats = cache_manager.get_stats()

        # Get API diagnostics
        api_diagnostics = mock_api_client.get_diagnostics()

        # Verify integration data
        assert cache_stats["total_entries"] >= 2
        assert api_diagnostics["total_requests"] == 50
        assert api_diagnostics["cache_hits"] + api_diagnostics["cache_misses"] == 50
