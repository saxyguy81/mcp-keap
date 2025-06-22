"""
Integration Tests for Pagination Coverage Issues

Tests that demonstrate and validate pagination issues where contacts
are missed due to limited search scope in bulk retrieval strategies.
"""

import pytest
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import list_contacts, get_collection_details


class TestPaginationCoverage:
    """Test pagination coverage in contact search strategies."""

    @pytest.mark.asyncio
    async def test_total_contact_count_discovery(self):
        """
        Discover the total number of contacts to understand pagination scope.
        """
        context = Context()
        
        print("\n🔍 Discovering total contact count for pagination analysis...")
        
        # Get a large sample to understand total scope
        large_sample = await list_contacts(
            context, 
            limit=1000,  # Request many contacts
            enable_optimization=False  # Use bulk retrieval
        )
        
        print(f"Large sample result: {large_sample['count']} contacts found")
        
        # Check if we hit the limit (indicating more contacts exist)
        if large_sample['count'] >= 1000:
            print("⚠️  Hit requested limit - more contacts likely exist beyond pagination scope")
        else:
            print(f"✅ Found {large_sample['count']} total contacts")
        
        # Test various search strategies to see coverage differences
        strategies = [
            ("Small limit", 10),
            ("Medium limit", 50), 
            ("Large limit", 200),
            ("Very large limit", 500),
        ]
        
        for description, limit in strategies:
            result = await list_contacts(context, limit=limit, enable_optimization=False)
            print(f"  {description} ({limit}): {result['count']} contacts")
        
        assert large_sample['count'] > 0, "Should find some contacts"

    @pytest.mark.asyncio
    async def test_pagination_coverage_with_rare_filters(self):
        """
        Test pagination coverage using filters that match rare contacts
        that might be missed due to limited pagination scope.
        """
        context = Context()
        
        print("\n🔍 Testing pagination coverage with rare filters...")
        
        # Test email filtering with different strategies
        rare_email_patterns = [
            ("@gmail.com", "Gmail addresses"),
            ("@yahoo.com", "Yahoo addresses"), 
            ("@hotmail.com", "Hotmail addresses"),
            ("test", "Test-related emails"),
        ]
        
        for pattern, description in rare_email_patterns:
            print(f"\nTesting {description} pattern: '{pattern}'")
            
            # Client-side search (current implementation)
            client_result = await list_contacts(
                context,
                filters=[{"field": "email", "operator": "contains", "value": pattern}],
                limit=100,
                enable_optimization=False  # Force client-side
            )
            
            print(f"  Client-side search: {client_result['count']} contacts")
            
            # If we found contacts, check if they actually match
            if client_result['count'] > 0:
                sample_details = await get_collection_details(
                    context,
                    client_result['collection_id'],
                    fields=["id", "email", "email_addresses"],
                    limit=3
                )
                
                print("  Sample verification:")
                for i, contact in enumerate(sample_details.get('contacts', [])):
                    from src.mcp.tools_collections import _extract_all_emails
                    all_emails = _extract_all_emails(contact)
                    has_pattern = any(pattern.lower() in email.lower() for email in all_emails)
                    print(f"    Contact {i+1}: emails={all_emails}, has_pattern={has_pattern}")

    @pytest.mark.asyncio
    async def test_pagination_boundary_conditions(self):
        """
        Test pagination at various boundary conditions to identify coverage gaps.
        """
        context = Context()
        
        print("\n🔍 Testing pagination boundary conditions...")
        
        # Test with different offsets to see if contacts are missed
        offset_tests = [0, 100, 500, 1000, 2000]
        
        for offset in offset_tests:
            try:
                print(f"\nTesting with offset {offset}:")
                
                result = await list_contacts(
                    context,
                    limit=50,
                    offset=offset,
                    enable_optimization=False
                )
                
                print(f"  Offset {offset}: {result['count']} contacts found")
                
                if result['count'] > 0:
                    # Get sample to see what contacts we're finding at this offset
                    details = await get_collection_details(
                        context,
                        result['collection_id'],
                        fields=["id", "email", "date_created"],
                        limit=2
                    )
                    
                    for contact in details.get('contacts', []):
                        print(f"    Contact ID {contact.get('id')}: {contact.get('email', 'no-email')}")
                
            except Exception as e:
                print(f"  Offset {offset}: ERROR - {e}")
                
    @pytest.mark.asyncio
    async def test_pagination_exhaustive_search(self):
        """
        Test if we can implement exhaustive pagination to find all contacts.
        """
        context = Context()
        
        print("\n🔍 Testing exhaustive pagination search...")
        
        from src.mcp.tools_collections import get_api_client
        api_client = get_api_client()
        
        # Try to get a sense of total contacts by paginating until empty
        batch_size = 200
        total_contacts_found = 0
        offset = 0
        max_batches = 10  # Limit for testing
        
        print(f"Searching in batches of {batch_size} contacts:")
        
        for batch_num in range(max_batches):
            try:
                response = await api_client.get_contacts(
                    limit=batch_size,
                    offset=offset,
                    include_custom_fields=True,
                    include_tags=True
                )
                
                contacts = response.get('contacts', [])
                batch_count = len(contacts)
                total_contacts_found += batch_count
                
                print(f"  Batch {batch_num + 1} (offset {offset}): {batch_count} contacts")
                
                if batch_count == 0:
                    print(f"  ✅ Reached end of data at offset {offset}")
                    break
                    
                offset += batch_size
                
            except Exception as e:
                print(f"  ❌ Batch {batch_num + 1} failed: {e}")
                break
        
        print("\nExhaustive search summary:")
        print(f"  Total contacts found: {total_contacts_found}")
        print(f"  Batches searched: {batch_num + 1}")
        print(f"  Final offset: {offset}")
        
        # Compare with our current limited search
        limited_result = await list_contacts(
            context,
            limit=500,  # Our current effective limit
            enable_optimization=False
        )
        
        print(f"  Current limited search: {limited_result['count']} contacts")
        
        coverage_ratio = limited_result['count'] / max(total_contacts_found, 1)
        print(f"  Coverage ratio: {coverage_ratio:.1%}")
        
        if coverage_ratio < 0.8:
            print("  ⚠️  Pagination coverage issue detected!")
            print(f"     Current search only covers {coverage_ratio:.1%} of available contacts")
            return False
        else:
            print("  ✅ Pagination coverage appears adequate")
            return True