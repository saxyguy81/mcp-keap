"""
Integration Tests for Email Field Inconsistencies

Tests the specific issue where:
- email field is null/empty
- email_addresses array has actual email data
- Server-side filtering on email field would miss these contacts
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
)


class TestEmailFieldInconsistencies:
    """Test cases where email field is null but email_addresses has data."""

    @pytest.mark.asyncio
    async def test_find_email_field_inconsistencies(self):
        """
        Find contacts where email field is null but email_addresses has data.
        This proves that server-side email filtering is incomplete.
        """
        context = Context()
        
        print("\n🔍 Searching for email field inconsistencies...")
        
        # Get a larger sample to find edge cases
        result = await list_contacts(context, limit=50)
        if result["count"] == 0:
            pytest.skip("Need contacts to test email field inconsistencies")
        
        details = await get_collection_details(context, result["collection_id"])
        contacts = details.get("contacts", [])
        
        print(f"Analyzing {len(contacts)} contacts for email field inconsistencies...")
        
        inconsistent_contacts = []
        null_email_with_addresses = 0
        populated_email_with_addresses = 0
        null_email_null_addresses = 0
        
        for contact in contacts:
            contact_id = contact.get("id", "unknown")
            email_field = contact.get("email")
            email_addresses = contact.get("email_addresses", [])
            
            # Check for the specific issue: null email field but populated email_addresses
            if not email_field and email_addresses:
                null_email_with_addresses += 1
                inconsistent_contacts.append({
                    "id": contact_id,
                    "email": email_field,
                    "email_addresses": email_addresses
                })
                print(f"\n❌ INCONSISTENCY FOUND - Contact {contact_id}:")
                print(f"   email field: {email_field}")
                print(f"   email_addresses: {email_addresses}")
            elif email_field and email_addresses:
                populated_email_with_addresses += 1
            elif not email_field and not email_addresses:
                null_email_null_addresses += 1
        
        print("\n📊 Email Field Analysis:")
        print(f"  Contacts with email=null but email_addresses=populated: {null_email_with_addresses}")
        print(f"  Contacts with email=populated and email_addresses=populated: {populated_email_with_addresses}")
        print(f"  Contacts with email=null and email_addresses=null: {null_email_null_addresses}")
        
        if null_email_with_addresses > 0:
            print(f"\n⚠️  CRITICAL FINDING: {null_email_with_addresses} contacts would be MISSED by server-side email filtering!")
            print("This proves that server-side email filtering is incomplete and unreliable.")
            
            return {
                "inconsistent_contacts": inconsistent_contacts,
                "would_be_missed": null_email_with_addresses,
                "total_analyzed": len(contacts)
            }
        else:
            print("\n✅ No inconsistencies found in this sample, but they may exist in larger dataset")
            return {
                "inconsistent_contacts": [],
                "would_be_missed": 0,
                "total_analyzed": len(contacts)
            }

    @pytest.mark.asyncio
    async def test_server_vs_client_email_filtering_completeness(self):
        """
        Compare server-side vs client-side email filtering to demonstrate missed contacts.
        """
        context = Context()
        
        print("\n🔍 Comparing server-side vs client-side email filtering completeness...")
        
        # Test server-side filtering (uses email field only)
        print("Testing server-side email filtering...")
        server_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=100,
            enable_optimization=True  # This should use server-side optimization
        )
        
        print(f"Server-side result: {server_result['count']} contacts")
        
        # Test client-side filtering (should process email_addresses array)
        print("Testing client-side email filtering...")
        client_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=100,
            enable_optimization=False  # Force client-side processing
        )
        
        print(f"Client-side result: {client_result['count']} contacts")
        
        # Analysis
        if client_result["count"] > server_result["count"]:
            missed_contacts = client_result["count"] - server_result["count"]
            print(f"\n❌ COMPLETENESS ISSUE: Server-side filtering missed {missed_contacts} contacts!")
            print("This confirms that server-side email filtering is incomplete.")
            
            # Get details of some contacts from client-side result to analyze
            if client_result["count"] > 0:
                client_details = await get_collection_details(
                    context, 
                    client_result["collection_id"], 
                    fields=["id", "email", "email_addresses"],
                    limit=5
                )
                
                print("\nSample of client-side results:")
                for i, contact in enumerate(client_details.get("contacts", [])):
                    email_field = contact.get("email")
                    email_addresses = contact.get("email_addresses", [])
                    print(f"  Contact {contact['id']}: email='{email_field}', email_addresses={email_addresses}")
            
            return {
                "server_count": server_result["count"],
                "client_count": client_result["count"],
                "missed_by_server": missed_contacts,
                "completeness_issue": True
            }
        elif client_result["count"] == server_result["count"]:
            print("\n✅ Same results from both approaches in this sample")
            return {
                "server_count": server_result["count"],
                "client_count": client_result["count"],
                "missed_by_server": 0,
                "completeness_issue": False
            }
        else:
            print("\n❓ Unexpected: Server-side found more than client-side")
            return {
                "server_count": server_result["count"],
                "client_count": client_result["count"],
                "missed_by_server": 0,
                "completeness_issue": False
            }

    @pytest.mark.asyncio
    async def test_comprehensive_email_search_strategy(self):
        """
        Test a comprehensive email search strategy that handles both email field and email_addresses.
        """
        context = Context()
        
        print("\n🔍 Testing comprehensive email search strategy...")
        
        # Strategy 1: Search using email field (server-side optimized)
        email_field_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=50,
            enable_optimization=True
        )
        
        # Strategy 2: Search using email_addresses field (if supported)
        # Note: This may not be supported by current implementation
        try:
            email_addresses_result = await list_contacts(
                context,
                filters=[{"field": "email_addresses", "operator": "contains", "value": "@"}],
                limit=50,
                enable_optimization=False  # Likely needs client-side processing
            )
            email_addresses_supported = True
        except Exception as e:
            print(f"email_addresses field filtering not supported: {e}")
            email_addresses_result = {"count": 0}
            email_addresses_supported = False
        
        print("Results:")
        print(f"  email field filtering: {email_field_result['count']} contacts")
        print(f"  email_addresses field filtering: {email_addresses_result['count']} contacts")
        
        # The ideal solution would be to:
        # 1. Use client-side filtering that checks both email field AND email_addresses array
        # 2. Or use a custom search strategy that handles the architecture properly
        
        print("\n💡 Recommended approach:")
        print("  - Force email filtering to client-side processing")
        print("  - Client-side logic should check both email field AND email_addresses array")
        print("  - This ensures no contacts are missed due to field inconsistencies")
        
        return {
            "email_field_count": email_field_result["count"],
            "email_addresses_count": email_addresses_result["count"],
            "email_addresses_supported": email_addresses_supported
        }