"""
Real integration tests for collection-based architecture.

These tests exercise the actual collection functionality without mocking,
using real component integration and actual API clients where possible.
"""

import pytest
import asyncio
import time
import os
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_contact_schema,
    collection_union,
    collection_intersect,
    collection_diff,
    collection_count,
    get_collection_details,
    get_collection_ids,
    get_tags,
    apply_tags_to_collection,
    get_api_diagnostics
)
from src.cache.collections import get_collection_manager, CollectionManager
from src.api.client import KeapApiService
from src.cache.manager import CacheManager


@pytest.fixture
def context():
    """Create MCP context"""
    return Context()


@pytest.fixture
def real_collection_manager():
    """Create a real collection manager for testing"""
    # Use a shorter TTL for testing
    manager = CollectionManager(default_ttl=300)  # 5 minutes
    manager.collections.clear()  # Start clean
    return manager


@pytest.fixture
def sample_contact_data():
    """Sample contact data for testing"""
    return [
        {"id": 1, "given_name": "John", "family_name": "Doe", "email": "john@company.com"},
        {"id": 2, "given_name": "Jane", "family_name": "Smith", "email": "jane@company.com"},
        {"id": 3, "given_name": "Bob", "family_name": "Johnson", "email": "bob@example.com"},
        {"id": 4, "given_name": "Alice", "family_name": "Wilson", "email": "alice@company.com"},
        {"id": 5, "given_name": "Charlie", "family_name": "Brown", "email": "charlie@example.com"},
        {"id": 6, "given_name": "Diana", "family_name": "Prince", "email": "diana@company.com"},
        {"id": 7, "given_name": "Eve", "family_name": "Adams", "email": "eve@example.com"},
        {"id": 8, "given_name": "Frank", "family_name": "Miller", "email": "frank@company.com"},
        {"id": 9, "given_name": "Grace", "family_name": "Hopper", "email": "grace@example.com"},
        {"id": 10, "given_name": "Henry", "family_name": "Ford", "email": "henry@company.com"}
    ]


