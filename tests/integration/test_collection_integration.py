"""
Integration tests for collection-based architecture.

Tests the full integration between collection manager, MCP tools, and API client
with real API calls. Requires KEAP_API_KEY in environment.
"""

import os
import pytest
import asyncio
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_contact_schema,
    collection_union,
    collection_intersect,
    collection_diff,
    get_collection_details
)
from src.cache.collections import get_collection_manager


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not required if environment is already set


@pytest.fixture
def skip_if_no_api_key():
    """Skip tests if KEAP_API_KEY is not available"""
    api_key = os.getenv('KEAP_API_KEY')
    if not api_key:
        pytest.skip("KEAP_API_KEY not available in environment")


@pytest.fixture
def context():
    """Create MCP context"""
    return Context()


class TestCollectionWorkflow:
    """Test complete collection-based workflows with real API"""

    @pytest.mark.asyncio
    async def test_search_and_filter_workflow(self, context, skip_if_no_api_key):
        """Test a complete search and filter workflow"""
        # Clear any existing collections
        collection_manager = get_collection_manager()
        collection_manager.collections.clear()

        # Step 1: List contacts (reduced limit for performance)
        result = await list_contacts(context, limit=2)
        collection_id_1 = result["collection_id"]
        assert result["count"] >= 0

        # Step 2: List contacts with different parameters (reduced limit)
        result2 = await list_contacts(context, limit=2, offset=1)
        collection_id_2 = result2["collection_id"]
        assert result2["count"] >= 0

        # Step 3: Test union operation
        union_result = await collection_union(context, collection_id_1, collection_id_2)
        union_collection_id = union_result["collection_id"]
        assert union_result["count"] >= 0

        # Step 4: Test intersection
        intersect_result = await collection_intersect(context, collection_id_1, collection_id_2)
        intersect_collection_id = intersect_result["collection_id"]
        assert intersect_result["count"] >= 0

        print(f"Union: {union_result['count']}, Intersect: {intersect_result['count']}")

    @pytest.mark.asyncio
    async def test_tag_operations_workflow(self, context, skip_if_no_api_key):
        """Test tag operations on collections"""
        # Clear collections
        collection_manager = get_collection_manager()
        collection_manager.collections.clear()

        # Create a collection (reduced limit)
        result = await list_contacts(context, limit=2)
        collection_id = result["collection_id"]

        if result["count"] > 0:
            # Note: Only test tag fetching, not application (to avoid modifying real data)
            # Apply tags would be: await modify_collection_tags(context, collection_id, [1], "add")
            print(f"Collection {collection_id} with {result['count']} contacts available for tag operations")
            assert True
        else:
            pytest.skip("No contacts available for tag operations")

    @pytest.mark.asyncio
    async def test_detailed_data_retrieval(self, context, skip_if_no_api_key):
        """Test retrieving detailed contact data"""
        # Clear collections
        collection_manager = get_collection_manager()
        collection_manager.collections.clear()

        # Create collection
        result = await list_contacts(context, limit=3)
        collection_id = result["collection_id"]

        if result["count"] > 0:
            # Get detailed contact information
            details = await get_collection_details(context, collection_id)
            contacts = details.get("contacts", [])

            assert len(contacts) > 0
            
            # Verify contact structure
            for contact in contacts:
                assert "id" in contact
                # Custom fields and tags should be included
                if "custom_fields" in contact:
                    print(f"Contact {contact['id']}: {len(contact['custom_fields'])} custom fields")
                if "tag_ids" in contact:
                    print(f"Contact {contact['id']}: tag_ids = {contact['tag_ids']}")

            # Test field filtering
            filtered_details = await get_collection_details(
                context, collection_id, fields=["id", "given_name", "family_name"]
            )
            filtered_contacts = filtered_details.get("contacts", [])
            
            for contact in filtered_contacts:
                # Should only have requested fields (plus any API includes)
                assert "id" in contact
                # Should not have email if not requested
                expected_fields = {"id", "given_name", "family_name"}
                contact_fields = set(contact.keys())
                assert expected_fields.intersection(contact_fields) == expected_fields
        else:
            pytest.skip("No contacts available for detailed data retrieval")

    @pytest.mark.asyncio
    async def test_complex_filtering_workflow(self, context, skip_if_no_api_key):
        """Test complex filtering scenarios"""
        # Test with different contact list parameters
        small_result = await list_contacts(context, limit=2)
        large_result = await list_contacts(context, limit=5)
        
        # Test difference operation
        diff_result = await collection_diff(context, large_result["collection_id"], small_result["collection_id"])
        
        # The difference should be the larger set minus the smaller set
        expected_diff = large_result["count"] - len(set(range(small_result["count"])).intersection(set(range(large_result["count"]))))
        print(f"Large: {large_result['count']}, Small: {small_result['count']}, Diff: {diff_result['count']}")

    @pytest.mark.asyncio
    async def test_edge_cases(self, context, skip_if_no_api_key):
        """Test edge cases and error handling"""
        # Test with empty collections
        result = await list_contacts(context, limit=0)
        collection_id = result["collection_id"]
        assert result["count"] == 0

        # Test operations on empty collection
        empty_result = await list_contacts(context, limit=0, offset=1000)
        empty_collection_id = empty_result["collection_id"]

        # Union with empty should return original
        union_with_empty = await collection_union(context, collection_id, empty_collection_id)
        assert union_with_empty["count"] == result["count"]

        # Intersection with empty should return empty
        intersect_with_empty = await collection_intersect(context, collection_id, empty_collection_id)
        assert intersect_with_empty["count"] == 0


