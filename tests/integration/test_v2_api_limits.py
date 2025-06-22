"""
Integration Tests for Keap API v2 Limits

Tests to discover batch size limits and performance characteristics of v2 API.
"""

import pytest
from src.api.client import KeapApiService


class TestKeapV2ApiLimits:
    """Test v2 API limits and compare with v1."""

    @pytest.mark.asyncio
    async def test_v2_api_availability_and_limits(self):
        """
        Test if v2 API is available and what its limits are.
        """
        print("\n🔍 Testing Keap API v2 availability and limits...")
        
        try:
            # Create v2 API client
            v2_client = KeapApiService(api_version="v2")
            
            print("✅ v2 API client created successfully")
            print(f"   Base URL: {v2_client.base_url}")
            
            # Test v2 contacts endpoint with various limits
            test_limits = [200, 500, 1000, 2000, 5000]
            v2_results = {}
            
            for limit in test_limits:
                try:
                    print(f"\nTesting v2 API with limit={limit}...")
                    
                    response = await v2_client.get_contacts(
                        limit=limit,
                        offset=0,
                        include_custom_fields=False,
                        include_tags=False
                    )
                    
                    contacts_returned = len(response.get("contacts", []))
                    v2_results[limit] = contacts_returned
                    
                    print(f"  v2 API - Requested: {limit}, Got: {contacts_returned} contacts")
                    
                except Exception as e:
                    print(f"  v2 API limit {limit} failed: {e}")
                    v2_results[limit] = f"Error: {e}"
                    
                    # If 401/403, v2 might not be available for this account
                    if "401" in str(e) or "403" in str(e) or "404" in str(e):
                        print("  ⚠️  v2 API may not be available for this account")
                        break
            
            # Compare with v1 results if v2 worked
            if any(isinstance(v, int) for v in v2_results.values()):
                print("\n📊 v2 API Results Summary:")
                for limit, result in v2_results.items():
                    if isinstance(result, int):
                        print(f"  Limit {limit}: {result} contacts")
                
                # Find max working limit for v2
                max_v2_contacts = max(v for v in v2_results.values() if isinstance(v, int))
                max_v2_limit = max(k for k, v in v2_results.items() if isinstance(v, int) and v == max_v2_contacts)
                
                print(f"\n  v2 API maximum discovered: {max_v2_contacts} contacts per request")
                print(f"  v2 API recommended batch size: {min(max_v2_limit, max_v2_contacts)}")
                
                return {
                    "v2_available": True,
                    "v2_max_contacts": max_v2_contacts,
                    "v2_recommended_batch": min(max_v2_limit, max_v2_contacts)
                }
            else:
                print("\n❌ v2 API not accessible or all requests failed")
                return {"v2_available": False}
        
        except Exception as e:
            print(f"❌ Failed to create v2 API client: {e}")
            return {"v2_available": False, "error": str(e)}

    @pytest.mark.asyncio
    async def test_v1_vs_v2_performance_comparison(self):
        """
        Compare v1 vs v2 API performance for contact retrieval.
        """
        print("\n🔍 Comparing v1 vs v2 API performance...")
        
        import time
        
        # Test v1 performance
        v1_client = KeapApiService(api_version="v1")
        
        try:
            print("Testing v1 API performance...")
            v1_start = time.time()
            
            v1_response = await v1_client.get_contacts(
                limit=1000,
                offset=0,
                include_custom_fields=True,
                include_tags=True
            )
            
            v1_duration = time.time() - v1_start
            v1_contacts = len(v1_response.get("contacts", []))
            v1_efficiency = v1_contacts / v1_duration if v1_duration > 0 else 0
            
            print(f"  v1: {v1_contacts} contacts in {v1_duration:.2f}s ({v1_efficiency:.1f} contacts/sec)")
            
        except Exception as e:
            print(f"  v1 API failed: {e}")
            v1_contacts = 0
            v1_duration = float('inf')
            v1_efficiency = 0
        
        # Test v2 performance
        try:
            v2_client = KeapApiService(api_version="v2")
            
            print("Testing v2 API performance...")
            v2_start = time.time()
            
            v2_response = await v2_client.get_contacts(
                limit=1000,
                offset=0,
                include_custom_fields=True,
                include_tags=True
            )
            
            v2_duration = time.time() - v2_start
            v2_contacts = len(v2_response.get("contacts", []))
            v2_efficiency = v2_contacts / v2_duration if v2_duration > 0 else 0
            
            print(f"  v2: {v2_contacts} contacts in {v2_duration:.2f}s ({v2_efficiency:.1f} contacts/sec)")
            
            # Performance comparison
            if v1_efficiency > 0 and v2_efficiency > 0:
                if v2_efficiency > v1_efficiency:
                    improvement = (v2_efficiency - v1_efficiency) / v1_efficiency * 100
                    print(f"\n📈 v2 is {improvement:.1f}% faster than v1")
                    recommendation = "v2"
                else:
                    decline = (v1_efficiency - v2_efficiency) / v1_efficiency * 100
                    print(f"\n📉 v2 is {decline:.1f}% slower than v1")
                    recommendation = "v1"
                
                print(f"💡 Recommendation: Use API {recommendation} for contact operations")
            
            return {
                "v1_contacts": v1_contacts,
                "v1_duration": v1_duration,
                "v1_efficiency": v1_efficiency,
                "v2_contacts": v2_contacts,
                "v2_duration": v2_duration,
                "v2_efficiency": v2_efficiency,
                "recommendation": recommendation if 'recommendation' in locals() else "v1"
            }
            
        except Exception as e:
            print(f"  v2 API failed: {e}")
            print("\n💡 Recommendation: Use API v1 (v2 not accessible)")
            
            return {
                "v1_contacts": v1_contacts,
                "v1_duration": v1_duration,
                "v1_efficiency": v1_efficiency,
                "v2_available": False,
                "recommendation": "v1"
            }

    @pytest.mark.asyncio
    async def test_should_we_upgrade_to_v2(self):
        """
        Determine if we should upgrade our implementation to use v2 API.
        """
        print("\n🔍 Determining if we should upgrade to v2 API...")
        
        # Get our current configuration
        from src.mcp.tools_collections import get_api_client
        current_client = get_api_client()
        
        print(f"Current API version in use: {getattr(current_client, 'api_version', 'v1')}")
        
        # Test both APIs
        try:
            v1_available = True
            v2_available = True
            
            # Quick v1 test
            try:
                v1_client = KeapApiService(api_version="v1")
                v1_test = await v1_client.get_contacts(limit=1)
                v1_works = len(v1_test.get("contacts", [])) >= 0
                print(f"  v1 API: {'✅ Working' if v1_works else '❌ Failed'}")
            except Exception as e:
                print(f"  v1 API: ❌ Failed - {e}")
                v1_available = False
            
            # Quick v2 test
            try:
                v2_client = KeapApiService(api_version="v2")
                v2_test = await v2_client.get_contacts(limit=1)
                v2_works = len(v2_test.get("contacts", [])) >= 0
                print(f"  v2 API: {'✅ Working' if v2_works else '❌ Failed'}")
            except Exception as e:
                print(f"  v2 API: ❌ Failed - {e}")
                v2_available = False
            
            # Recommendation
            print("\n💡 Upgrade Recommendation:")
            
            if v2_available and v1_available:
                print("  Both APIs available - performance testing recommended")
                print("  v2 is typically newer with more features")
                recommendation = "Consider upgrading to v2 after performance validation"
            elif v2_available and not v1_available:
                print("  Only v2 available - upgrade required")
                recommendation = "Upgrade to v2 immediately"
            elif v1_available and not v2_available:
                print("  Only v1 available - stay with current implementation")
                recommendation = "Stay with v1 (v2 not accessible)"
            else:
                print("  Neither API working - configuration issue")
                recommendation = "Fix API configuration"
            
            print(f"  Final recommendation: {recommendation}")
            
            return {
                "v1_available": v1_available,
                "v2_available": v2_available,
                "current_version": getattr(current_client, 'api_version', 'v1'),
                "recommendation": recommendation
            }
            
        except Exception as e:
            print(f"❌ Error during API version testing: {e}")
            return {"error": str(e), "recommendation": "Stay with current v1"}