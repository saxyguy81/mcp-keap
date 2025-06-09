"""
Query Services

Simplified query services for contact and tag operations.
"""

from typing import List, Dict, Any
from src.api.client import KeapApiService

class ContactQueryService:
    """Simplified contact query service"""
    
    def __init__(self, api_client: KeapApiService = None):
        self.api_client = api_client
    
    async def query_contacts(self, filters: List[Dict] = None, limit: int = 100) -> Dict[str, Any]:
        """Query contacts with filters"""
        if self.api_client:
            return await self.api_client.query_contacts(filters=filters, limit=limit)
        return {"contacts": [], "count": 0}
    
    async def get_contact_by_id(self, contact_id: int) -> Dict[str, Any]:
        """Get contact by ID"""
        if self.api_client:
            return await self.api_client.get_contact(contact_id)
        return {}

class TagQueryService:
    """Simplified tag query service"""
    
    def __init__(self, api_client: KeapApiService = None):
        self.api_client = api_client
    
    async def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags"""
        if self.api_client:
            return await self.api_client.get_all_tags()
        return []
    
    async def get_tag_by_id(self, tag_id: int) -> Dict[str, Any]:
        """Get tag by ID"""
        if self.api_client:
            return await self.api_client.get_tag(tag_id)
        return {}

__all__ = ['ContactQueryService', 'TagQueryService']