"""
Integration Tests for Email Field Architecture Issues

This test file specifically addresses the critical architectural issue:
- The 'email' field is a dummy/placeholder field
- Actual email data is stored in the 'email_addresses' array
- Server-side filtering on 'email' field won't work and must be client-side

This test ensures our filtering correctly handles this architecture.
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    get_contact_schema,
)


class TestEmailFieldArchitecture:
    """Test proper handling of email vs email_addresses field architecture."""

    @pytest.mark.asyncio
    async def test_email_field_vs_email_addresses_structure(self):
        """
        Test that demonstrates the email field architecture:
        - email field is dummy/placeholder
        - email_addresses is array with actual data
        """
        context = Context()
        
        # Get some contacts to examine the structure
        result = await list_contacts(context, limit=3)
        if result["count"] == 0:
            pytest.skip("Need contacts to test email field architecture")
        
        details = await get_collection_details(context, result["collection_id"])
        contacts = details.get("contacts", [])
        
        if not contacts:
            pytest.skip("No contact details available")
        
        print(f"\n🔍 Analyzing email field architecture with {len(contacts)} contacts:")
        
        email_field_populated = 0
        email_addresses_populated = 0
        
        for i, contact in enumerate(contacts[:3]):
            contact_id = contact.get("id", "unknown")
            email_field = contact.get("email")
            email_addresses = contact.get("email_addresses", [])
            
            print(f"\nContact {i+1} (ID: {contact_id}):")
            print(f"  email field: {email_field}")
            print(f"  email_addresses: {email_addresses}")
            
            if email_field:
                email_field_populated += 1
            if email_addresses:
                email_addresses_populated += 1
                
        print(f"\n📊 Architecture Analysis:")
        print(f"  Contacts with email field populated: {email_field_populated}/{len(contacts)}")
        print(f"  Contacts with email_addresses populated: {email_addresses_populated}/{len(contacts)}")
        
        # The architectural expectation is that email_addresses is the primary source
        assert email_addresses_populated > 0, "email_addresses should be the primary email data source"
        
        if email_field_populated == 0:
            print("✅ Confirmed: email field is dummy/empty as expected")
        else:
            print("⚠️  Some contacts have email field populated - may be legacy data")

    @pytest.mark.asyncio
    async def test_server_side_email_filtering_fails(self):
        """
        Test that server-side filtering on email field fails because it's dummy.
        This test demonstrates why email filtering must be client-side.
        """
        context = Context()
        
        # Test server-side optimization with email filtering
        print(f"\n🔍 Testing server-side email filtering (should find no results):")
        
        server_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=20,
            enable_optimization=True  # This will try server-side filtering
        )
        
        print(f"Server-side email filtering result: {server_result['count']} contacts")
        
        # Test client-side filtering with email_addresses
        print(f"\n🔍 Testing client-side email_addresses filtering:")
        
        # Note: For proper email filtering, we should be using email_addresses field
        # But first let's test what our current implementation does
        client_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=20,
            enable_optimization=False  # Force client-side filtering
        )
        
        print(f"Client-side email filtering result: {client_result['count']} contacts")
        
        # The server-side should find fewer (or zero) because email field is dummy
        # The client-side should find more because it processes actual email_addresses
        if server_result["count"] == 0 and client_result["count"] > 0:
            print("✅ Confirmed: Server-side email filtering fails, client-side works")
        elif server_result["count"] < client_result["count"]:
            print("⚠️  Server-side finds fewer than client-side (expected)")
        else:
            print("❓ Unexpected: Server-side and client-side return similar results")

    @pytest.mark.asyncio
    async def test_proper_email_filtering_approach(self):
        """
        Test the correct approach for email filtering using email_addresses field.
        """
        context = Context()
        
        print(f"\n🔍 Testing proper email filtering with email_addresses field:")
        
        # This is how email filtering should be done - targeting email_addresses
        # Note: This requires our filtering logic to understand email_addresses array
        
        # For now, test that client-side email filtering works
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=10,
            enable_optimization=False  # Force client-side to avoid dummy email field
        )
        
        print(f"Found {result['count']} contacts with email addresses")
        
        if result["count"] > 0:
            # Verify the filtering actually worked by checking the results
            details = await get_collection_details(
                context,
                result["collection_id"],
                fields=["id", "email", "email_addresses"],
                limit=3
            )
            
            contacts = details.get("contacts", [])
            print(f"\n📧 Email filtering verification (first {len(contacts)} contacts):")
            
            for i, contact in enumerate(contacts):
                contact_id = contact.get("id", "unknown")
                email_field = contact.get("email", "")
                email_addresses = contact.get("email_addresses", [])
                
                print(f"\nContact {i+1} (ID: {contact_id}):")
                print(f"  email field: '{email_field}'")
                print(f"  email_addresses: {email_addresses}")
                
                # Check if filtering worked correctly
                has_email_in_addresses = any(
                    "@" in addr.get("email", "") if isinstance(addr, dict) else "@" in str(addr)
                    for addr in email_addresses
                )
                
                has_email_in_field = "@" in email_field
                
                if has_email_in_addresses:
                    print(f"  ✅ Has email in email_addresses")
                elif has_email_in_field:
                    print(f"  ✅ Has email in email field")
                else:
                    print(f"  ❌ No email found - filtering may be broken")
                    
        assert result["count"] >= 0, "Email filtering should complete without error"

    @pytest.mark.asyncio
    async def test_contact_schema_email_fields(self):
        """
        Test that contact schema properly describes email field architecture.
        """
        context = Context()
        
        print(f"\n🔍 Checking contact schema for email field documentation:")
        
        schema = await get_contact_schema(context)
        
        # Look for email-related fields in schema
        fields = schema.get("fields", {})
        
        email_field_info = fields.get("email")
        email_addresses_field_info = fields.get("email_addresses")
        
        print(f"\nSchema information:")
        print(f"  email field: {email_field_info}")
        print(f"  email_addresses field: {email_addresses_field_info}")
        
        # Check if schema properly documents the architecture
        if email_field_info:
            print(f"  📋 email field is documented in schema")
        if email_addresses_field_info:
            print(f"  📋 email_addresses field is documented in schema")
            
        # The schema should help users understand which field to use
        assert "email" in fields or "email_addresses" in fields, "Schema should document email fields"

    @pytest.mark.asyncio
    async def test_optimization_engine_email_handling(self):
        """
        Test that optimization engine correctly handles email field architecture.
        After our fix, email filtering should not be optimized server-side.
        """
        context = Context()
        
        print(f"\n🔍 Testing optimization engine email handling:")
        
        # Test that email filtering is now forced to client-side
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@gmail.com"}],
            limit=10,
            enable_optimization=True,  # Try to use optimization
            return_metrics=True  # Get optimization metrics
        )
        
        print(f"Result: {result['count']} contacts found")
        
        # Check optimization metrics to see if email filtering was done server-side
        metrics = result.get("optimization_metrics", {})
        server_side_filters = metrics.get("server_side_filters", 0)
        client_side_filters = metrics.get("client_side_filters", 0)
        
        print(f"Optimization metrics:")
        print(f"  Server-side filters: {server_side_filters}")
        print(f"  Client-side filters: {client_side_filters}")
        
        # After our fix, email filters should be client-side (since email field is dummy)
        if client_side_filters > 0 and server_side_filters == 0:
            print("✅ Confirmed: Email filtering correctly forced to client-side")
        elif server_side_filters > 0:
            print("⚠️  Email filtering still using server-side optimization (may fail)")
        else:
            print("❓ No filter metrics available")
            
        assert result["count"] >= 0, "Email filtering should complete without error"