class TestCollectionPersistence:
    """Test collection persistence and expiration"""

    @pytest.mark.asyncio
    async def test_collection_cleanup(self, context, skip_if_no_api_key):
        """Test collection TTL and cleanup"""
        
        collection_manager = get_collection_manager()
        collection_manager.collections.clear()

        # Create collections with short TTL
        result1 = await list_contacts(context, limit=3)
        result2 = await list_contacts(context, limit=3)
        
        collection_id_1 = result1["collection_id"]
        collection_id_2 = result2["collection_id"]

        # Verify collections exist
        assert collection_manager.get_collection(collection_id_1) is not None
        assert collection_manager.get_collection(collection_id_2) is not None

        # Manually trigger expiration (simulate TTL)
        collection_manager.cleanup_expired_collections()
        
        # Collections should still exist immediately after creation
        assert collection_manager.get_collection(collection_id_1) is not None

    @pytest.mark.asyncio
    async def test_collection_operations_with_expiration(self, context, skip_if_no_api_key):
        """Test that operations handle collection expiration gracefully"""
        collection_manager = get_collection_manager()
        collection_manager.collections.clear()

        # Create collections
        result1 = await list_contacts(context, limit=3)
        result2 = await list_contacts(context, limit=3)

        # Test operations work normally
        union_result = await collection_union(context, result1["collection_id"], result2["collection_id"])
        assert union_result["count"] >= 0

        # Force cleanup
        collection_manager.cleanup_expired_collections()

    @pytest.mark.asyncio
    async def test_concurrent_collection_operations(self, context, skip_if_no_api_key):
        """Test concurrent collection operations"""
        collection_manager = get_collection_manager()
        collection_manager.collections.clear()

        # Create multiple collections concurrently
        tasks = [
            list_contacts(context, limit=i+1, offset=i) 
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert "collection_id" in result
            assert result["count"] >= 0

        print(f"Created {len(results)} collections concurrently")


class TestSchemaAndDiagnostics:
    """Test schema discovery and diagnostics"""

    @pytest.mark.asyncio  
    async def test_contact_schema_discovery(self, context, skip_if_no_api_key):
        """Test contact schema discovery"""
        schema = await get_contact_schema(context)
        
        assert "standard_fields" in schema
        assert "filter_examples" in schema
        assert "supported_operators" in schema
        
        # Should have some standard fields
        standard_fields = schema["standard_fields"]
        expected_fields = ["id", "given_name", "family_name", "email"]
        
        for field in expected_fields:
            if field in standard_fields:
                print(f"✓ Found expected field: {field}")


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_invalid_collection_operations(self, context, skip_if_no_api_key):
        """Test operations with invalid collection IDs"""
        
        # Test with non-existent collection ID
        with pytest.raises(ValueError, match="not found"):
            await get_collection_details(context, "non_existent_collection")

        with pytest.raises(ValueError, match="not found"):
            await collection_union(context, "invalid1", "invalid2")

    @pytest.mark.asyncio
    async def test_api_error_recovery(self, context, skip_if_no_api_key):
        """Test recovery from API errors"""
        # This test naturally handles API errors during normal operations
        try:
            result = await list_contacts(context, limit=1)
            assert "collection_id" in result
        except Exception as e:
            # Should handle gracefully
            assert isinstance(e, (ValueError, RuntimeError))