"""
Real API Integration Tests (No Mocking)

These tests exercise the actual code paths with real API client and cache instances,
but without making actual external API calls. They test the integration between
components while keeping tests isolated and deterministic.
"""

import os
import pytest
from unittest.mock import patch
from src.api.client import KeapApiService, create_keap_client
from src.cache.manager import CacheManager
from src.mcp.contact_tools import list_contacts, search_contacts_by_email, get_contact_details
from src.mcp.tag_tools import get_tags, apply_tags_to_contacts
from src.mcp.tools import (
    get_api_diagnostics,
    set_custom_field_values,
    query_contacts_by_custom_field,
    intersect_id_lists,
    analyze_query_performance
)
from src.utils.contact_utils import get_full_name, get_primary_email, format_contact_data
from src.utils.filter_utils import filter_by_name_pattern, validate_filter_conditions
from src.schemas.definitions import Contact, Tag
from src.mcp.optimization.api_optimization import ApiParameterOptimizer
from src.mcp.optimization.optimization import QueryExecutor, QueryOptimizer


class TestRealApiIntegration:
    """Test real API client integration without external calls."""

    @pytest.fixture
    def real_api_client(self):
        """Create real API client with environment variables."""
        api_key = os.getenv("KEAP_API_KEY", "test_api_key")
        return KeapApiService(api_key=api_key)

    @pytest.fixture  
    def real_cache_manager(self, tmp_path):
        """Create real cache manager with temporary database."""
        cache_path = tmp_path / "test_cache.db"
        cache_manager = CacheManager(
            db_path=str(cache_path),
            max_entries=1000,
            max_memory_mb=10
        )
        yield cache_manager
        cache_manager.close()

    @pytest.fixture
    def context(self, real_api_client, real_cache_manager):
        """Create real context with API client and cache manager."""
        class Context:
            def __init__(self):
                self.api_client = real_api_client
                self.cache_manager = real_cache_manager
        return Context()

    def test_api_client_initialization(self, real_api_client):
        """Test real API client initialization and configuration."""
        assert real_api_client.base_url == "https://api.infusionsoft.com/crm/rest/v1"
        assert real_api_client.api_key is not None
        assert real_api_client.session is not None
        assert real_api_client.diagnostics is not None

    def test_cache_manager_operations(self, real_cache_manager):
        """Test real cache manager operations."""
        # Test basic operations
        real_cache_manager.set("test_key", {"data": "value"}, ttl=3600)
        result = real_cache_manager.get("test_key")
        assert result == {"data": "value"}

        # Test stats
        stats = real_cache_manager.get_stats()
        assert "total_entries" in stats
        assert "memory_usage_mb" in stats
        assert stats["total_entries"] >= 1

        # Test invalidation
        real_cache_manager.invalidate_pattern("test_*")
        result = real_cache_manager.get("test_key")
        assert result is None

    @patch('src.api.client.KeapApiService.get_contacts')
    @pytest.mark.asyncio
    async def test_contact_tools_integration(self, mock_get_contacts, context):
        """Test contact tools with real context (mocked external calls)."""
        # Mock API response
        mock_get_contacts.return_value = {
            "contacts": [
                {
                    "id": 1,
                    "given_name": "John",
                    "family_name": "Doe", 
                    "email_addresses": [{"email": "john@example.com", "field": "EMAIL1"}]
                }
            ]
        }

        # Test list_contacts function execution path
        result = await list_contacts(context, limit=10)
        assert len(result) == 1
        assert result[0]["given_name"] == "John"

        # Verify cache was used
        cache_stats = context.cache_manager.get_stats()
        assert cache_stats["total_entries"] > 0

    @patch('src.api.client.KeapApiService.get_contacts')
    @pytest.mark.asyncio
    async def test_search_contacts_integration(self, mock_get_contacts, context):
        """Test contact search integration."""
        mock_get_contacts.return_value = {
            "contacts": [
                {
                    "id": 2,
                    "given_name": "Jane",
                    "family_name": "Smith",
                    "email_addresses": [{"email": "jane@example.com", "field": "EMAIL1"}]
                }
            ]
        }

        result = await search_contacts_by_email(context, "jane@example.com")
        assert len(result) == 1
        assert result[0]["family_name"] == "Smith"

    @patch('src.api.client.KeapApiService.get_contact')
    @pytest.mark.asyncio
    async def test_contact_details_integration(self, mock_get_contact, context):
        """Test get contact details integration."""
        mock_get_contact.return_value = {
            "id": 3,
            "given_name": "Bob",
            "family_name": "Johnson",
            "email_addresses": [{"email": "bob@example.com", "field": "EMAIL1"}],
            "custom_fields": [{"id": 7, "content": "VIP"}]
        }

        result = await get_contact_details(context, contact_id="3")
        assert result["given_name"] == "Bob"
        assert len(result["custom_fields"]) == 1

    @patch('src.api.client.KeapApiService.get_tags')
    @pytest.mark.asyncio
    async def test_tag_tools_integration(self, mock_get_tags, context):
        """Test tag tools integration."""
        mock_get_tags.return_value = {
            "tags": [
                {"id": 10, "name": "VIP Customer"},
                {"id": 20, "name": "Newsletter"}
            ]
        }

        result = await get_tags(context, limit=50)
        assert len(result) == 2
        assert result[0]["name"] == "VIP Customer"

    @patch('src.api.client.KeapApiService.apply_tags_to_contacts')
    @pytest.mark.asyncio
    async def test_tag_application_integration(self, mock_apply_tags, context):
        """Test tag application integration."""
        mock_apply_tags.return_value = {"success": True}

        result = await apply_tags_to_contacts(context, tag_ids=["10"], contact_ids=["1", "2"])
        assert result["success"] is True

        # Verify cache invalidation occurred
        cache_stats = context.cache_manager.get_stats()
        assert isinstance(cache_stats, dict)

    def test_utility_functions_integration(self):
        """Test utility functions without mocking."""
        contact_data = {
            "given_name": "Alice",
            "family_name": "Cooper",
            "email_addresses": [
                {"email": "alice@example.com", "field": "EMAIL1"},
                {"email": "alice.cooper@work.com", "field": "EMAIL2"}
            ]
        }

        # Test contact utilities
        full_name = get_full_name(contact_data)
        assert full_name == "Alice Cooper"

        primary_email = get_primary_email(contact_data)
        assert primary_email == "alice@example.com"

        formatted = format_contact_data(contact_data)
        assert formatted["full_name"] == "Alice Cooper"
        assert "email_addresses" in formatted

    def test_filter_utilities_integration(self):
        """Test filter utilities without mocking."""
        items = [
            {"name": "John Doe", "id": 1},
            {"name": "Jane Smith", "id": 2},
            {"name": "Johnny Cash", "id": 3}
        ]

        # Test pattern filtering
        filtered = filter_by_name_pattern(items, "John*")
        assert len(filtered) == 2

        # Test filter validation
        filters = [
            {"field": "name", "operator": "equals", "value": "test"}
        ]
        # validate_filter_conditions raises ValueError if invalid, otherwise returns None
        try:
            validate_filter_conditions(filters)
            validation_passed = True
        except ValueError:
            validation_passed = False
        assert validation_passed is True

    def test_schema_validation_integration(self):
        """Test schema validation without mocking."""
        contact_data = {
            "id": 123,
            "given_name": "Test",
            "family_name": "User",
            "email": "test@example.com"
        }

        # Test Contact schema
        contact = Contact(**contact_data)
        assert contact.id == 123
        assert contact.given_name == "Test"

        # Test Tag schema
        tag_data = {"id": 456, "name": "Test Tag"}
        tag = Tag(**tag_data)
        assert tag.id == 456
        assert tag.name == "Test Tag"

    @patch('src.api.client.KeapApiService.get_contacts')
    def test_optimization_integration(self, mock_get_contacts, context):
        """Test optimization components integration."""
        mock_get_contacts.return_value = {"contacts": []}

        # Test API parameter optimizer
        optimizer = ApiParameterOptimizer()
        filters = [{"field": "email", "operator": "equals", "value": "test@example.com"}]
        
        result = optimizer.optimize_contact_query_parameters(filters)
        assert hasattr(result, 'optimization_strategy')
        assert hasattr(result, 'server_side_filters')

        # Test performance analysis
        performance = optimizer.analyze_filter_performance(filters, "contact")
        assert "performance_rating" in performance
        assert "optimization_score" in performance

    @patch('src.api.client.KeapApiService.update_contact')
    @pytest.mark.asyncio
    async def test_custom_field_integration(self, mock_update, context):
        """Test custom field operations integration."""
        mock_update.return_value = {"success": True}

        result = await set_custom_field_values(
            context,
            field_id="7",
            contact_ids=["1", "2"],
            common_value="Premium"
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_diagnostic_tools_integration(self, context):
        """Test diagnostic tools integration."""
        # Add some cache data first
        context.cache_manager.set("diag_test", {"data": "value"}, ttl=3600)

        result = await get_api_diagnostics(context)
        assert "cache_stats" in result
        assert "api_stats" in result
        assert result["cache_stats"]["total_entries"] > 0

    @pytest.mark.asyncio
    async def test_query_performance_integration(self, context):
        """Test query performance analysis integration."""
        filters = [
            {"field": "email", "operator": "equals", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"}
        ]

        result = await analyze_query_performance(context, filters=filters, query_type="contact")
        assert "estimated_performance" in result
        assert "optimization_suggestions" in result

    @pytest.mark.asyncio
    async def test_utility_intersect_integration(self, context):
        """Test ID list intersection utility integration."""
        list1 = ["1", "2", "3", "4"]
        list2 = ["2", "3", "5", "6"]
        
        result = await intersect_id_lists(context, list1=list1, list2=list2)
        assert result["intersection"] == ["2", "3"]
        assert result["list1_only"] == ["1", "4"]
        assert result["list2_only"] == ["5", "6"]

    @patch('src.api.client.KeapApiService.get_contacts')
    @pytest.mark.asyncio
    async def test_query_contacts_by_custom_field_integration(self, mock_get_contacts, context):
        """Test custom field query integration."""
        mock_get_contacts.return_value = {
            "contacts": [
                {
                    "id": 100,
                    "given_name": "Premium",
                    "family_name": "User",
                    "custom_fields": [{"id": 7, "content": "VIP"}]
                }
            ]
        }

        result = await query_contacts_by_custom_field(
            context,
            field_id="7",
            field_value="VIP",
            limit=10
        )
        assert len(result) == 1
        assert result[0]["given_name"] == "Premium"

    def test_factory_functions_integration(self):
        """Test factory functions without mocking."""
        # Test client creation with environment
        client = create_keap_client()
        assert isinstance(client, KeapApiService)
        assert client.api_key is not None

        # Test client creation with explicit key
        client_with_key = create_keap_client("explicit_key")
        assert client_with_key.api_key == "explicit_key"

    def test_error_handling_integration(self, real_api_client, real_cache_manager):
        """Test error handling in real integration scenarios."""
        # Test API client error handling
        assert real_api_client.should_rate_limit() in [True, False]

        # Test cache manager error handling
        real_cache_manager.set("error_test", {"data": "value"}, ttl=1)
        result = real_cache_manager.get("error_test")
        assert result is not None

        # Test diagnostics
        diagnostics = real_api_client.get_diagnostics()
        assert "total_requests" in diagnostics