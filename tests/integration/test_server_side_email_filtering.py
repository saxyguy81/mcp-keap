"""
Integration Tests for Server-Side Email Filtering in Keap v1 API

This test validates whether the Keap v1 API actually supports server-side email filtering
and measures its effectiveness compared to client-side filtering.
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import list_contacts


class TestServerSideEmailFiltering:
    """Test server-side email filtering capabilities in Keap v1 API."""

    @pytest.mark.asyncio
    async def test_server_side_email_parameter_support(self):
        """
        Test if Keap v1 API supports server-side email filtering parameters.
        """
        context = Context()
        
        print("\n🔍 Testing server-side email filtering support...")
        
        # First, let's manually test what happens when we use optimization 
        # but temporarily allow email filtering to go server-side
        
        # We'll test by directly examining API calls
        from src.mcp.tools_collections import get_api_client
        
        api_client = get_api_client()
        
        # Test 1: Try server-side email filtering
        print("\n📡 Test 1: Server-side email filtering with API parameters")
        
        try:
            # Temporarily test what the API does with email parameter
            response = await api_client.get_contacts(
                limit=10,
                email="*@gmail.com*"  # Wildcard pattern
            )
            
            server_side_count = len(response.get("contacts", []))
            print(f"  Server-side email=*@gmail.com* returned: {server_side_count} contacts")
            
            if server_side_count > 0:
                print("  ✅ Server-side email filtering appears to work!")
                
                # Test exact email match
                response2 = await api_client.get_contacts(
                    limit=5,
                    email="smunira@gmail.com"  # Exact match
                )
                exact_match_count = len(response2.get("contacts", []))
                print(f"  Server-side exact email match returned: {exact_match_count} contacts")
                
            else:
                print("  ❌ Server-side email filtering returned 0 results")
                
        except Exception as e:
            print(f"  ❌ Server-side email filtering failed: {e}")
            server_side_count = -1
        
        # Test 2: Compare with client-side filtering
        print("\n💻 Test 2: Client-side email filtering for comparison")
        
        client_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@gmail.com"}],
            limit=10,
            enable_optimization=False  # Force client-side
        )
        
        client_side_count = client_result["count"]
        print(f"  Client-side email filtering returned: {client_side_count} contacts")
        
        # Analysis
        print("\n📊 Analysis:")
        print(f"  Server-side count: {server_side_count}")
        print(f"  Client-side count: {client_side_count}")
        
        if server_side_count > 0 and client_side_count > 0:
            if server_side_count == client_side_count:
                print("  ✅ Server-side and client-side return same results!")
                return {"server_works": True, "same_results": True}
            elif server_side_count < client_side_count:
                print("  ⚠️  Server-side returns fewer results (may miss some contacts)")
                return {"server_works": True, "same_results": False, "server_incomplete": True}
            else:
                print("  ❓ Server-side returns more results (unexpected)")
                return {"server_works": True, "same_results": False, "server_more": True}
        elif server_side_count > 0:
            print("  ⚠️  Server-side works but client-side failed")
            return {"server_works": True, "client_failed": True}
        elif client_side_count > 0:
            print("  ❌ Server-side doesn't work, client-side does")
            return {"server_works": False, "client_works": True}
        else:
            print("  ❓ Both approaches returned 0 results")
            return {"server_works": False, "both_zero": True}

    @pytest.mark.asyncio
    async def test_email_parameter_patterns(self):
        """
        Test different email parameter patterns to understand server-side filtering capabilities.
        """
        Context()
        
        print("\n🔍 Testing various email parameter patterns...")
        
        from src.mcp.tools_collections import get_api_client
        api_client = get_api_client()
        
        # Test different email patterns
        test_patterns = [
            ("*@gmail.com*", "Wildcard gmail pattern"),
            ("*@*", "All emails pattern"),  
            ("smunira@gmail.com", "Exact email match"),
            ("*gmail*", "Contains gmail"),
            ("*@gmail.com", "Ends with @gmail.com"),
            ("test*", "Starts with test"),
        ]
        
        results = {}
        
        for pattern, description in test_patterns:
            try:
                print(f"\n  Testing pattern: '{pattern}' ({description})")
                
                response = await api_client.get_contacts(
                    limit=5,
                    email=pattern
                )
                
                count = len(response.get("contacts", []))
                print(f"    Result: {count} contacts")
                
                if count > 0:
                    # Get first contact to verify email matches pattern
                    first_contact = response["contacts"][0]
                    contact_email = first_contact.get("email", "")
                    email_addresses = first_contact.get("email_addresses", [])
                    
                    print(f"    First contact email field: '{contact_email}'")
                    print(f"    First contact email_addresses: {email_addresses}")
                
                results[pattern] = {
                    "count": count,
                    "description": description,
                    "works": count > 0
                }
                
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results[pattern] = {
                    "count": -1,
                    "description": description,
                    "error": str(e),
                    "works": False
                }
        
        # Summary
        working_patterns = [p for p, r in results.items() if r.get("works", False)]
        
        print("\n📊 Email Pattern Results:")
        print(f"  Working patterns: {len(working_patterns)}/{len(test_patterns)}")
        for pattern in working_patterns:
            print(f"    ✅ '{pattern}': {results[pattern]['count']} contacts")
        
        return results

    @pytest.mark.asyncio
    async def test_server_side_vs_client_side_performance(self):
        """
        Performance comparison between server-side and client-side email filtering.
        """
        context = Context()
        
        print("\n🔍 Testing performance: server-side vs client-side email filtering...")
        
        import time
        
        # Test server-side performance (if it works)
        print("\n⚡ Server-side email filtering performance:")
        start_time = time.time()
        
        try:
            from src.mcp.tools_collections import get_api_client
            api_client = get_api_client()
            
            response = await api_client.get_contacts(
                limit=50,
                email="*@gmail.com*"
            )
            
            server_time = time.time() - start_time
            server_count = len(response.get("contacts", []))
            
            print(f"  Time: {server_time:.2f}s")
            print(f"  Contacts: {server_count}")
            print(f"  Rate: {server_count / max(server_time, 0.1):.1f} contacts/sec")
            
            server_works = True
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            server_time = -1
            server_count = 0
            server_works = False
        
        # Test client-side performance
        print("\n💻 Client-side email filtering performance:")
        start_time = time.time()
        
        client_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@gmail.com"}],
            limit=50,
            enable_optimization=False  # Force client-side
        )
        
        client_time = time.time() - start_time
        client_count = client_result["count"]
        
        print(f"  Time: {client_time:.2f}s") 
        print(f"  Contacts: {client_count}")
        print(f"  Rate: {client_count / max(client_time, 0.1):.1f} contacts/sec")
        
        # Performance comparison
        print("\n📊 Performance Comparison:")
        if server_works and server_time > 0:
            speedup = client_time / server_time
            print(f"  Server-side is {speedup:.1f}x {'faster' if speedup > 1 else 'slower'} than client-side")
            
            if server_count == client_count:
                print(f"  ✅ Same accuracy: both found {client_count} contacts")
                recommendation = "server-side" if speedup < 1 else "client-side"
                print(f"  💡 Recommendation: Use {recommendation} for email filtering")
            else:
                print(f"  ⚠️  Different accuracy: server={server_count}, client={client_count}")
                print("  💡 Recommendation: Use client-side for completeness")
        else:
            print("  💡 Recommendation: Use client-side (server-side doesn't work)")
        
        return {
            "server_works": server_works,
            "server_time": server_time,
            "server_count": server_count,
            "client_time": client_time,
            "client_count": client_count
        }