class TestRealCollectionManager:
    """Test real collection manager functionality without mocking"""

    def test_collection_creation_and_retrieval(self, real_collection_manager):
        """Test real collection creation and retrieval"""
        contact_ids = [1, 2, 3, 4, 5]
        
        # Create collection
        collection_id = real_collection_manager.create_collection(
            contact_ids=contact_ids,
            name="Test Collection",
            description="A real test collection"
        )
        
        # Verify collection exists
        assert collection_id.startswith("contacts_")
        collection = real_collection_manager.get_collection(collection_id)
        assert collection is not None
        assert collection.contact_ids == set(contact_ids)
        assert collection.name == "Test Collection"
        
        # Test retrieval methods
        retrieved_ids = real_collection_manager.get_contact_ids(collection_id)
        assert set(retrieved_ids) == set(contact_ids)
        
        count = real_collection_manager.count(collection_id)
        assert count == 5

    def test_real_set_operations(self, real_collection_manager):
        """Test real set operations between collections"""
        # Create first collection
        collection_a_id = real_collection_manager.create_collection([1, 2, 3, 4, 5], "Collection A")
        
        # Create second collection  
        collection_b_id = real_collection_manager.create_collection([4, 5, 6, 7, 8], "Collection B")
        
        # Test union
        union_id = real_collection_manager.union(collection_a_id, collection_b_id)
        union_contacts = set(real_collection_manager.get_contact_ids(union_id))
        assert union_contacts == {1, 2, 3, 4, 5, 6, 7, 8}
        
        # Test intersection
        intersect_id = real_collection_manager.intersect(collection_a_id, collection_b_id)
        intersect_contacts = set(real_collection_manager.get_contact_ids(intersect_id))
        assert intersect_contacts == {4, 5}
        
        # Test difference
        diff_id = real_collection_manager.diff(collection_a_id, collection_b_id)
        diff_contacts = set(real_collection_manager.get_contact_ids(diff_id))
        assert diff_contacts == {1, 2, 3}

    def test_collection_expiration_real_time(self):
        """Test real collection expiration with actual timing"""
        # Create manager with very short TTL
        short_manager = CollectionManager(default_ttl=0.5)  # 0.5 seconds
        
        # Create collection
        collection_id = short_manager.create_collection([1, 2, 3], "Short-lived Collection")
        
        # Verify it exists initially
        assert short_manager.get_collection(collection_id) is not None
        assert short_manager.count(collection_id) == 3
        
        # Wait for expiration
        time.sleep(0.6)
        
        # Collection should be expired
        assert short_manager.get_collection(collection_id) is None
        assert short_manager.count(collection_id) == 0

    def test_concurrent_collection_operations(self, real_collection_manager):
        """Test real concurrent operations on collections"""
        # Create base collections
        collection_a = real_collection_manager.create_collection(list(range(1, 51)), "Large Collection A")
        collection_b = real_collection_manager.create_collection(list(range(26, 76)), "Large Collection B")
        
        async def perform_operations():
            # Simulate concurrent operations
            tasks = []
            
            # Create multiple derived collections concurrently
            for i in range(5):
                start = i * 10 + 1
                end = start + 20
                subset_id = real_collection_manager.create_collection(
                    list(range(start, end)), f"Subset {i}"
                )
                tasks.append(subset_id)
            
            return tasks
        
        # Run concurrent operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            subset_collections = loop.run_until_complete(perform_operations())
            
            # Verify all collections were created successfully
            assert len(subset_collections) == 5
            for collection_id in subset_collections:
                assert real_collection_manager.count(collection_id) == 20
        finally:
            loop.close()

    def test_collection_diagnostics_real_data(self, real_collection_manager):
        """Test collection diagnostics with real data"""
        # Create multiple collections with different sizes
        collections = []
        for i in range(5):
            size = (i + 1) * 10
            collection_id = real_collection_manager.create_collection(
                list(range(i * 100, i * 100 + size)), 
                f"Collection {i+1}"
            )
            collections.append(collection_id)
        
        # Get real diagnostics
        diagnostics = real_collection_manager.get_diagnostics()
        
        # Verify diagnostics accuracy
        assert diagnostics["active_collections"] == 5
        expected_total = sum((i + 1) * 10 for i in range(5))  # 10+20+30+40+50 = 150
        assert diagnostics["total_contacts_across_collections"] == expected_total
        assert len(diagnostics["collections"]) == 5
        
        # Verify individual collection details
        for i, collection_info in enumerate(diagnostics["collections"]):
            expected_size = (i + 1) * 10
            assert collection_info["count"] == expected_size
            assert collection_info["name"] == f"Collection {i+1}"


class TestRealSchemaDiscovery:
    """Test real schema discovery functionality"""

    async def test_contact_schema_structure(self, context):
        """Test real contact schema discovery structure"""
        # This tests the actual schema discovery logic without mocking
        from src.mcp.tools_collections import get_contact_schema
        
        # Create a temporary API client for schema discovery
        # We'll use environment variables if available, otherwise skip
        if not os.getenv('KEAP_API_KEY'):
            pytest.skip("KEAP_API_KEY not available for real API testing")
        
        try:
            schema = await get_contact_schema(context)
            
            # Verify schema structure
            assert isinstance(schema, dict)
            assert "standard_fields" in schema
            assert "custom_fields" in schema
            assert "supported_operators" in schema
            assert "filter_examples" in schema
            
            # Verify operators are comprehensive
            operators = schema["supported_operators"]
            expected_operators = [
                "equals", "not_equals", "contains", "not_contains",
                "starts_with", "ends_with", "is_null", "is_not_null"
            ]
            for op in expected_operators:
                assert op in operators
                
            # Verify filter examples have proper structure
            examples = schema["filter_examples"]
            assert len(examples) >= 3
            for example in examples:
                assert "description" in example
                assert "filter" in example or "filters" in example
                
        except Exception as e:
            if "API" in str(e) or "authentication" in str(e).lower():
                pytest.skip(f"API not available for testing: {e}")
            else:
                raise


