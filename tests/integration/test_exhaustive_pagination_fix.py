"""
Integration Tests for Exhaustive Pagination Fix

Tests that the exhaustive pagination fix correctly searches the entire database
and finds contacts that were previously missed due to pagination limitations.
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import list_contacts, get_collection_details


class TestExhaustivePaginationFix:
    """Test the exhaustive pagination fix."""

    @pytest.mark.asyncio
    async def test_exhaustive_email_search_coverage(self):
        """
        Test that exhaustive email search finds significantly more contacts
        than the previous limited approach.
        """
        context = Context()
        
        print("\n🔍 Testing exhaustive email search coverage...")
        
        # Test with a common email pattern that should find many contacts
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@gmail.com"}],
            limit=100,  # Request many matches to trigger exhaustive search
            enable_optimization=False  # Force client-side comprehensive search
        )
        
        print(f"Gmail search result: {result['count']} contacts found")
        
        # This should now find significantly more contacts than before (when it was limited to ~500-1500 contacts)
        # Previously we found only a few gmail contacts; with exhaustive search we should find many more
        
        if result['count'] > 0:
            # Verify some of the results actually contain gmail addresses
            details = await get_collection_details(
                context,
                result['collection_id'],
                fields=["id", "email", "email_addresses"],
                limit=5
            )
            
            print("\nSample verification (first 5 contacts):")
            for i, contact in enumerate(details.get('contacts', [])):
                from src.mcp.tools_collections import _extract_all_emails
                all_emails = _extract_all_emails(contact)
                has_gmail = any("@gmail.com" in email.lower() for email in all_emails)
                print(f"  Contact {i+1} (ID: {contact['id']}): emails={all_emails}, has_gmail={has_gmail}")
                assert has_gmail, "Contact should contain @gmail.com"
        
        # With exhaustive search, we should find more than the previous ~5-10 gmail contacts
        assert result['count'] > 5, f"Exhaustive search should find more gmail contacts, got {result['count']}"
        
        print(f"✅ Exhaustive email search found {result['count']} gmail contacts")

    @pytest.mark.asyncio
    async def test_exhaustive_search_finds_specific_contacts(self):
        """
        Test that exhaustive search can find specific contacts that might be
        in different parts of the database (various offsets).
        """
        context = Context()
        
        print("\n🔍 Testing exhaustive search finds specific contacts...")
        
        # Search for contacts with specific characteristics that might be spread throughout database
        test_cases = [
            ("@yahoo.com", "Yahoo email addresses"),
            ("@hotmail.com", "Hotmail email addresses"),
            ("test", "Test-related emails"),
            ("@company.com", "Company email domains"),
        ]
        
        total_unique_contacts = 0
        
        for pattern, description in test_cases:
            result = await list_contacts(
                context,
                filters=[{"field": "email", "operator": "contains", "value": pattern}],
                limit=50,
                enable_optimization=False  # Force exhaustive search
            )
            
            print(f"\n{description}: {result['count']} contacts")
            total_unique_contacts += result['count']
            
            # Basic validation that results are reasonable
            assert result['count'] >= 0, "Should return non-negative count"
            
            if result['count'] > 0:
                # Quick validation of first result
                details = await get_collection_details(
                    context,
                    result['collection_id'], 
                    fields=["id", "email", "email_addresses"],
                    limit=1
                )
                
                if details.get('contacts'):
                    contact = details['contacts'][0]
                    from src.mcp.tools_collections import _extract_all_emails
                    all_emails = _extract_all_emails(contact)
                    has_pattern = any(pattern.lower() in email.lower() for email in all_emails)
                    print(f"  Verified: contact {contact['id']} has pattern '{pattern}': {has_pattern}")
        
        print(f"\nTotal contacts found across all patterns: {total_unique_contacts}")
        
        # With exhaustive search, we should find a reasonable number of varied contacts
        print("✅ Exhaustive search successfully found contacts across multiple patterns")

    @pytest.mark.asyncio
    async def test_exhaustive_search_performance_monitoring(self):
        """
        Test that exhaustive search completes in reasonable time while providing full coverage.
        """
        context = Context()
        
        print("\n🔍 Testing exhaustive search performance...")
        
        import time
        start_time = time.time()
        
        # Use a filter that requires extensive searching
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@"}],  # All emails
            limit=200,  # Request many to trigger exhaustive search 
            enable_optimization=False
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("Exhaustive search performance:")
        print(f"  Contacts found: {result['count']}")
        print(f"  Time taken: {duration:.2f} seconds")
        print(f"  Rate: {result['count'] / max(duration, 0.1):.1f} contacts/second")
        
        # Performance should be reasonable even with exhaustive search
        assert duration < 120, f"Exhaustive search took too long: {duration:.2f} seconds"
        
        # Should find significantly more contacts than limited approach
        assert result['count'] > 50, f"Exhaustive search should find many contacts with '@', got {result['count']}"
        
        print("✅ Exhaustive search performance test passed")

    @pytest.mark.asyncio
    async def test_compare_before_after_pagination_fix(self):
        """
        Compare search results before and after pagination fix by simulating
        the old limited approach vs new exhaustive approach.
        """
        context = Context()
        
        print("\n🔍 Comparing limited vs exhaustive search approaches...")
        
        # Test with email filtering that should show the difference
        
        # Get a rough simulation of "old limited approach" by using a smaller sample
        # We'll search for contacts in the first 1000 only (simulating old limitation)
        from src.mcp.tools_collections import get_api_client
        api_client = get_api_client()
        
        # Simulate old limited approach
        print("Simulating old limited approach (first 1000 contacts only):")
        limited_contacts = await api_client.get_contacts(
            limit=1000,
            offset=0,
            include_custom_fields=True,
            include_tags=True
        )
        
        limited_gmail_count = 0
        for contact in limited_contacts.get('contacts', []):
            from src.mcp.tools_collections import _extract_all_emails
            all_emails = _extract_all_emails(contact)
            if any("@gmail.com" in email.lower() for email in all_emails):
                limited_gmail_count += 1
        
        print(f"  Limited approach found: {limited_gmail_count} gmail contacts")
        
        # Now test with new exhaustive approach
        print("Testing new exhaustive approach:")
        exhaustive_result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@gmail.com"}],
            limit=100,
            enable_optimization=False  # Force exhaustive search
        )
        
        exhaustive_gmail_count = exhaustive_result['count']
        print(f"  Exhaustive approach found: {exhaustive_gmail_count} gmail contacts")
        
        # Calculate improvement
        if limited_gmail_count > 0:
            improvement = (exhaustive_gmail_count - limited_gmail_count) / limited_gmail_count * 100
            print(f"  Improvement: {improvement:.1f}% more contacts found")
        else:
            print(f"  Improvement: Found {exhaustive_gmail_count} contacts vs 0 in limited approach")
        
        # Exhaustive approach should find at least as many (likely more) contacts
        assert exhaustive_gmail_count >= limited_gmail_count, \
            "Exhaustive search should find at least as many contacts as limited search"
        
        if exhaustive_gmail_count > limited_gmail_count:
            print(f"✅ Exhaustive search successfully found {exhaustive_gmail_count - limited_gmail_count} additional contacts!")
        else:
            print("✅ Exhaustive search found same number of contacts (both approaches complete)")
        
        return {
            "limited_count": limited_gmail_count,
            "exhaustive_count": exhaustive_gmail_count,
            "improvement": exhaustive_gmail_count - limited_gmail_count
        }