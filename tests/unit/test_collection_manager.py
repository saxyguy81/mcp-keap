"""
Unit tests for the CollectionManager class.

Tests the core collection management functionality including:
- Collection creation and storage
- Set operations (union, intersection, difference)
- TTL expiration
- Error handling
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from src.cache.collections import CollectionManager, Collection, get_collection_manager


class TestCollectionManager:
    """Test cases for CollectionManager"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = CollectionManager(default_ttl=3600)  # 1 hour TTL

    def test_create_collection(self):
        """Test creating a new collection"""
        contact_ids = [1, 2, 3, 4, 5]
        collection_id = self.manager.create_collection(
            contact_ids=contact_ids,
            name="Test Collection",
            description="A test collection"
        )
        
        assert collection_id.startswith("contacts_")
        assert len(collection_id) == 17  # "contacts_" + 8 char UUID
        
        collection = self.manager.get_collection(collection_id)
        assert collection is not None
        assert collection.contact_ids == set(contact_ids)
        assert collection.name == "Test Collection"
        assert collection.description == "A test collection"
        assert isinstance(collection.created_at, float)

    def test_create_collection_without_name(self):
        """Test creating collection without optional parameters"""
        contact_ids = [1, 2, 3]
        collection_id = self.manager.create_collection(contact_ids=contact_ids)
        
        collection = self.manager.get_collection(collection_id)
        assert collection is not None
        assert collection.contact_ids == {1, 2, 3}
        assert collection.name is None
        assert collection.description is None

    def test_get_collection_ids(self):
        """Test retrieving contact IDs from collection"""
        contact_ids = [1, 2, 3, 4, 5]
        collection_id = self.manager.create_collection(contact_ids=contact_ids)
        
        retrieved_ids = self.manager.get_contact_ids(collection_id)
        assert set(retrieved_ids) == set(contact_ids)

    def test_get_collection_ids_nonexistent(self):
        """Test retrieving IDs from non-existent collection"""
        result = self.manager.get_contact_ids("nonexistent_id")
        assert result == []

    def test_count(self):
        """Test counting contacts in collection"""
        contact_ids = [1, 2, 3, 4, 5]
        collection_id = self.manager.create_collection(contact_ids=contact_ids)
        
        count = self.manager.count(collection_id)
        assert count == 5

    def test_count_nonexistent(self):
        """Test counting contacts in non-existent collection"""
        count = self.manager.count("nonexistent_id")
        assert count == 0

    def test_union(self):
        """Test union operation (A ∪ B)"""
        collection_a = self.manager.create_collection([1, 2, 3, 4])
        collection_b = self.manager.create_collection([3, 4, 5, 6])
        
        union_id = self.manager.union(collection_a, collection_b)
        union_contacts = set(self.manager.get_contact_ids(union_id))
        
        assert union_contacts == {1, 2, 3, 4, 5, 6}

    def test_union_nonexistent_collection(self):
        """Test union with non-existent collection"""
        collection_a = self.manager.create_collection([1, 2, 3])
        
        with pytest.raises(ValueError, match="Collection nonexistent not found"):
            self.manager.union(collection_a, "nonexistent")
        
        with pytest.raises(ValueError, match="Collection nonexistent not found"):
            self.manager.union("nonexistent", collection_a)

    def test_intersect(self):
        """Test intersection operation (A ∩ B)"""
        collection_a = self.manager.create_collection([1, 2, 3, 4])
        collection_b = self.manager.create_collection([3, 4, 5, 6])
        
        intersect_id = self.manager.intersect(collection_a, collection_b)
        intersect_contacts = set(self.manager.get_contact_ids(intersect_id))
        
        assert intersect_contacts == {3, 4}

    def test_intersect_no_overlap(self):
        """Test intersection with no overlapping contacts"""
        collection_a = self.manager.create_collection([1, 2])
        collection_b = self.manager.create_collection([3, 4])
        
        intersect_id = self.manager.intersect(collection_a, collection_b)
        intersect_contacts = self.manager.get_contact_ids(intersect_id)
        
        assert intersect_contacts == []

    def test_intersect_nonexistent_collection(self):
        """Test intersection with non-existent collection"""
        collection_a = self.manager.create_collection([1, 2, 3])
        
        with pytest.raises(ValueError, match="Collection nonexistent not found"):
            self.manager.intersect(collection_a, "nonexistent")

    def test_diff(self):
        """Test difference operation (A - B)"""
        collection_a = self.manager.create_collection([1, 2, 3, 4])
        collection_b = self.manager.create_collection([3, 4, 5, 6])
        
        diff_id = self.manager.diff(collection_a, collection_b)
        diff_contacts = set(self.manager.get_contact_ids(diff_id))
        
        assert diff_contacts == {1, 2}

    def test_diff_complete_overlap(self):
        """Test difference where B contains all of A"""
        collection_a = self.manager.create_collection([1, 2])
        collection_b = self.manager.create_collection([1, 2, 3, 4])
        
        diff_id = self.manager.diff(collection_a, collection_b)
        diff_contacts = self.manager.get_contact_ids(diff_id)
        
        assert diff_contacts == []

    def test_diff_nonexistent_collection(self):
        """Test difference with non-existent collection"""
        collection_a = self.manager.create_collection([1, 2, 3])
        
        with pytest.raises(ValueError, match="Collection nonexistent not found"):
            self.manager.diff(collection_a, "nonexistent")

    def test_list_collections(self):
        """Test listing all collections"""
        # Start with empty manager
        assert self.manager.list_collections() == []
        
        # Create some collections
        id1 = self.manager.create_collection([1, 2], "Collection 1", "First collection")
        id2 = self.manager.create_collection([3, 4, 5], "Collection 2", "Second collection")
        
        collections = self.manager.list_collections()
        assert len(collections) == 2
        
        # Find our collections in the list
        collection_1 = next(c for c in collections if c["id"] == id1)
        collection_2 = next(c for c in collections if c["id"] == id2)
        
        assert collection_1["count"] == 2
        assert collection_1["name"] == "Collection 1"
        assert collection_1["description"] == "First collection"
        
        assert collection_2["count"] == 3
        assert collection_2["name"] == "Collection 2"
        assert collection_2["description"] == "Second collection"

    def test_delete_collection(self):
        """Test deleting a collection"""
        collection_id = self.manager.create_collection([1, 2, 3])
        
        # Verify collection exists
        assert self.manager.get_collection(collection_id) is not None
        
        # Delete collection
        result = self.manager.delete_collection(collection_id)
        assert result is True
        
        # Verify collection is gone
        assert self.manager.get_collection(collection_id) is None
        
        # Try to delete again
        result = self.manager.delete_collection(collection_id)
        assert result is False

    def test_ttl_expiration(self):
        """Test TTL expiration of collections"""
        # Create manager with very short TTL
        short_ttl_manager = CollectionManager(default_ttl=0.1)  # 0.1 seconds
        
        collection_id = short_ttl_manager.create_collection([1, 2, 3])
        
        # Collection should exist immediately
        assert short_ttl_manager.get_collection(collection_id) is not None
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Collection should be expired and return None
        assert short_ttl_manager.get_collection(collection_id) is None

    def test_cleanup_expired(self):
        """Test cleanup of expired collections"""
        # Create manager with very short TTL
        short_ttl_manager = CollectionManager(default_ttl=0.1)
        
        # Create multiple collections
        id1 = short_ttl_manager.create_collection([1, 2])
        id2 = short_ttl_manager.create_collection([3, 4])
        
        # Both should exist
        assert len(short_ttl_manager.list_collections()) == 2
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Trigger cleanup by creating a new collection
        id3 = short_ttl_manager.create_collection([5, 6])
        
        # Only the new collection should exist
        collections = short_ttl_manager.list_collections()
        assert len(collections) == 1
        assert collections[0]["id"] == id3

    def test_get_diagnostics(self):
        """Test diagnostics reporting"""
        # Start with empty manager
        diagnostics = self.manager.get_diagnostics()
        assert diagnostics["active_collections"] == 0
        assert diagnostics["total_contacts_across_collections"] == 0
        assert diagnostics["default_ttl"] == 3600
        assert diagnostics["collections"] == []
        
        # Create some collections
        self.manager.create_collection([1, 2, 3])
        self.manager.create_collection([4, 5])
        
        diagnostics = self.manager.get_diagnostics()
        assert diagnostics["active_collections"] == 2
        assert diagnostics["total_contacts_across_collections"] == 5
        assert len(diagnostics["collections"]) == 2

    def test_duplicate_contact_ids(self):
        """Test handling of duplicate contact IDs in a collection"""
        contact_ids = [1, 2, 2, 3, 3, 3]  # Contains duplicates
        collection_id = self.manager.create_collection(contact_ids)
        
        # Should store as set, removing duplicates
        retrieved_ids = self.manager.get_contact_ids(collection_id)
        assert set(retrieved_ids) == {1, 2, 3}
        assert self.manager.count(collection_id) == 3

    def test_empty_collection(self):
        """Test creating and handling empty collections"""
        collection_id = self.manager.create_collection([])
        
        assert self.manager.count(collection_id) == 0
        assert self.manager.get_contact_ids(collection_id) == []
        
        # Operations with empty collections
        other_id = self.manager.create_collection([1, 2, 3])
        
        union_id = self.manager.union(collection_id, other_id)
        assert set(self.manager.get_contact_ids(union_id)) == {1, 2, 3}
        
        intersect_id = self.manager.intersect(collection_id, other_id)
        assert self.manager.get_contact_ids(intersect_id) == []
        
        diff_id = self.manager.diff(other_id, collection_id)
        assert set(self.manager.get_contact_ids(diff_id)) == {1, 2, 3}

    @patch('time.time')
    def test_is_valid_timing(self, mock_time):
        """Test _is_valid method with controlled timing"""
        # Mock time to control expiration
        mock_time.return_value = 1000.0
        
        collection_id = self.manager.create_collection([1, 2, 3])
        
        # Should be valid immediately
        assert self.manager._is_valid(collection_id) is True
        
        # Advance time beyond TTL
        mock_time.return_value = 1000.0 + 3600 + 1  # Past TTL
        
        # Should be expired
        assert self.manager._is_valid(collection_id) is False
        
        # Collection should be removed from storage
        assert collection_id not in self.manager.collections