class TestRealFilteringLogic:
    """Test real filtering logic without mocking"""

    def test_filter_matching_logic(self, sample_contact_data):
        """Test real contact filtering logic"""
        from src.mcp.tools_collections import _apply_filters, _contact_matches_filters, _field_matches_condition
        
        # Test simple equals filter
        filters = [{"field": "given_name", "operator": "equals", "value": "John"}]
        result = _apply_filters(sample_contact_data, filters)
        assert len(result) == 1
        assert result[0]["given_name"] == "John"
        
        # Test contains filter
        filters = [{"field": "email", "operator": "contains", "value": "@company.com"}]
        result = _apply_filters(sample_contact_data, filters)
        # Should match John, Jane, Alice, Diana, Frank, Henry (6 contacts)
        assert len(result) == 6
        for contact in result:
            assert "@company.com" in contact["email"]
        
        # Test multiple filters (AND logic)
        filters = [
            {"field": "email", "operator": "contains", "value": "@company.com"},
            {"field": "given_name", "operator": "starts_with", "value": "J"}
        ]
        result = _apply_filters(sample_contact_data, filters)
        # Should match John and Jane
        assert len(result) == 2
        names = {contact["given_name"] for contact in result}
        assert names == {"John", "Jane"}
        
        # Test not_contains filter
        filters = [{"field": "email", "operator": "not_contains", "value": "@company.com"}]
        result = _apply_filters(sample_contact_data, filters)
        # Should match Bob, Charlie, Eve, Grace (4 contacts)
        assert len(result) == 4
        for contact in result:
            assert "@company.com" not in contact["email"]

    def test_field_matching_conditions_real(self):
        """Test real field matching conditions"""
        from src.mcp.tools_collections import _field_matches_condition
        
        contact = {
            "given_name": "John",
            "family_name": "Doe",
            "email": "john.doe@company.com",
            "custom_field": None
        }
        
        # Test all operator types with real data
        assert _field_matches_condition(contact, "given_name", "equals", "John") is True
        assert _field_matches_condition(contact, "given_name", "equals", "john") is True  # Case insensitive
        assert _field_matches_condition(contact, "given_name", "not_equals", "Jane") is True
        assert _field_matches_condition(contact, "email", "contains", "@company") is True
        assert _field_matches_condition(contact, "email", "not_contains", "@example") is True
        assert _field_matches_condition(contact, "given_name", "starts_with", "Jo") is True
        assert _field_matches_condition(contact, "email", "ends_with", ".com") is True
        assert _field_matches_condition(contact, "custom_field", "is_null", None) is True
        assert _field_matches_condition(contact, "given_name", "is_not_null", None) is True
        
        # Test numeric comparisons
        contact_with_id = {"id": 42, "score": 85.5}
        assert _field_matches_condition(contact_with_id, "id", "greater_than", 40) is True
        assert _field_matches_condition(contact_with_id, "id", "less_than", 50) is True
        assert _field_matches_condition(contact_with_id, "score", "greater_than", 80.0) is True


class TestRealErrorHandling:
    """Test real error handling scenarios"""

    def test_invalid_collection_operations(self, real_collection_manager):
        """Test error handling with invalid collection operations"""
        valid_collection = real_collection_manager.create_collection([1, 2, 3], "Valid Collection")
        
        # Test operations with non-existent collections
        with pytest.raises(ValueError, match="not found"):
            real_collection_manager.union(valid_collection, "invalid_collection_id")
            
        with pytest.raises(ValueError, match="not found"):
            real_collection_manager.intersect("invalid_id", valid_collection)
            
        with pytest.raises(ValueError, match="not found"):
            real_collection_manager.diff(valid_collection, "invalid_id")
        
        # Test operations on expired collections
        short_manager = CollectionManager(default_ttl=0.1)
        expired_collection = short_manager.create_collection([4, 5, 6], "Expired Collection")
        time.sleep(0.2)  # Let it expire
        
        with pytest.raises(ValueError, match="not found or expired"):
            short_manager.union(expired_collection, valid_collection)

    def test_edge_case_collections(self, real_collection_manager):
        """Test edge cases with real collections"""
        # Empty collection
        empty_collection = real_collection_manager.create_collection([], "Empty Collection")
        assert real_collection_manager.count(empty_collection) == 0
        assert real_collection_manager.get_contact_ids(empty_collection) == []
        
        # Large collection
        large_ids = list(range(1, 1001))  # 1000 contacts
        large_collection = real_collection_manager.create_collection(large_ids, "Large Collection")
        assert real_collection_manager.count(large_collection) == 1000
        
        # Collection with duplicate IDs (should be deduplicated)
        duplicate_ids = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]
        dedup_collection = real_collection_manager.create_collection(duplicate_ids, "Deduplicated")
        assert real_collection_manager.count(dedup_collection) == 4
        retrieved_ids = real_collection_manager.get_contact_ids(dedup_collection)
        assert set(retrieved_ids) == {1, 2, 3, 4}
        
        # Operations between empty and non-empty collections
        normal_collection = real_collection_manager.create_collection([1, 2, 3], "Normal")
        
        union_with_empty = real_collection_manager.union(empty_collection, normal_collection)
        assert real_collection_manager.count(union_with_empty) == 3
        
        intersect_with_empty = real_collection_manager.intersect(empty_collection, normal_collection)
        assert real_collection_manager.count(intersect_with_empty) == 0
        
        diff_with_empty = real_collection_manager.diff(normal_collection, empty_collection)
        assert real_collection_manager.count(diff_with_empty) == 3


