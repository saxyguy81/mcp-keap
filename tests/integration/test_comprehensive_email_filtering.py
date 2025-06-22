"""
Integration Tests for Comprehensive Email Filtering

Tests email filtering functionality with the email_addresses array structure
and comprehensive search across both optimization engine and client-side paths.
"""

import pytest
from mcp.server.fastmcp import Context
from src.mcp.tools_collections import list_contacts, get_collection_details


class TestEmailFiltering:
    """Test email filtering with email_addresses array"""

    @pytest.mark.asyncio
    async def test_email_contains_filtering(self):
        """Test email contains filtering works with email_addresses array"""
        context = Context()
        
        # Test broad email filtering
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@gmail.com"}],
            limit=10,
            enable_optimization=False
        )
        
        assert result["count"] > 0, "Should find contacts with gmail addresses"
        
        # Verify email extraction worked
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "email"],
            limit=5
        )
        
        contacts = details.get("contacts", [])
        assert len(contacts) > 0
        
        # All returned contacts should have gmail in email
        for contact in contacts:
            email = contact.get("email", "")
            assert "@gmail.com" in email.lower(), f"Contact {contact['id']} email '{email}' should contain @gmail.com"

    @pytest.mark.asyncio
    async def test_email_equals_filtering(self):
        """Test exact email matching"""
        context = Context()
        
        # Test exact email match (we know this exists from our exploration)
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "equals", "value": "smhanan@gmail.com"}],
            limit=5,
            enable_optimization=False
        )
        
        # Should find exactly 1 contact
        assert result["count"] == 1, "Should find exactly 1 contact with smhanan@gmail.com"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "given_name", "family_name", "email"],
            limit=1
        )
        
        contacts = details.get("contacts", [])
        assert len(contacts) == 1
        
        contact = contacts[0]
        assert contact["email"] == "smhanan@gmail.com"
        assert contact["given_name"] == "Scott"
        assert contact["family_name"] == "Hanan"

    @pytest.mark.asyncio
    async def test_email_is_not_null_filtering(self):
        """Test finding contacts with any email address"""
        context = Context()
        
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "is_not_null", "value": ""}],
            limit=10,
            enable_optimization=False
        )
        
        assert result["count"] > 0, "Should find contacts with email addresses"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "email"],
            limit=5
        )
        
        contacts = details.get("contacts", [])
        
        # All returned contacts should have non-empty emails
        for contact in contacts:
            email = contact.get("email", "")
            assert email is not None and email != "", f"Contact {contact['id']} should have email"
            assert "@" in email, f"Contact {contact['id']} email '{email}' should be valid"


class TestOptimizationEngineEmailFiltering:
    """Test optimization engine email filtering"""

    @pytest.mark.asyncio
    async def test_optimization_engine_email_filtering(self):
        """Test that optimization engine produces same results as client-side"""
        context = Context()
        
        test_filter = {"field": "email", "operator": "contains", "value": "@gmail.com"}
        
        # Test client-side filtering
        client_result = await list_contacts(
            context,
            filters=[test_filter],
            limit=10,
            enable_optimization=False
        )
        
        # Test optimization engine
        opt_result = await list_contacts(
            context,
            filters=[test_filter],
            limit=10,
            enable_optimization=True
        )
        
        # Results should be identical
        assert client_result["count"] == opt_result["count"], \
            f"Client-side ({client_result['count']}) and optimization engine ({opt_result['count']}) should return same count"
        
        # Verify both find contacts
        assert client_result["count"] > 0, "Both should find gmail contacts"

    @pytest.mark.asyncio
    async def test_optimization_strategy_for_email_filters(self):
        """Test that email filters use BULK_RETRIEVE strategy"""
        context = Context()
        
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "test"}],
            limit=5,
            enable_optimization=True,
            return_metrics=True
        )
        
        metrics = result.get("performance_metrics", {})
        strategy = metrics.get("strategy_used", "")
        
        # Email filters should use BULK_RETRIEVE strategy for proper email_addresses handling
        assert "BULK_RETRIEVE" in str(strategy), f"Email filters should use BULK_RETRIEVE, got {strategy}"


