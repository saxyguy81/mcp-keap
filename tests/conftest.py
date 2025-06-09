"""
Test Configuration and Fixtures

Provides shared fixtures and configuration for comprehensive testing
of the Keap MCP Server with real API credentials.
"""

import os
import pytest
import asyncio
import tempfile
import sqlite3
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch

from src.cache.manager import CacheManager
from src.api.client import KeapApiService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration from environment variables"""
    config = {
        "api_key": os.environ.get("KEAP_API_KEY"),
        "base_url": os.environ.get("KEAP_API_BASE_URL", "https://api.infusionsoft.com/crm/rest/v1"),
        "timeout": 30,
        "max_retries": 3
    }
    
    if not config["api_key"]:
        pytest.skip("KEAP_API_KEY not found in environment variables")
    
    return config


@pytest.fixture
def temp_cache_db():
    """Create a temporary SQLite database for cache testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def cache_manager(temp_cache_db):
    """Create a cache manager for testing"""
    cache = CacheManager(db_path=temp_cache_db)
    
    yield cache
    
    # Cleanup if needed
    try:
        cache.close()
    except AttributeError:
        pass


@pytest.fixture
def keap_client(test_config):
    """Create a Keap API client with real credentials"""
    client = KeapApiService(api_key=test_config["api_key"])
    
    yield client
    
    # Cleanup
    try:
        asyncio.create_task(client.close())
    except AttributeError:
        pass


@pytest.fixture
def v2_client(test_config):
    """Create a V2 API client with real credentials"""
    client = KeapApiService(api_key=test_config["api_key"], api_version="v2")
    
    yield client
    
    # Cleanup
    try:
        asyncio.create_task(client.close())
    except AttributeError:
        pass


@pytest.fixture
def mock_keap_client():
    """Create a mock Keap client for unit testing"""
    client = AsyncMock(spec=KeapApiService)
    
    # Default mock responses
    client.query_contacts.return_value = {
        "contacts": [
            {
                "id": 1,
                "given_name": "John",
                "family_name": "Doe",
                "email_addresses": [{"email": "john@example.com"}]
            }
        ],
        "count": 1
    }
    
    client.get_all_tags.return_value = [
        {"id": 100, "name": "Customer", "description": "Customer tag"}
    ]
    
    return client


@pytest.fixture
def sample_contacts():
    """Sample contact data for testing"""
    return [
        {
            "id": 1,
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [{"email": "john@example.com"}],
            "phone_numbers": [{"number": "555-1234"}],
            "tag_ids": [100, 101]
        },
        {
            "id": 2,
            "given_name": "Jane",
            "family_name": "Smith",
            "email_addresses": [{"email": "jane@example.com"}],
            "tag_ids": [100, 102]
        }
    ]


@pytest.fixture
def sample_tags():
    """Sample tag data for testing"""
    return [
        {"id": 100, "name": "Customer", "description": "Customer tag", "category": {"id": 1, "name": "Status"}},
        {"id": 101, "name": "VIP", "description": "VIP customer tag", "category": {"id": 1, "name": "Status"}},
        {"id": 102, "name": "Newsletter", "description": "Newsletter subscriber", "category": {"id": 2, "name": "Marketing"}}
    ]


@pytest.fixture
def sample_filters():
    """Sample filter configurations for testing"""
    return {
        "simple_name_filter": [
            {"field": "given_name", "operator": "=", "value": "John"}
        ],
        "email_pattern_filter": [
            {"field": "email", "operator": "pattern", "value": "*@example.com"}
        ],
        "tag_filter": [
            {"field": "tag_ids", "operator": "contains", "value": 100}
        ],
        "date_range_filter": [
            {"field": "date_created", "operator": ">=", "value": "2024-01-01T00:00:00"},
            {"field": "date_created", "operator": "<=", "value": "2024-12-31T23:59:59"}
        ],
        "complex_filter": [
            {
                "type": "group",
                "operator": "AND",
                "filters": [
                    {"field": "given_name", "operator": "pattern", "value": "J*"},
                    {
                        "type": "group",
                        "operator": "OR",
                        "filters": [
                            {"field": "tag_ids", "operator": "contains", "value": 100},
                            {"field": "tag_ids", "operator": "contains", "value": 101}
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def api_call_tracker():
    """Track API calls for performance testing"""
    tracker = {
        "calls": [],
        "total_calls": 0,
        "endpoints": {}
    }
    
    def track_call(method: str, endpoint: str, params: Dict[str, Any] = None):
        call = {
            "method": method,
            "endpoint": endpoint,
            "params": params or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        tracker["calls"].append(call)
        tracker["total_calls"] += 1
        
        if endpoint not in tracker["endpoints"]:
            tracker["endpoints"][endpoint] = 0
        tracker["endpoints"][endpoint] += 1
    
    tracker["track"] = track_call
    return tracker


@pytest.fixture(autouse=True)
def cleanup_test_cache():
    """Automatically cleanup test cache files after each test"""
    yield
    
    # Clean up any cache files created during testing
    for cache_file in Path(".").glob("test_*.db"):
        try:
            cache_file.unlink()
        except OSError:
            pass


class TestHelpers:
    """Helper functions for testing"""
    
    @staticmethod
    def create_test_cache_entry(cache: CacheManager, key: str, value: Any, ttl: int = 3600):
        """Helper to create a test cache entry"""
        cache.set(key, value, ttl)
        return key
    
    @staticmethod
    def verify_cache_stats(cache: CacheManager, expected_entries: int = None):
        """Helper to verify cache statistics"""
        try:
            stats = cache.get_stats()
            assert "total_entries" in stats or "cache_hits" in stats
            
            if expected_entries is not None and "total_entries" in stats:
                assert stats["total_entries"] == expected_entries
            
            return stats
        except AttributeError:
            # Simple cache manager might not have stats
            return {"status": "simple_cache"}
    
    @staticmethod
    async def run_api_call_with_tracking(client, method_name: str, *args, tracker=None, **kwargs):
        """Helper to run API call with tracking"""
        if tracker:
            start_calls = tracker["total_calls"]
        
        method = getattr(client, method_name)
        result = await method(*args, **kwargs)
        
        if tracker:
            calls_made = tracker["total_calls"] - start_calls
            return result, calls_made
        
        return result


@pytest.fixture
def test_helpers():
    """Provide test helper functions"""
    return TestHelpers


# Performance testing markers
performance_test = pytest.mark.performance
integration_test = pytest.mark.integration
unit_test = pytest.mark.unit
security_test = pytest.mark.security


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location"""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)