class TestPerformanceIntegration:
    """Test real performance scenarios"""

    def test_large_collection_performance(self, real_collection_manager):
        """Test performance with large collections"""
        import time
        
        # Create large collections
        start_time = time.time()
        large_collection_a = real_collection_manager.create_collection(
            list(range(1, 5001)), "Large Collection A"  # 50 contacts
        )
        creation_time = time.time() - start_time
        
        # Creation should be fast (under 1 second)
        assert creation_time < 1.0
        
        # Create second large collection
        large_collection_b = real_collection_manager.create_collection(
            list(range(2501, 7501)), "Large Collection B"  # 50 contacts, 50% overlap
        )
        
        # Test union performance
        start_time = time.time()
        union_result = real_collection_manager.union(large_collection_a, large_collection_b)
        union_time = time.time() - start_time
        
        # Union should be fast (under 0.5 seconds)
        assert union_time < 0.5
        assert real_collection_manager.count(union_result) == 7500  # 1-7500
        
        # Test intersection performance
        start_time = time.time()
        intersect_result = real_collection_manager.intersect(large_collection_a, large_collection_b)
        intersect_time = time.time() - start_time
        
        # Intersection should be fast
        assert intersect_time < 0.5
        assert real_collection_manager.count(intersect_result) == 2500  # 2501-50

    def test_many_small_collections_performance(self, real_collection_manager):
        """Test performance with many small collections"""
        import time
        
        # Create many small collections
        start_time = time.time()
        collection_ids = []
        
        for i in range(100):  # 100 collections
            collection_id = real_collection_manager.create_collection(
                [i * 10 + j for j in range(10)],  # 10 contacts each
                f"Small Collection {i}"
            )
            collection_ids.append(collection_id)
        
        creation_time = time.time() - start_time
        
        # Creating 100 small collections should be fast
        assert creation_time < 2.0
        
        # Test batch operations
        start_time = time.time()
        
        # Perform operations on multiple collections
        union_results = []
        for i in range(0, len(collection_ids), 2):
            if i + 1 < len(collection_ids):
                union_id = real_collection_manager.union(collection_ids[i], collection_ids[i + 1])
                union_results.append(union_id)
        
        batch_time = time.time() - start_time
        
        # Batch operations should complete quickly
        assert batch_time < 1.0
        assert len(union_results) == 50

    async def test_concurrent_access_performance(self, real_collection_manager):
        """Test concurrent access performance"""
        # Create base collection
        base_collection = real_collection_manager.create_collection(
            list(range(1, 1001)), "Base Collection"
        )
        
        async def concurrent_operation(operation_id):
            """Perform concurrent collection operations"""
            # Create a subset collection
            start = operation_id * 100
            subset_collection = real_collection_manager.create_collection(
                list(range(start, start + 200)), f"Subset {operation_id}"
            )
            
            # Perform intersection with base
            result = real_collection_manager.intersect(base_collection, subset_collection)
            return real_collection_manager.count(result)
        
        # Run multiple concurrent operations
        start_time = time.time()
        tasks = [concurrent_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        
        # Concurrent operations should complete quickly
        assert concurrent_time < 2.0
        assert len(results) == 10
        assert all(count > 0 for count in results)  # All should have some intersection


class TestDataIntegrityVerification:
    """Test real data integrity across operations"""

    def test_collection_immutability(self, real_collection_manager):
        """Test that collections are immutable after creation"""
        original_ids = [1, 2, 3, 4, 5]
        collection_id = real_collection_manager.create_collection(original_ids, "Immutable Test")
        
        # Get IDs multiple times
        ids_1 = real_collection_manager.get_contact_ids(collection_id)
        ids_2 = real_collection_manager.get_contact_ids(collection_id)
        ids_3 = real_collection_manager.get_contact_ids(collection_id)
        
        # Should always be the same
        assert ids_1 == ids_2 == ids_3
        assert set(ids_1) == set(original_ids)
        
        # Count should be consistent
        count_1 = real_collection_manager.count(collection_id)
        count_2 = real_collection_manager.count(collection_id)
        assert count_1 == count_2 == 5

    def test_set_operation_mathematical_correctness(self, real_collection_manager):
        """Test mathematical correctness of set operations"""
        # Create test sets with known properties
        set_a = list(range(1, 21))      # {1, 2, ..., 20}
        set_b = list(range(11, 31))     # {11, 12, ..., 30}
        set_c = list(range(21, 41))     # {21, 22, ..., 40}
        
        collection_a = real_collection_manager.create_collection(set_a, "Set A")
        collection_b = real_collection_manager.create_collection(set_b, "Set B")
        collection_c = real_collection_manager.create_collection(set_c, "Set C")
        
        # Test A ∪ B
        union_ab = real_collection_manager.union(collection_a, collection_b)
        union_ab_ids = set(real_collection_manager.get_contact_ids(union_ab))
        expected_union = set(range(1, 31))  # {1, 2, ..., 30}
        assert union_ab_ids == expected_union
        
        # Test A ∩ B
        intersect_ab = real_collection_manager.intersect(collection_a, collection_b)
        intersect_ab_ids = set(real_collection_manager.get_contact_ids(intersect_ab))
        expected_intersect = set(range(11, 21))  # {11, 12, ..., 20}
        assert intersect_ab_ids == expected_intersect
        
        # Test A - B
        diff_ab = real_collection_manager.diff(collection_a, collection_b)
        diff_ab_ids = set(real_collection_manager.get_contact_ids(diff_ab))
        expected_diff = set(range(1, 11))  # {1, 2, ..., 10}
        assert diff_ab_ids == expected_diff
        
        # Test mathematical properties
        # |A ∪ B| = |A| + |B| - |A ∩ B|
        assert len(union_ab_ids) == len(set_a) + len(set_b) - len(intersect_ab_ids)
        
        # |A - B| + |A ∩ B| = |A|
        assert len(diff_ab_ids) + len(intersect_ab_ids) == len(set_a)
        
        # Test disjoint sets (B and C have no overlap with A)
        intersect_bc = real_collection_manager.intersect(collection_b, collection_c)
        intersect_bc_ids = set(real_collection_manager.get_contact_ids(intersect_bc))
        expected_bc_intersect = set(range(21, 31))  # {21, 22, ..., 30}
        assert intersect_bc_ids == expected_bc_intersect

    def test_collection_lifecycle_integrity(self, real_collection_manager):
        """Test integrity throughout collection lifecycle"""
        # Create collection
        original_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        collection_id = real_collection_manager.create_collection(original_ids, "Lifecycle Test")
        
        # Verify initial state
        initial_collection = real_collection_manager.get_collection(collection_id)
        assert initial_collection.contact_ids == set(original_ids)
        assert initial_collection.name == "Lifecycle Test"
        
        # Use collection in operations
        subset_collection = real_collection_manager.create_collection([6, 7, 8, 9, 10, 11, 12], "Subset")
        
        intersection_id = real_collection_manager.intersect(collection_id, subset_collection)
        intersection_ids = set(real_collection_manager.get_contact_ids(intersection_id))
        
        # Original collection should be unchanged
        post_op_collection = real_collection_manager.get_collection(collection_id)
        assert post_op_collection.contact_ids == set(original_ids)
        assert post_op_collection.name == "Lifecycle Test"
        
        # Intersection should be correct
        assert intersection_ids == {6, 7, 8, 9, 10}
        
        # Multiple operations should not affect original
        union_id = real_collection_manager.union(collection_id, subset_collection)
        diff_id = real_collection_manager.diff(collection_id, subset_collection)
        
        final_collection = real_collection_manager.get_collection(collection_id)
        assert final_collection.contact_ids == set(original_ids)
        
        # Verify all derived collections are correct
        union_ids = set(real_collection_manager.get_contact_ids(union_id))
        diff_ids = set(real_collection_manager.get_contact_ids(diff_id))
        
        assert union_ids == {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
        assert diff_ids == {1, 2, 3, 4, 5}