class TestCombinedFiltering:
    """Test combined name and email filtering"""

    @pytest.mark.asyncio
    async def test_combined_name_email_filtering(self):
        """Test filtering by both name and email"""
        context = Context()
        
        # Test Scott with any email
        result = await list_contacts(
            context,
            filters=[
                {"field": "given_name", "operator": "contains", "value": "Scott"},
                {"field": "email", "operator": "contains", "value": "@"}
            ],
            limit=15,
            enable_optimization=False
        )
        
        assert result["count"] > 0, "Should find Scott contacts with emails"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "given_name", "family_name", "email"],
            limit=10
        )
        
        contacts = details.get("contacts", [])
        
        # All contacts should be named Scott and have emails
        for contact in contacts:
            given_name = contact.get("given_name", "")
            email = contact.get("email", "")
            
            assert "scott" in given_name.lower(), f"Contact {contact['id']} should have Scott in name"
            assert "@" in email, f"Contact {contact['id']} should have valid email"

    @pytest.mark.asyncio
    async def test_specific_scott_smhanan_combination(self):
        """Test finding Scott contacts with smhanan emails specifically"""
        context = Context()
        
        result = await list_contacts(
            context,
            filters=[
                {"field": "given_name", "operator": "contains", "value": "Scott"},
                {"field": "email", "operator": "contains", "value": "smhanan"}
            ],
            limit=15,
            enable_optimization=False
        )
        
        # Based on our database exploration, we know there are 10 such contacts
        assert result["count"] >= 10, f"Should find at least 10 Scott+smhanan contacts, found {result['count']}"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "given_name", "family_name", "email"],
            limit=15
        )
        
        contacts = details.get("contacts", [])
        
        # Verify all match criteria
        for contact in contacts:
            given_name = contact.get("given_name", "")
            email = contact.get("email", "")
            
            assert "scott" in given_name.lower(), f"Contact {contact['id']} name '{given_name}' should contain Scott"
            assert "smhanan" in email.lower(), f"Contact {contact['id']} email '{email}' should contain smhanan"


class TestComprehensiveSearch:
    """Test comprehensive search functionality"""

    @pytest.mark.asyncio
    async def test_comprehensive_search_finds_newest_contacts(self):
        """Test that comprehensive search finds contacts across entire database"""
        context = Context()
        
        # Search for smhanan contacts (we know these are among the newest)
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "smhanan"}],
            limit=15,
            enable_optimization=False
        )
        
        # Should find all 10+ smhanan contacts
        assert result["count"] >= 10, f"Should find at least 10 smhanan contacts, found {result['count']}"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "given_name", "family_name", "email"],
            limit=15
        )
        
        contacts = details.get("contacts", [])
        
        # Verify we found the known smhanan contact IDs
        contact_ids = [contact["id"] for contact in contacts]
        known_smhanan_ids = [23719, 23709, 23583, 23581, 23557, 23555, 23553, 22775, 22773, 22543]
        
        found_known_ids = [cid for cid in known_smhanan_ids if cid in contact_ids]
        assert len(found_known_ids) >= 8, f"Should find most known smhanan IDs, found {len(found_known_ids)}: {found_known_ids}"

    @pytest.mark.asyncio
    async def test_email_extraction_from_email_addresses_array(self):
        """Test that email extraction works from email_addresses array, not email field"""
        context = Context()
        
        # Get any contact with email
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "is_not_null", "value": ""}],
            limit=1,
            enable_optimization=False
        )
        
        assert result["count"] > 0, "Should find at least one contact with email"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "email", "email_addresses"],
            limit=1
        )
        
        contacts = details.get("contacts", [])
        contact = contacts[0]
        
        # The extracted email should match what's in email_addresses array
        extracted_email = contact.get("email", "")
        email_addresses = contact.get("email_addresses", [])
        
        assert extracted_email is not None and extracted_email != "", "Should have extracted email"
        assert isinstance(email_addresses, list), "email_addresses should be array"
        
        if email_addresses:
            # Email should match one from the array
            array_emails = [addr.get("email", "") for addr in email_addresses if isinstance(addr, dict)]
            array_emails = [email.replace("mailto:", "") for email in array_emails]  # Handle normalization
            
            assert any(extracted_email in email or email in extracted_email for email in array_emails), \
                f"Extracted email '{extracted_email}' should match one from array {array_emails}"