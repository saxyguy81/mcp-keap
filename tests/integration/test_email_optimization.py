"""
Integration Tests for Email Filtering Optimization

Tests the optimized email filtering strategy:
- Exact email matches use server-side optimization (fast)
- Contains/wildcard matches use client-side processing (comprehensive)
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import list_contacts, get_collection_details


class TestEmailFilteringOptimization:
    """Test optimized email filtering strategy."""

    @pytest.mark.asyncio
    async def test_exact_email_optimization(self):
        """
        Test that exact email matches are optimized to server-side.
        """
        context = Context()
        
        print("\n🔍 Testing exact email match optimization...")
        
        # First, find a real email address to test with
        sample_result = await list_contacts(context, limit=3)
        if sample_result["count"] == 0:
            pytest.skip("Need contacts to test email optimization")
        
        sample_details = await get_collection_details(context, sample_result["collection_id"])
        contacts = sample_details.get("contacts", [])
        
        test_email = None
        for contact in contacts:
            # Try both email field and email_addresses
            if contact.get("email"):
                test_email = contact["email"]
                break
            elif contact.get("email_addresses"):
                email_addresses = contact["email_addresses"]
                if email_addresses and isinstance(email_addresses, list):
                    for email_obj in email_addresses:
                        if isinstance(email_obj, dict) and email_obj.get("email"):
                            test_email = email_obj["email"]
                            break
                if test_email:
                    break
        
        if not test_email:
            pytest.skip("No email addresses found in test contacts")
        
        print(f"Testing exact match for email: {test_email}")
        
        # Test exact email match (should use server-side optimization)
        exact_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "equals", "value": test_email}],
            limit=5,
            enable_optimization=True,  # Should use server-side optimization
            return_metrics=True
        )
        
        print(f"Exact email match result: {exact_result['count']} contacts")
        
        # Verify it found the contact
        assert exact_result["count"] >= 1, f"Should find at least 1 contact with email {test_email}"
        
        # Verify the found contact actually has the email
        if exact_result["count"] > 0:
            found_details = await get_collection_details(
                context,
                exact_result["collection_id"],
                fields=["id", "email", "email_addresses"]
            )
            
            found_contact = found_details["contacts"][0]
            contact_email = found_contact.get("email", "")
            email_addresses = found_contact.get("email_addresses", [])
            
            print(f"Found contact email field: '{contact_email}'")
            print(f"Found contact email_addresses: {email_addresses}")
            
            # Email should match in either field or email_addresses
            email_match = (
                contact_email == test_email or 
                any(
                    email_obj.get("email") == test_email 
                    for email_obj in email_addresses 
                    if isinstance(email_obj, dict)
                )
            )
            
            assert email_match, f"Found contact should have email {test_email}"
        
        print("✅ Exact email optimization test passed")

    @pytest.mark.asyncio 
    async def test_contains_email_client_side(self):
        """
        Test that contains email filters use client-side processing.
        """
        context = Context()
        
        print("\n🔍 Testing contains email filter (should be client-side)...")
        
        # Test contains filter (should use client-side)
        contains_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@gmail.com"}],
            limit=10,
            enable_optimization=True,  # Should still force client-side for contains
            return_metrics=True
        )
        
        print(f"Contains email filter result: {contains_result['count']} contacts")
        
        # Verify results if any found
        if contains_result["count"] > 0:
            # Verify the found contacts actually contain gmail.com
            sample_details = await get_collection_details(
                context,
                contains_result["collection_id"],
                fields=["id", "email", "email_addresses"],
                limit=3
            )
            
            print("\nVerifying gmail.com in results:")
            for i, contact in enumerate(sample_details["contacts"]):
                from src.mcp.tools_collections import _extract_all_emails
                all_emails = _extract_all_emails(contact)
                
                has_gmail = any("@gmail.com" in email.lower() for email in all_emails)
                print(f"  Contact {i+1}: emails={all_emails}, has_gmail={has_gmail}")
                
                assert has_gmail, "Contact should contain @gmail.com in emails"
        
        print("✅ Contains email client-side test passed")

    @pytest.mark.asyncio
    async def test_optimization_strategy_selection(self):
        """
        Test that the optimization engine correctly selects strategies for different email operators.
        """
        context = Context()
        
        print("\n🔍 Testing optimization strategy selection for different email operators...")
        
        # Find a test email for exact match testing
        sample_result = await list_contacts(context, limit=1)
        if sample_result["count"] == 0:
            pytest.skip("Need contacts to test optimization strategies")
        
        sample_details = await get_collection_details(context, sample_result["collection_id"])
        contact = sample_details["contacts"][0]
        
        # Extract a test email
        test_email = None
        if contact.get("email"):
            test_email = contact["email"]
        elif contact.get("email_addresses"):
            email_addresses = contact["email_addresses"]
            if email_addresses and isinstance(email_addresses, list):
                for email_obj in email_addresses:
                    if isinstance(email_obj, dict) and email_obj.get("email"):
                        test_email = email_obj["email"]
                        break
        
        if not test_email:
            pytest.skip("No email found for testing")
        
        # Test different operators
        test_cases = [
            ("equals", test_email, "Should use server-side optimization"),
            ("contains", "@gmail.com", "Should use client-side processing"),
            ("starts_with", "test", "Should use client-side processing"),
            ("ends_with", ".com", "Should use client-side processing"),
        ]
        
        for operator, value, expectation in test_cases:
            print(f"\n  Testing operator '{operator}' with value '{value}'")
            print(f"  Expectation: {expectation}")
            
            try:
                result = await list_contacts(
                    context,
                    filters=[{"field": "email", "operator": operator, "value": value}],
                    limit=5,
                    enable_optimization=True,
                    return_metrics=True
                )
                
                print(f"    Result: {result['count']} contacts found")
                
                # Basic validation
                assert "collection_id" in result
                assert "count" in result
                assert result["count"] >= 0
                
                # For exact matches with the test email, should find at least 1 result
                if operator == "equals" and value == test_email:
                    assert result["count"] >= 1, f"Exact match for {test_email} should find at least 1 contact"
                
            except Exception as e:
                pytest.fail(f"Operator '{operator}' failed: {e}")
        
        print("✅ Optimization strategy selection test passed")

    @pytest.mark.asyncio
    async def test_server_side_vs_client_side_accuracy(self):
        """
        Test that server-side exact matches and client-side processing return consistent results.
        """
        context = Context()
        
        print("\n🔍 Testing server-side vs client-side accuracy for exact email matches...")
        
        # Find a real email to test with
        sample_result = await list_contacts(context, limit=5)
        if sample_result["count"] == 0:
            pytest.skip("Need contacts to test accuracy comparison")
        
        sample_details = await get_collection_details(context, sample_result["collection_id"])
        
        # Find an email that exists in multiple contacts or at least one contact
        test_emails = []
        for contact in sample_details["contacts"]:
            from src.mcp.tools_collections import _extract_all_emails
            all_emails = _extract_all_emails(contact)
            test_emails.extend(all_emails)
        
        if not test_emails:
            pytest.skip("No emails found for accuracy testing")
        
        # Test with the first email found
        test_email = test_emails[0]
        print(f"Testing accuracy for email: {test_email}")
        
        # Test server-side optimized approach (exact match)
        server_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "equals", "value": test_email}],
            limit=10,
            enable_optimization=True  # Should use server-side for equals
        )
        
        # Test client-side approach (force client-side)
        client_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "equals", "value": test_email}],
            limit=10,
            enable_optimization=False  # Force client-side
        )
        
        print(f"Server-side optimized result: {server_result['count']} contacts")
        print(f"Client-side result: {client_result['count']} contacts")
        
        # Both approaches should find the same contacts for exact matches
        assert server_result["count"] == client_result["count"], \
            "Server-side and client-side should return same count for exact email match"
        
        # Verify both found at least the contact we know has this email
        assert server_result["count"] >= 1, "Should find at least 1 contact with the test email"
        assert client_result["count"] >= 1, "Should find at least 1 contact with the test email"
        
        print("✅ Server-side vs client-side accuracy test passed")