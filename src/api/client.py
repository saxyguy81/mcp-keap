"""
Unified Keap API Client

Provides a robust interface for interacting with both Keap CRM API v1 and v2
with support for rate limiting, retries, and pagination.
"""

import os
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional

import httpx
from httpx import AsyncClient, Response

logger = logging.getLogger(__name__)


class KeapApiService:
    """Unified client for interacting with Keap CRM API (v1 and v2)"""
    
    def __init__(self, api_key: Optional[str] = None, api_version: str = "v1"):
        """Initialize the Keap API client
        
        Args:
            api_key: Keap API key (will use KEAP_API_KEY env var if not provided)
            api_version: API version to use ('v1' or 'v2')
        """
        self.api_key = api_key or os.getenv('KEAP_API_KEY')
        if not self.api_key:
            raise ValueError("KEAP_API_KEY must be provided or set in environment")
        
        self.api_version = api_version
        self.base_url = f"https://api.infusionsoft.com/crm/rest/{api_version}"
        
        # Setup session for API calls
        self.session = AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30.0
        )
        
        # Rate limiting
        self.rate_limit_remaining = 1000
        self.rate_limit_window = 3600  # 1 hour
        self.last_request_time = 0
        
        # Cache for tag data
        self._tag_cache = {}
        self._tag_cache_timestamp = 0
        self._tag_cache_ttl = 3600  # 1 hour cache TTL
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def _should_rate_limit(self):
        """Check if we should rate limit requests"""
        current_time = time.time()
        if current_time - self.last_request_time < 0.1:  # 100ms between requests
            return True
        return False
    
    async def _wait_for_rate_limit(self):
        """Wait for rate limit if necessary"""
        if self._should_rate_limit():
            await asyncio.sleep(0.1)
    
    def _handle_rate_limit_headers(self, response: Response):
        """Update rate limit info from response headers"""
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        
        self.last_request_time = time.time()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Response:
        """Make HTTP request with rate limiting and retries"""
        await self._wait_for_rate_limit()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.session.request(method, endpoint, **kwargs)
                self._handle_rate_limit_headers(response)
                
                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    continue
                
                if response.status_code >= 500 and attempt < self.max_retries:
                    # Server error, retry with exponential backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response
                
            except httpx.RequestError as e:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request error: {e}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
        
        raise Exception(f"Max retries exceeded for {method} {endpoint}")
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request"""
        response = await self._make_request("GET", endpoint, params=params)
        return response.json()
    
    async def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request"""
        response = await self._make_request("POST", endpoint, json=data)
        return response.json()
    
    async def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PUT request"""
        response = await self._make_request("PUT", endpoint, json=data)
        return response.json()
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request"""
        response = await self._make_request("DELETE", endpoint)
        return response.json() if response.content else {}
    
    async def get_paginated(self, endpoint: str, params: Optional[Dict] = None, 
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all pages of a paginated endpoint"""
        params = params or {}
        all_items = []
        offset = 0
        page_size = params.get('limit', 200)
        
        while True:
            page_params = {**params, 'offset': offset, 'limit': page_size}
            response = await self.get(endpoint, page_params)
            
            # Handle different response formats
            if isinstance(response, list):
                items = response
            elif 'contacts' in response:
                items = response['contacts']
            elif 'tags' in response:
                items = response['tags']
            elif 'data' in response:
                items = response['data']
            else:
                # Fallback: assume the response itself is the items
                items = response if isinstance(response, list) else []
            
            if not items:
                break
                
            all_items.extend(items)
            
            # Check if we've hit the user-specified limit
            if limit and len(all_items) >= limit:
                all_items = all_items[:limit]
                break
            
            # Check if this was the last page
            if len(items) < page_size:
                break
                
            offset += page_size
        
        return all_items
    
    # Contact Methods
    async def get_contacts(self, limit: int = 200, offset: int = 0, 
                          **filters) -> Dict[str, Any]:
        """Get contacts with optional filters"""
        params = {'limit': limit, 'offset': offset}
        params.update(filters)
        return await self.get('/contacts', params)
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get a specific contact by ID"""
        return await self.get(f'/contacts/{contact_id}')
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact"""
        return await self.post('/contacts', contact_data)
    
    async def update_contact(self, contact_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing contact"""
        return await self.put(f'/contacts/{contact_id}', contact_data)
    
    # Tag Methods
    async def get_tags(self, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """Get tags with caching"""
        current_time = time.time()
        
        # Check cache
        if (self._tag_cache and 
            current_time - self._tag_cache_timestamp < self._tag_cache_ttl):
            return self._tag_cache
        
        # Fetch fresh data
        response = await self.get('/tags', {'limit': limit, 'offset': offset})
        
        # Cache the response
        self._tag_cache = response
        self._tag_cache_timestamp = current_time
        
        return response
    
    async def get_tag(self, tag_id: str) -> Dict[str, Any]:
        """Get a specific tag by ID"""
        return await self.get(f'/tags/{tag_id}')
    
    async def create_tag(self, tag_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new tag"""
        return await self.post('/tags', tag_data)
    
    async def apply_tag_to_contact(self, contact_id: str, tag_id: str) -> Dict[str, Any]:
        """Apply a tag to a contact"""
        if self.api_version == "v2":
            # Use v2 batch endpoint if available
            return await self.apply_tags_to_contacts([tag_id], [contact_id])
        else:
            # Use v1 individual endpoint
            return await self.post(f'/contacts/{contact_id}/tags', {'tagId': tag_id})
    
    async def remove_tag_from_contact(self, contact_id: str, tag_id: str) -> Dict[str, Any]:
        """Remove a tag from a contact"""
        return await self.delete(f'/contacts/{contact_id}/tags/{tag_id}')
    
    async def apply_tags_to_contacts(self, tag_ids: List[str], 
                                   contact_ids: List[str]) -> Dict[str, Any]:
        """Apply multiple tags to multiple contacts (v2 only)"""
        if self.api_version != "v2":
            raise ValueError("Batch tag operations require API v2")
        
        data = {
            'tagIds': tag_ids,
            'contactIds': contact_ids
        }
        return await self.post('/contacts/tags', data)
    
    # Search Methods
    async def search_contacts(self, query: str, limit: int = 200) -> Dict[str, Any]:
        """Search contacts by various fields"""
        params = {
            'email': query,
            'given_name': query,
            'family_name': query,
            'limit': limit
        }
        return await self.get('/contacts', params)
    
    async def get_contacts_by_tag(self, tag_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """Get all contacts with a specific tag"""
        return await self.get_paginated('/contacts', 
                                      params={'tag_id': tag_id}, 
                                      limit=limit)
    
    # Utility Methods
    def get_api_info(self) -> Dict[str, Any]:
        """Get API client information"""
        return {
            'api_version': self.api_version,
            'base_url': self.base_url,
            'rate_limit_remaining': self.rate_limit_remaining,
            'cache_entries': len(self._tag_cache),
            'cache_age_seconds': time.time() - self._tag_cache_timestamp if self._tag_cache else 0
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self._tag_cache.clear()
        self._tag_cache_timestamp = 0
        logger.info("API client cache cleared")


# Factory functions for backward compatibility
def create_keap_client(api_key: Optional[str] = None) -> KeapApiService:
    """Create a Keap API v1 client"""
    return KeapApiService(api_key=api_key, api_version="v1")


def create_keap_v2_client(api_key: Optional[str] = None) -> KeapApiService:
    """Create a Keap API v2 client"""
    return KeapApiService(api_key=api_key, api_version="v2")


# Backward compatibility aliases
KeapClient = KeapApiService

def KeapV2Client(*args, **kwargs):
    """Create Keap API service with v2 API version"""
    return KeapApiService(*args, api_version="v2", **kwargs)