class TestGetCollectionManager:
    """Test the global collection manager factory function"""

    def test_singleton_behavior(self):
        """Test that get_collection_manager returns the same instance"""
        manager1 = get_collection_manager()
        manager2 = get_collection_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, CollectionManager)

    def test_manager_persistence(self):
        """Test that collections persist across get_collection_manager calls"""
        manager1 = get_collection_manager()
        collection_id = manager1.create_collection([1, 2, 3], "Test")
        
        manager2 = get_collection_manager()
        retrieved_collection = manager2.get_collection(collection_id)
        
        assert retrieved_collection is not None
        assert retrieved_collection.name == "Test"
        assert retrieved_collection.contact_ids == {1, 2, 3}


class TestCollectionDataclass:
    """Test the Collection dataclass"""

    def test_collection_creation(self):
        """Test creating a Collection instance"""
        contact_ids = {1, 2, 3, 4}
        created_at = time.time()
        
        collection = Collection(
            id="test_id",
            contact_ids=contact_ids,
            created_at=created_at,
            name="Test Collection",
            description="A test collection"
        )
        
        assert collection.id == "test_id"
        assert collection.contact_ids == contact_ids
        assert collection.created_at == created_at
        assert collection.name == "Test Collection"
        assert collection.description == "A test collection"

    def test_collection_defaults(self):
        """Test Collection with default values"""
        contact_ids = {1, 2, 3}
        created_at = time.time()
        
        collection = Collection(
            id="test_id",
            contact_ids=contact_ids,
            created_at=created_at
        )
        
        assert collection.name is None
        assert collection.description is None