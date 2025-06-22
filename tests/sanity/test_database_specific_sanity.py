"""
Database-Specific Sanity Tests

These tests verify known data exists in the specific Keap database
and that core functionality works with real data patterns.
"""

import pytest
from mcp.server.fastmcp import Context
from src.mcp.tools_collections import list_contacts, get_collection_details, get_contact_schema


class TestKnownDataExistence:
    """Test that known data exists in the database"""

    @pytest.mark.asyncio
    async def test_smhanan_contacts_exist(self):
        """Test that all known smhanan contacts exist and are findable"""
        context = Context()
        
        # Search for all smhanan contacts
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "smhanan"}],
            limit=20,
            enable_optimization=False
        )
        
        # We know there are 10 smhanan contacts
        assert result["count"] >= 10, f"Should find at least 10 smhanan contacts, found {result['count']}"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "given_name", "family_name", "email"],
            limit=20
        )
        
        contacts = details.get("contacts", [])
        contact_ids = [contact["id"] for contact in contacts]
        
        # Known smhanan contact IDs from exploration
        known_smhanan_ids = [23719, 23709, 23583, 23581, 23557, 23555, 23553, 22775, 22773, 22543]
        
        found_known_ids = [cid for cid in known_smhanan_ids if cid in contact_ids]
        
        # Should find most of the known IDs (allowing for some variation)
        assert len(found_known_ids) >= 8, \
            f"Should find at least 8 known smhanan IDs, found {len(found_known_ids)}: {found_known_ids}"

    @pytest.mark.asyncio
    async def test_scott_hanan_primary_contact_exists(self):
        """Test that the primary Scott Hanan contact exists"""
        context = Context()
        
        # Search for Scott Hanan with specific email
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "equals", "value": "smhanan@gmail.com"}],
            limit=5,
            enable_optimization=False
        )
        
        assert result["count"] == 1, "Should find exactly 1 contact with smhanan@gmail.com"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "given_name", "family_name", "email"],
            limit=1
        )
        
        contacts = details.get("contacts", [])
        contact = contacts[0]
        
        # Verify the primary contact details
        assert contact["given_name"] == "Scott", f"Expected Scott, got {contact['given_name']}"
        assert contact["family_name"] == "Hanan", f"Expected Hanan, got {contact['family_name']}"
        assert contact["email"] == "smhanan@gmail.com"
        assert contact["id"] == 23709, f"Expected ID 23709, got {contact['id']}"

    @pytest.mark.asyncio
    async def test_email_pattern_variations(self):
        """Test that various smhanan email patterns exist"""
        context = Context()
        
        # Get all smhanan contacts
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "smhanan"}],
            limit=20,
            enable_optimization=False
        )
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "email"],
            limit=20
        )
        
        contacts = details.get("contacts", [])
        emails = [contact["email"] for contact in contacts]
        
        # Expected email patterns based on exploration
        expected_patterns = [
            "smhanan@gmail.com",
            "smhanan+test",  # Various test variants
            "smhanan+testpt@gmail.com",
            "smhanan+testmt@gmail.com"
        ]
        
        found_patterns = 0
        for pattern in expected_patterns:
            if any(pattern in email for email in emails):
                found_patterns += 1
        
        assert found_patterns >= 3, f"Should find at least 3 email patterns, found {found_patterns}"

    @pytest.mark.asyncio
    async def test_database_contact_count(self):
        """Test that database has expected number of contacts"""
        context = Context()
        
        # Get total contact count
        result = await list_contacts(
            context,
            limit=1000,  # High limit to get total
            enable_optimization=False
        )
        
        # Database should have around 1000 contacts based on exploration
        assert result["count"] >= 800, f"Expected at least 800 contacts, found {result['count']}"
        assert result["count"] <= 1200, f"Expected at most 1200 contacts, found {result['count']}"

    @pytest.mark.asyncio
    async def test_gmail_contact_distribution(self):
        """Test that there are gmail contacts in the database"""
        context = Context()
        
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "contains", "value": "@gmail.com"}],
            limit=20,
            enable_optimization=False
        )
        
        # Should find significant number of gmail contacts
        assert result["count"] >= 10, f"Should find at least 10 gmail contacts, found {result['count']}"


