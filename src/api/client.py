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
        
        # Setup session for API calls with HTTP2 support
        self.session = AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30.0,
            http2=True,  # Enable HTTP/2 support
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
        )
        
        # Enhanced rate limiting
        self.rate_limit_remaining = 1000
        self.rate_limit_window = 3600  # 1 hour
        self.last_request_time = 0
        self.daily_request_count = 0
        self.daily_request_limit = 25000  # Conservative daily limit
        self.request_start_of_day = time.time()
        
        # Cache for tag data
        self._tag_cache = {}
        self._tag_cache_timestamp = 0
        self._tag_cache_ttl = 3600  # 1 hour cache TTL
        
        # Enhanced retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Diagnostics and monitoring
        self.diagnostics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retried_requests": 0,
            "rate_limited_requests": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0,
            "last_request_time": None,
            "endpoints_called": {},
            "error_counts": {},
            "cache_hits": 0,
            "cache_misses": 0
        }
        
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
        """Enhanced rate limiting check"""
        current_time = time.time()
        
        # Check if we need to reset daily counter
        if current_time - self.request_start_of_day > 86400:  # 24 hours
            self.daily_request_count = 0
            self.request_start_of_day = current_time
        
        # Check daily limit
        if self.daily_request_count >= self.daily_request_limit:
            logger.warning(f"Daily request limit of {self.daily_request_limit} reached")
            return True
            
        # Check minimum time between requests
        if current_time - self.last_request_time < 0.1:  # 100ms between requests
            return True
            
        # Check remaining rate limit
        if self.rate_limit_remaining < 10:  # Conservative threshold
            return True
            
        return False
    
    async def _wait_for_rate_limit(self):
        """Enhanced rate limit waiting with diagnostics"""
        if self._should_rate_limit():
            if self.daily_request_count >= self.daily_request_limit:
                # Wait until next day
                wait_time = 86400 - (time.time() - self.request_start_of_day)
                logger.warning(f"Daily limit reached, waiting {wait_time/3600:.1f} hours")
                await asyncio.sleep(min(wait_time, 3600))  # Wait max 1 hour at a time
            else:
                await asyncio.sleep(0.1)
    
    def _handle_rate_limit_headers(self, response: Response):
        """Enhanced rate limit handling with diagnostics"""
        if 'X-RateLimit-Remaining' in response.headers:
            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        
        self.last_request_time = time.time()
        self.daily_request_count += 1
        self.diagnostics["last_request_time"] = self.last_request_time
    
    def _update_diagnostics(self, endpoint: str, success: bool, response_time: float, was_retry: bool = False, error: str = None):
        """Update diagnostic information"""
        self.diagnostics["total_requests"] += 1
        
        if success:
            self.diagnostics["successful_requests"] += 1
        else:
            self.diagnostics["failed_requests"] += 1
            if error:
                self.diagnostics["error_counts"][error] = self.diagnostics["error_counts"].get(error, 0) + 1
        
        if was_retry:
            self.diagnostics["retried_requests"] += 1
        
        # Update response time tracking
        self.diagnostics["total_response_time"] += response_time
        self.diagnostics["average_response_time"] = (
            self.diagnostics["total_response_time"] / self.diagnostics["total_requests"]
        )
        
        # Track endpoint usage
        self.diagnostics["endpoints_called"][endpoint] = self.diagnostics["endpoints_called"].get(endpoint, 0) + 1
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get current diagnostic information"""
        return {
            **self.diagnostics,
            "rate_limit_remaining": self.rate_limit_remaining,
            "daily_requests_remaining": self.daily_request_limit - self.daily_request_count,
            "uptime_hours": (time.time() - self.request_start_of_day) / 3600,
            "requests_per_hour": self.diagnostics["total_requests"] / max((time.time() - self.request_start_of_day) / 3600, 0.1)
        }
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Response:
        """Make HTTP request with enhanced error handling, rate limiting and retries"""
        start_time = time.time()
        await self._wait_for_rate_limit()
        
        last_exception = None
        was_retry = False
        
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                was_retry = True
                
            try:
                response = await self.session.request(method, endpoint, **kwargs)
                self._handle_rate_limit_headers(response)
                
                # Enhanced status code handling
                if response.status_code == 200:
                    response_time = time.time() - start_time
                    self._update_diagnostics(endpoint, success=True, response_time=response_time, was_retry=was_retry)
                    return response
                elif response.status_code == 429:  # Rate limited
                    self.diagnostics["rate_limited_requests"] += 1
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds before retry {attempt + 1}")
                    await asyncio.sleep(retry_after)
                    continue
                elif response.status_code in [500, 502, 503, 504]:  # Server errors - retry
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error {response.status_code}, retrying in {wait_time}s (attempt {attempt + 1})")
                    if attempt < self.max_retries:
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        response_time = time.time() - start_time
                        self._update_diagnostics(endpoint, success=False, response_time=response_time, 
                                               was_retry=was_retry, error=f"HTTP_{response.status_code}")
                        response.raise_for_status()
                elif response.status_code in [400, 401, 403, 404]:  # Client errors - don't retry
                    response_time = time.time() - start_time
                    self._update_diagnostics(endpoint, success=False, response_time=response_time, 
                                           was_retry=was_retry, error=f"HTTP_{response.status_code}")
                    logger.error(f"Client error {response.status_code}: {response.text}")
                    response.raise_for_status()
                else:
                    # Other status codes
                    response_time = time.time() - start_time
                    self._update_diagnostics(endpoint, success=False, response_time=response_time,
                                           was_retry=was_retry, error=f"HTTP_{response.status_code}")
                    response.raise_for_status()
                    
                return response
                
            except httpx.TimeoutException as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Timeout error, retrying in {wait_time}s (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    await asyncio.sleep(wait_time)
                    continue
                    
            except httpx.NetworkError as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Network error: {e}, retrying in {wait_time}s (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    await asyncio.sleep(wait_time)
                    continue
                    
            except httpx.HTTPStatusError as e:
                # Don't retry 4xx client errors
                if 400 <= e.response.status_code < 500:
                    response_time = time.time() - start_time
                    self._update_diagnostics(endpoint, success=False, response_time=response_time,
                                           was_retry=was_retry, error=f"HTTP_{e.response.status_code}")
                    logger.error(f"Client error {e.response.status_code}: {e.response.text}")
                    raise
                else:
                    last_exception = e
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"HTTP error {e.response.status_code}, retrying in {wait_time}s (attempt {attempt + 1})")
                    if attempt < self.max_retries:
                        await asyncio.sleep(wait_time)
                        continue
                        
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    continue
        
        # If we get here, all retries failed
        response_time = time.time() - start_time
        error_type = type(last_exception).__name__ if last_exception else "Unknown"
        self._update_diagnostics(endpoint, success=False, response_time=response_time,
                               was_retry=was_retry, error=error_type)
        
        if last_exception:
            logger.error(f"All {self.max_retries + 1} attempts failed. Last error: {last_exception}")
            raise last_exception
        else:
            raise Exception(f"Request failed after {self.max_retries + 1} attempts")
    
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
    
    async def patch(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PATCH request"""
        response = await self._make_request("PATCH", endpoint, json=data)
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
    
    async def update_contact_custom_field(self, contact_id: str, field_id: str, value: Any) -> Dict[str, Any]:
        """Update a custom field for a specific contact"""
        try:
            # Prepare custom field data according to Keap API format
            custom_field_data = {
                'custom_fields': [
                    {
                        'id': int(field_id),
                        'content': str(value)
                    }
                ]
            }
            
            # Use PATCH method to update only the custom field
            response = await self.patch(f'/contacts/{contact_id}', custom_field_data)
            
            # Check if the response indicates success
            if response and ('id' in response or 'contact' in response):
                return {"success": True, "contact_id": contact_id, "field_id": field_id, "value": value}
            else:
                return {"success": False, "error": "Invalid response from API", "response": response}
                
        except Exception as e:
            logger.error(f"Error updating custom field {field_id} for contact {contact_id}: {e}")
            return {"success": False, "error": str(e)}
    
    # Tag Methods
    async def get_tags(self, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """Get tags with enhanced caching and diagnostics"""
        current_time = time.time()
        
        # Check cache
        if (self._tag_cache and 
            current_time - self._tag_cache_timestamp < self._tag_cache_ttl):
            self.diagnostics["cache_hits"] += 1
            logger.debug("Tag cache hit")
            return self._tag_cache
        
        # Cache miss - fetch fresh data
        self.diagnostics["cache_misses"] += 1
        logger.debug("Tag cache miss - fetching fresh data")
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