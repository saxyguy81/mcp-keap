"""
Integration Tests to Discover Keap API Limits

Tests to discover the actual maximum batch sizes supported by the Keap v1 API.
"""

import pytest
from src.mcp.tools_collections import get_api_client


class TestKeapApiLimits:
    """Test to discover actual API limits."""

    @pytest.mark.asyncio
    async def test_discover_maximum_contact_limit(self):
        """
        Test to discover the maximum limit parameter for the contacts endpoint.
        """
        api_client = get_api_client()
        
        print("\n🔍 Testing maximum contact limit supported by Keap API...")
        
        # Test progressively larger limits to find the maximum
        test_limits = [200, 500, 1000, 2000, 5000, 10000]
        
        max_working_limit = 0
        
        for limit in test_limits:
            try:
                print(f"\nTesting limit={limit}...")
                
                response = await api_client.get_contacts(
                    limit=limit,
                    offset=0,
                    include_custom_fields=False,  # Minimize response size
                    include_tags=False
                )
                
                contacts_returned = len(response.get("contacts", []))
                
                print(f"  Requested: {limit}, Got: {contacts_returned} contacts")
                
                if contacts_returned > 0:
                    max_working_limit = limit
                    print(f"  ✅ Limit {limit} works")
                else:
                    print(f"  ⚠️  Limit {limit} returned 0 contacts (may be valid)")
                    
            except Exception as e:
                print(f"  ❌ Limit {limit} failed: {e}")
                break
        
        print("\n📊 Results:")
        print(f"  Maximum working limit discovered: {max_working_limit}")
        
        # Test if the API has any documented upper bound
        if max_working_limit >= 1000:
            print("  ✅ API supports at least 1000 contacts per request")
        
        return max_working_limit

    @pytest.mark.asyncio
    async def test_rate_limit_discovery(self):
        """
        Test to understand the actual rate limits in practice.
        """
        api_client = get_api_client()
        
        print("\n🔍 Testing rate limit behavior...")
        
        import time
        
        # Make several quick requests to understand rate limiting
        request_times = []
        
        for i in range(5):
            start = time.time()
            
            try:
                response = await api_client.get_contacts(limit=10)
                end = time.time()
                
                request_time = end - start
                request_times.append(request_time)
                
                print(f"  Request {i+1}: {request_time:.3f}s, got {len(response.get('contacts', []))} contacts")
                
                # Check rate limit headers if available
                if hasattr(api_client, 'rate_limit_remaining'):
                    print(f"    Rate limit remaining: {api_client.rate_limit_remaining}")
                
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
                break
        
        if request_times:
            avg_time = sum(request_times) / len(request_times)
            print("\n📊 Rate limit analysis:")
            print(f"  Average request time: {avg_time:.3f}s")
            print(f"  Estimated max requests/second: {1/avg_time:.1f}")
        
        return request_times

    @pytest.mark.asyncio
    async def test_optimal_batch_size_discovery(self):
        """
        Test to find the optimal batch size for efficiency.
        """
        api_client = get_api_client()
        
        print("\n🔍 Testing optimal batch sizes for efficiency...")
        
        import time
        
        # Test various batch sizes to find the sweet spot
        batch_sizes = [200, 500, 1000, 1500, 2000]
        results = {}
        
        for batch_size in batch_sizes:
            try:
                print(f"\nTesting batch size: {batch_size}")
                
                start_time = time.time()
                
                response = await api_client.get_contacts(
                    limit=batch_size,
                    offset=0,
                    include_custom_fields=True,
                    include_tags=True
                )
                
                end_time = time.time()
                duration = end_time - start_time
                contacts_returned = len(response.get("contacts", []))
                
                efficiency = contacts_returned / duration if duration > 0 else 0
                
                results[batch_size] = {
                    "contacts": contacts_returned,
                    "duration": duration,
                    "efficiency": efficiency
                }
                
                print(f"  Contacts: {contacts_returned}")
                print(f"  Duration: {duration:.2f}s")
                print(f"  Efficiency: {efficiency:.1f} contacts/second")
                
            except Exception as e:
                print(f"  Batch size {batch_size} failed: {e}")
                results[batch_size] = {"error": str(e)}
        
        # Find optimal batch size
        valid_results = {k: v for k, v in results.items() if "error" not in v and v["contacts"] > 0}
        
        if valid_results:
            optimal_batch = max(valid_results.keys(), key=lambda k: valid_results[k]["efficiency"])
            
            print("\n📊 Optimal batch size analysis:")
            print(f"  Optimal batch size: {optimal_batch}")
            print(f"  Best efficiency: {valid_results[optimal_batch]['efficiency']:.1f} contacts/second")
            
            # Recommend batch size for our implementation
            recommended_size = min(optimal_batch, 1000)  # Cap at reasonable limit
            print(f"  Recommended for implementation: {recommended_size}")
            
            return recommended_size
        
        return 500  # Fallback