class TestCustomFieldDataIntegrity:
    """Test custom field data integrity"""

    @pytest.mark.asyncio
    async def test_custom_field_schema_exists(self):
        """Test that custom field schema is accessible"""
        context = Context()
        
        schema = await get_contact_schema(context)
        
        assert "custom_fields" in schema, "Schema should include custom_fields"
        
        custom_fields = schema["custom_fields"]
        assert isinstance(custom_fields, list), "custom_fields should be a list"
        assert len(custom_fields) > 0, "Should have some custom fields defined"
        
        # Look for known custom fields
        field_names = [field.get("name", "") for field in custom_fields]
        
        # Should have some date/time related fields (common in CRM)
        date_fields = [name for name in field_names if "date" in name.lower() or "time" in name.lower()]
        assert len(date_fields) > 0, f"Should have date/time fields, found: {date_fields}"

    @pytest.mark.asyncio
    async def test_6fn_custom_field_exists(self):
        """Test that 6FN custom fields exist (if present)"""
        context = Context()
        
        schema = await get_contact_schema(context)
        custom_fields = schema.get("custom_fields", [])
        field_names = [field.get("name", "") for field in custom_fields]
        
        # Look for 6FN fields
        sixfn_fields = [name for name in field_names if "6FN" in name or "6fn" in name]
        
        if sixfn_fields:
            # If 6FN fields exist, test that we can search by them
            sixfn_field = sixfn_fields[0]
            
            result = await list_contacts(
                context,
                filters=[{"field": sixfn_field, "operator": "is_not_null", "value": ""}],
                limit=5,
                enable_optimization=False
            )
            
            # Should not error (even if no results)
            assert "count" in result, f"Should handle 6FN field search: {sixfn_field}"


class TestRealWorldDataPatterns:
    """Test real-world data patterns in the database"""

    @pytest.mark.asyncio
    async def test_email_addresses_array_structure(self):
        """Test that contacts use email_addresses array structure"""
        context = Context()
        
        # Get contacts with emails
        result = await list_contacts(
            context,
            filters=[{"field": "email", "operator": "is_not_null", "value": ""}],
            limit=5,
            enable_optimization=False
        )
        
        assert result["count"] > 0, "Should find contacts with emails"
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "email", "email_addresses"],
            limit=5
        )
        
        contacts = details.get("contacts", [])
        
        for contact in contacts:
            email = contact.get("email")
            email_addresses = contact.get("email_addresses")
            
            # Should have extracted email
            assert email is not None and email != "", f"Contact {contact['id']} should have extracted email"
            
            # Should have email_addresses array
            assert isinstance(email_addresses, list), f"Contact {contact['id']} should have email_addresses array"
            
            if email_addresses:
                # Array should contain email objects
                for addr in email_addresses:
                    assert isinstance(addr, dict), "email_addresses items should be objects"
                    assert "email" in addr, "email_addresses items should have email field"

    @pytest.mark.asyncio
    async def test_name_field_population(self):
        """Test that contacts have name fields populated"""
        context = Context()
        
        # Get some contacts
        result = await list_contacts(
            context,
            limit=10,
            enable_optimization=False
        )
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "given_name", "family_name"],
            limit=10
        )
        
        contacts = details.get("contacts", [])
        
        # Most contacts should have at least one name field
        named_contacts = 0
        for contact in contacts:
            given_name = contact.get("given_name", "")
            family_name = contact.get("family_name", "")
            
            if given_name or family_name:
                named_contacts += 1
        
        # At least 50% should have names
        assert named_contacts >= len(contacts) * 0.5, \
            f"At least 50% of contacts should have names, found {named_contacts}/{len(contacts)}"

    @pytest.mark.asyncio
    async def test_newest_contacts_accessibility(self):
        """Test that newest contacts (like smhanan) are accessible"""
        context = Context()
        
        # The smhanan contacts are among the newest, so test newest contact retrieval
        result = await list_contacts(
            context,
            limit=20,  # Get recent contacts
            enable_optimization=False
        )
        
        details = await get_collection_details(
            context,
            result["collection_id"],
            fields=["id", "given_name", "family_name", "email"],
            limit=20
        )
        
        contacts = details.get("contacts", [])
        contact_ids = [contact["id"] for contact in contacts]
        
        # Should include some high ID numbers (newer contacts)
        high_ids = [cid for cid in contact_ids if cid > 20000]
        assert len(high_ids) > 0, f"Should find some newer contacts (high IDs), found IDs: {sorted(contact_ids)}"
        
        # Should find at least some smhanan contacts among recent ones
        smhanan_emails = [contact["email"] for contact in contacts if "smhanan" in contact.get("email", "").lower()]
        assert len(smhanan_emails) > 0, "Should find some smhanan contacts among recent contacts"