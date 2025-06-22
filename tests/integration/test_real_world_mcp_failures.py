"""
Integration Tests for Real-World MCP Failures

These tests are designed to catch the specific types of failures that occur
when the MCP tools are used by actual LLMs in production scenarios.

Based on real-world failures:
1. 'str' object has no attribute 'copy' error with filtering
2. Collection behavior inconsistencies (0 contacts bug) 
3. get_collection_fields Context hashable error
4. Inaccurate diagnostics reporting
5. Data truncation issues

These scenarios weren't caught by existing integration tests.
"""

import pytest
import asyncio
import json
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_collection_details,
    get_collection_fields,
    collection_union,
    get_api_diagnostics,
    get_contact_schema,
)
from src.mcp.server import KeapMCPServer


class TestRealWorldMCPFailures:
    """Test scenarios that mirror real LLM usage patterns and failures."""

    @pytest.mark.asyncio
    async def test_invalid_filter_formats_string_instead_of_dict(self):
        """Test the exact failure: 'str' object has no attribute 'copy'"""
        context = Context()
        
        # Test Case 1: Single string instead of filter dict (actual failure case)
        with pytest.raises(ValueError, match="Invalid filter format.*expected dict.*got string"):
            await list_contacts(context, filters="given_name = Scott")
        
        # Test Case 2: Mixed string and dict in filter list
        with pytest.raises(ValueError, match="Invalid filter format.*expected dict.*got string"):
            await list_contacts(context, filters=[
                {"field": "email", "operator": "contains", "value": "@example.com"},
                "given_name = Scott"  # This should fail
            ])
        
        # Test Case 3: Other invalid types
        with pytest.raises(ValueError, match="Invalid filter format.*expected dict"):
            await list_contacts(context, filters=[123, {"field": "email", "operator": "equals", "value": "test"}])
        
        # Test Case 4: Verify correct format still works
        result = await list_contacts(context, filters=[
            {"field": "given_name", "operator": "equals", "value": "Scott"}
        ], limit=5)
        assert "collection_id" in result
        assert isinstance(result["count"], int)

    @pytest.mark.asyncio
    async def test_large_collection_zero_contacts_bug(self):
        """Test large collections returning 0 contacts when they shouldn't."""
        context = Context()
        
        # Test Case 1: Large limit with restrictive filter (should return 0)
        result = await list_contacts(context, 
            filters=[{"field": "email", "operator": "equals", "value": "nonexistent@nowhere.com"}],
            limit=200
        )
        assert result["count"] == 0
        assert result["collection_id"] is not None
        
        # Verify collection details work with empty large collection
        details = await get_collection_details(context, result["collection_id"])
        assert details["count"] == 0
        assert details["contacts"] == []
        
        # Test Case 2: Large limit with broad filter (should return > 0 if data exists)
        result = await list_contacts(context, 
            filters=[{"field": "email", "operator": "contains", "value": "@"}],
            limit=200
        )
        # Don't assert specific count since it depends on test data
        assert "collection_id" in result
        assert isinstance(result["count"], int)
        
        # Test Case 3: Collection operations on large collections
        collection1 = await list_contacts(context, limit=50)
        collection2 = await list_contacts(context, limit=100)
        
        if collection1["count"] > 0 and collection2["count"] > 0:
            union_result = await collection_union(context, [
                collection1["collection_id"], 
                collection2["collection_id"]
            ])
            assert "collection_id" in union_result
            assert isinstance(union_result["count"], int)

    @pytest.mark.asyncio
    async def test_context_hashable_errors_in_collection_fields(self):
        """Test get_collection_fields with potentially unhashable context objects."""
        context = Context()
        
        # Create a small collection first
        result = await list_contacts(context, limit=3)
        if result["count"] == 0:
            pytest.skip("No contacts available for testing")
        
        collection_id = result["collection_id"]
        
        # Test Case 1: Basic get_collection_fields (should not have hashable errors)
        try:
            # Correct function signature: get_collection_fields(collection_id, fields, ...)
            field_result = await get_collection_fields(collection_id, ["email", "given_name"])
            assert isinstance(field_result, dict)
            assert "results" in field_result
        except Exception as e:
            # If this fails, it should not be due to "unhashable type: 'Context'"
            assert "unhashable type" not in str(e).lower(), f"Context hashable error: {e}"
        
        # Test Case 2: Test with complex field names
        try:
            # Correct function signature: get_collection_fields(collection_id, fields, ...)
            field_result = await get_collection_fields(collection_id, [
                "email", 
                "custom_fields.7",  # Numeric custom field
                "6FN Next Date/Time"  # Complex custom field name
            ])
            assert isinstance(field_result, dict)
        except Exception as e:
            # Should fail gracefully, not with hashable errors
            assert "unhashable type" not in str(e).lower(), f"Context hashable error: {e}"

    @pytest.mark.asyncio
    async def test_diagnostic_accuracy_against_real_collections(self):
        """Test that diagnostic reports accurately reflect actual collection data."""
        context = Context()
        
        # Create known collections with known counts
        collection1 = await list_contacts(context, limit=5)
        collection2 = await list_contacts(context, limit=3)
        
        # Wait a moment for collections to be registered
        await asyncio.sleep(0.1)
        
        # Get diagnostics
        diagnostics = await get_api_diagnostics(context)
        
        # Test Case 1: Verify diagnostic structure
        assert "collection_diagnostics" in diagnostics
        assert "total_contacts_across_collections" in diagnostics["collection_diagnostics"]
        
        # Test Case 2: Verify counts are reasonable (not wildly inaccurate)
        reported_total = diagnostics["collection_diagnostics"]["total_contacts_across_collections"]
        actual_total = collection1["count"] + collection2["count"]
        
        # The reported total should be at least as large as our known collections
        # (may be larger due to other collections, but shouldn't be smaller)
        assert reported_total >= actual_total, \
            f"Diagnostic total {reported_total} is less than actual {actual_total}"
        
        # Test Case 3: Verify diagnostic data is reasonable (not absurdly wrong)
        # If user says they have "many more contacts than 250", diagnostics shouldn't report 250
        if reported_total < 100:  # Arbitrary threshold for "many contacts"
            # Log this for investigation but don't fail the test since we don't know actual data size
            print(f"Warning: Diagnostics report only {reported_total} contacts, which may be inaccurate")

    @pytest.mark.asyncio
    async def test_data_truncation_and_serialization(self):
        """Test handling of large data that might be truncated at 100,000 characters."""
        context = Context()
        
        # Test Case 1: Create collection and get details
        result = await list_contacts(context, limit=50)  # Larger dataset
        if result["count"] == 0:
            pytest.skip("No contacts available for testing")
        
        collection_id = result["collection_id"]
        details = await get_collection_details(context, collection_id)
        
        # Test Case 2: Verify response is JSON serializable
        try:
            json_str = json.dumps(details)
            assert isinstance(json_str, str)
        except Exception as e:
            pytest.fail(f"Collection details not JSON serializable: {e}")
        
        # Test Case 3: Check for reasonable data size limits
        json_str = json.dumps(details)
        if len(json_str) > 100000:  # 100KB threshold mentioned in user report
            print(f"Warning: Response size {len(json_str)} bytes exceeds 100KB, may be truncated")
        
        # Test Case 4: Verify critical data is preserved even if truncated
        assert "collection_id" in details
        assert "count" in details
        assert "contacts" in details
        
        # If contacts exist, verify they have basic required fields
        if details["contacts"]:
            for contact in details["contacts"][:5]:  # Check first 5
                assert "id" in contact, "Contact missing required 'id' field"

    @pytest.mark.asyncio
    async def test_rapid_consecutive_calls_llm_burst_pattern(self):
        """Test rapid consecutive calls that simulate LLM usage patterns."""
        context = Context()
        
        # Test Case 1: Rapid burst of small collections
        tasks = []
        for i in range(5):  # Reduced from 10 to avoid rate limits
            task = list_contacts(context, limit=2, offset=i*2)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify most calls succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 3, f"Too many failures in burst: {len(successful_results)}/5"
        
        # Test Case 2: Mixed valid/invalid operations in sequence
        valid_result = await list_contacts(context, limit=3)
        assert "collection_id" in valid_result
        
        # Intentional error
        try:
            await get_collection_details(context, "invalid_collection_id_12345")
        except ValueError:
            pass  # Expected error
        
        # Recovery - should still work after error
        recovery_result = await list_contacts(context, limit=2)
        assert "collection_id" in recovery_result

    @pytest.mark.asyncio
    async def test_field_resolution_with_special_characters(self):
        """Test field resolution with complex field names that might cause issues."""
        context = Context()
        
        # Get schema first to understand available fields
        schema = await get_contact_schema(context)
        custom_fields = schema.get("custom_fields", [])
        
        if not custom_fields:
            pytest.skip("No custom fields available for testing")
        
        # Test Case 1: Field names with special characters
        test_field_names = []
        for field in custom_fields[:3]:  # Test first 3 custom fields
            field_name = field.get("label", "")
            if field_name and any(char in field_name for char in "/ &()[]{}"):
                test_field_names.append(field_name)
        
        if test_field_names:
            # Try searching with complex field names
            for field_name in test_field_names:
                try:
                    result = await list_contacts(context, 
                        filters=[{"field": field_name, "operator": "is_not_null", "value": ""}],
                        limit=5
                    )
                    assert "collection_id" in result
                except Exception as e:
                    # Should not crash with field resolution errors
                    assert "copy" not in str(e).lower(), f"Field resolution error: {e}"
        
        # Test Case 2: Mixed field types in single filter
        try:
            result = await list_contacts(context, filters=[
                {"field": "email", "operator": "contains", "value": "@"},  # Standard field
                {"field_id": str(custom_fields[0]["id"]), "operator": "is_not_null", "value": ""} if custom_fields else {"field": "given_name", "operator": "is_not_null", "value": ""}  # Explicit field ID or fallback
            ], limit=5)
            assert "collection_id" in result
        except Exception as e:
            assert "copy" not in str(e).lower(), f"Mixed field type error: {e}"

    @pytest.mark.asyncio
    async def test_collection_expiration_and_cleanup(self):
        """Test operations on expired or invalid collections."""
        context = Context()
        
        # Test Case 1: Operations on non-existent collection
        with pytest.raises(ValueError, match="Collection .* not found"):
            await get_collection_details(context, "nonexistent_collection_12345")
        
        with pytest.raises(ValueError, match="Collection .* not found"):
            await collection_union(context, ["nonexistent_1", "nonexistent_2"])
        
        # Test Case 2: Create collection and test basic operations
        result = await list_contacts(context, limit=2)
        collection_id = result["collection_id"]
        
        # Should work immediately after creation
        details = await get_collection_details(context, collection_id)
        assert details["collection_id"] == collection_id

    @pytest.mark.asyncio
    async def test_malformed_filter_objects(self):
        """Test various malformed filter objects that LLMs might create."""
        context = Context()
        
        malformed_filters = [
            # Missing required keys
            [{"field": "email"}],  # Missing operator and value
            [{"operator": "equals", "value": "test"}],  # Missing field
            [{"field": "email", "value": "test"}],  # Missing operator
            
            # Empty objects
            [{}],
            
            # Wrong value types
            [{"field": None, "operator": "equals", "value": "test"}],
            [{"field": "email", "operator": None, "value": "test"}],
        ]
        
        for filters in malformed_filters:
            with pytest.raises((ValueError, TypeError)):
                await list_contacts(context, filters=filters, limit=5)

    @pytest.mark.asyncio
    async def test_empty_and_null_scenarios(self):
        """Test edge cases with empty results and null values."""
        context = Context()
        
        # Test Case 1: Empty filter list
        result = await list_contacts(context, filters=[], limit=5)
        assert "collection_id" in result
        
        # Test Case 2: None filters
        result = await list_contacts(context, filters=None, limit=5)
        assert "collection_id" in result
        
        # Test Case 3: Zero limit
        result = await list_contacts(context, filters=None, limit=0)
        assert result["count"] == 0
        
        # Test Case 4: Very restrictive filter that returns no results
        result = await list_contacts(context, 
            filters=[{"field": "email", "operator": "equals", "value": "impossible_email_that_does_not_exist_12345@nowhere.invalid"}],
            limit=10
        )
        assert result["count"] == 0
        assert "collection_id" in result
        
        # Should be able to get details of empty collection
        details = await get_collection_details(context, result["collection_id"])
        assert details["count"] == 0
        assert details["contacts"] == []


class TestMCPServerIntegration:
    """Test actual MCP server protocol communication, not just function calls."""
    
    @pytest.mark.asyncio
    async def test_mcp_server_tool_calls_with_invalid_inputs(self):
        """Test MCP server handles invalid inputs gracefully."""
        server = KeapMCPServer("test-server")
        
        # Test invalid filter format through MCP protocol
        # Note: This would require actual MCP protocol testing
        # For now, we test the server initialization and tool registration
        
        # Verify server has correct tools registered
        try:
            # Test that server doesn't crash on initialization
            assert server.name == "test-server"
            assert hasattr(server, 'mcp')
            assert hasattr(server, '_register_tools')
        except Exception as e:
            pytest.fail(f"MCP server initialization failed: {e}")

    @pytest.mark.asyncio
    async def test_mcp_server_error_recovery(self):
        """Test that MCP server recovers gracefully from errors."""
        # This is a placeholder for future MCP protocol testing
        # Would require mocking MCP client interactions
        pass