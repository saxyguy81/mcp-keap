"""
Collection Manager for Keap MCP Server

Manages in-memory collections of contact IDs with TTL expiration
and provides set operations for composable contact operations.
"""

import time
import uuid
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Collection:
    """Represents a collection of contact IDs with metadata"""
    id: str
    contact_ids: Set[int]
    created_at: float
    name: Optional[str] = None
    description: Optional[str] = None


class CollectionManager:
    """Manages collections of contact IDs with TTL and set operations"""
    
    def __init__(self, default_ttl: int = 3600):
        """Initialize collection manager
        
        Args:
            default_ttl: Default time-to-live for collections in seconds (1 hour)
        """
        self.collections: Dict[str, Collection] = {}
        self.default_ttl = default_ttl
        
    def create_collection(
        self, 
        contact_ids: List[int], 
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Create a new collection
        
        Args:
            contact_ids: List of contact IDs
            name: Optional name for the collection
            description: Optional description
            
        Returns:
            Collection ID
        """
        collection_id = f"contacts_{str(uuid.uuid4())[:8]}"
        
        # Clean expired collections periodically
        self._cleanup_expired()
        
        collection = Collection(
            id=collection_id,
            contact_ids=set(contact_ids),
            created_at=time.time(),
            name=name,
            description=description
        )
        
        self.collections[collection_id] = collection
        logger.info(f"Created collection {collection_id} with {len(contact_ids)} contacts")
        
        return collection_id
        
    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Get a collection by ID
        
        Args:
            collection_id: Collection identifier
            
        Returns:
            Collection object or None if not found/expired
        """
        if not self._is_valid(collection_id):
            return None
            
        return self.collections.get(collection_id)
        
    def get_contact_ids(self, collection_id: str) -> List[int]:
        """Get contact IDs from a collection
        
        Args:
            collection_id: Collection identifier
            
        Returns:
            List of contact IDs or empty list if not found
        """
        collection = self.get_collection(collection_id)
        if not collection:
            return []
            
        return list(collection.contact_ids)
        
    def count(self, collection_id: str) -> int:
        """Get the count of contacts in a collection
        
        Args:
            collection_id: Collection identifier
            
        Returns:
            Number of contacts in collection or 0 if not found
        """
        collection = self.get_collection(collection_id)
        if not collection:
            return 0
            
        return len(collection.contact_ids)
        
    def union(self, collection_a_id: str, collection_b_id: str) -> str:
        """Create union of two collections (A ∪ B)
        
        Args:
            collection_a_id: First collection ID
            collection_b_id: Second collection ID
            
        Returns:
            New collection ID containing the union
            
        Raises:
            ValueError: If either collection doesn't exist
        """
        collection_a = self.get_collection(collection_a_id)
        collection_b = self.get_collection(collection_b_id)
        
        if not collection_a:
            raise ValueError(f"Collection {collection_a_id} not found or expired")
        if not collection_b:
            raise ValueError(f"Collection {collection_b_id} not found or expired")
            
        union_ids = collection_a.contact_ids | collection_b.contact_ids
        
        return self.create_collection(
            contact_ids=list(union_ids),
            name=f"Union of {collection_a_id} and {collection_b_id}",
            description=f"Union operation: {collection_a_id} ∪ {collection_b_id}"
        )
        
    def intersect(self, collection_a_id: str, collection_b_id: str) -> str:
        """Create intersection of two collections (A ∩ B)
        
        Args:
            collection_a_id: First collection ID
            collection_b_id: Second collection ID
            
        Returns:
            New collection ID containing the intersection
            
        Raises:
            ValueError: If either collection doesn't exist
        """
        collection_a = self.get_collection(collection_a_id)
        collection_b = self.get_collection(collection_b_id)
        
        if not collection_a:
            raise ValueError(f"Collection {collection_a_id} not found or expired")
        if not collection_b:
            raise ValueError(f"Collection {collection_b_id} not found or expired")
            
        intersect_ids = collection_a.contact_ids & collection_b.contact_ids
        
        return self.create_collection(
            contact_ids=list(intersect_ids),
            name=f"Intersection of {collection_a_id} and {collection_b_id}",
            description=f"Intersection operation: {collection_a_id} ∩ {collection_b_id}"
        )
        
    def diff(self, collection_a_id: str, collection_b_id: str) -> str:
        """Create difference of two collections (A - B)
        
        Args:
            collection_a_id: First collection ID
            collection_b_id: Second collection ID
            
        Returns:
            New collection ID containing the difference
            
        Raises:
            ValueError: If either collection doesn't exist
        """
        collection_a = self.get_collection(collection_a_id)
        collection_b = self.get_collection(collection_b_id)
        
        if not collection_a:
            raise ValueError(f"Collection {collection_a_id} not found or expired")
        if not collection_b:
            raise ValueError(f"Collection {collection_b_id} not found or expired")
            
        diff_ids = collection_a.contact_ids - collection_b.contact_ids
        
        return self.create_collection(
            contact_ids=list(diff_ids),
            name=f"Difference of {collection_a_id} and {collection_b_id}",
            description=f"Difference operation: {collection_a_id} - {collection_b_id}"
        )
        
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all active collections
        
        Returns:
            List of collection metadata
        """
        self._cleanup_expired()
        
        collections = []
        for collection in self.collections.values():
            collections.append({
                "id": collection.id,
                "count": len(collection.contact_ids),
                "created_at": collection.created_at,
                "name": collection.name,
                "description": collection.description
            })
            
        return collections
        
    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection
        
        Args:
            collection_id: Collection identifier
            
        Returns:
            True if deleted, False if not found
        """
        if collection_id in self.collections:
            del self.collections[collection_id]
            logger.info(f"Deleted collection {collection_id}")
            return True
        return False
        
    def _is_valid(self, collection_id: str) -> bool:
        """Check if a collection exists and hasn't expired
        
        Args:
            collection_id: Collection identifier
            
        Returns:
            True if valid, False if not found or expired
        """
        collection = self.collections.get(collection_id)
        if not collection:
            return False
            
        # Check if expired
        if time.time() - collection.created_at > self.default_ttl:
            logger.info(f"Collection {collection_id} expired, removing")
            del self.collections[collection_id]
            return False
            
        return True
        
    def _cleanup_expired(self):
        """Remove expired collections"""
        current_time = time.time()
        expired_ids = []
        
        for collection_id, collection in self.collections.items():
            if current_time - collection.created_at > self.default_ttl:
                expired_ids.append(collection_id)
                
        for collection_id in expired_ids:
            logger.info(f"Removing expired collection {collection_id}")
            del self.collections[collection_id]
            
    def cleanup_expired_collections(self):
        """Public method to clean up expired collections"""
        self._cleanup_expired()
            
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get collection manager diagnostics
        
        Returns:
            Diagnostic information about collections
        """
        self._cleanup_expired()
        
        total_contacts = sum(len(c.contact_ids) for c in self.collections.values())
        
        return {
            "active_collections": len(self.collections),
            "total_contacts_across_collections": total_contacts,
            "default_ttl": self.default_ttl,
            "collections": self.list_collections()
        }


# Global collection manager instance
_collection_manager = None


def get_collection_manager() -> CollectionManager:
    """Get or create the global collection manager instance"""
    global _collection_manager
    if _collection_manager is None:
        _collection_manager = CollectionManager()
    return _collection_manager