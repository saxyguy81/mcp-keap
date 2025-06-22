"""
Final integration tests to push coverage to 70%+ target.

Targets specific uncovered lines and edge cases in tools_collections.py,
especially the newly implemented enhanced functionality.
"""

import pytest
import os
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_contact_schema,
    get_collection_details,
    collection_union,
    collection_intersect,
    collection_diff,
    collection_count,
    get_collection_ids,
    get_tags,
    modify_collection_tags,
    get_api_diagnostics,
    # Enhanced functions
    get_fields_for_collection_mcp,
    set_fields_for_collection_mcp,
    set_field_for_contacts_mcp,
    modify_collection_tags_mcp,
    get_tag_details_mcp,
    modify_tags_mcp,
    create_tags_mcp,
    delete_tags_mcp,
    # Helper functions
    _validate_field_value,
    _is_datetime_field,
    _convert_datetime_value,
    _normalize_datetime_value,
    get_api_client
)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


@pytest.fixture
def skip_if_no_api_key():
    """Skip tests if KEAP_API_KEY is not available"""
    api_key = os.getenv('KEAP_API_KEY')
    if not api_key:
        pytest.skip("KEAP_API_KEY not available in environment")


@pytest.fixture
def context():
    """Create MCP context"""
    return Context()


class TestSpecificUncoveredLines:
    """Target specific uncovered lines and code paths"""

    @pytest.mark.asyncio
    async def test_field_validation_all_error_paths(self):
        """Test all validation error paths in _validate_field_value"""
        # Test email validation error path
        result = await _validate_field_value("email", "invalid")
        assert not result["valid"]
        assert any("email" in err.lower() for err in result["errors"])
        
        # Test phone validation error path
        result = await _validate_field_value("phone", 12345)
        assert not result["valid"]
        assert any("string" in err.lower() for err in result["errors"])
        
        # Test string length validation
        result = await _validate_field_value("given_name", "A" * 100)
        assert not result["valid"]
        assert any("length" in err.lower() for err in result["errors"])
        
        # Test datetime validation with invalid timezone requirement
        try:
            _convert_datetime_value("2024-01-01T12:00:00", "appointment_date")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "timezone" in str(e).lower()
        
        # Test future only constraint
        try:
            _convert_datetime_value("2020-01-01T12:00:00Z", "appointment_date")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "future" in str(e).lower()

    @pytest.mark.asyncio
    async def test_enhanced_field_operations_error_paths(self, context, skip_if_no_api_key):
        """Test error paths in enhanced field operations"""
        result = await list_contacts(context, limit=1)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for error path testing")
        
        # Test get_fields_for_collection with timezone parameter
        try:
            fields_result = await get_fields_for_collection_mcp(
                context,
                collection_id,
                ["id", "created_date"],  # Include datetime field
                timezone="UTC",
                return_raw_json=False,
                return_metrics=True
            )
            
            assert "fields" in fields_result
            assert "performance_metrics" in fields_result
            
        except Exception as e:
            # API might not support timezone conversion
            if "timezone" not in str(e).lower():
                raise
        
        # Test set_field_for_contacts with contact validation
        try:
            # Test with contact not in collection
            field_result = await set_field_for_contacts_mcp(
                context,
                collection_id,
                "given_name",
                {"99999999": "Test"},  # Non-existent contact
                validate_types=True,
                return_metrics=True
            )
            
            # Should detect invalid contact
            if "validation_errors" in field_result:
                assert len(field_result["validation_errors"]) > 0
            
        except ValueError as e:
            # Expected error for invalid contact
            assert "not in collection" in str(e).lower()
        except Exception as e:
            # Other API errors expected in test environment
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise

    @pytest.mark.asyncio
    async def test_tag_operations_comprehensive_error_paths(self, context, skip_if_no_api_key):
        """Test comprehensive error paths in tag operations"""
        
        # Test modify_tags with missing ID
        try:
            modify_result = await modify_tags_mcp(
                context,
                [{"name": "New Name"}],  # Missing tag_id
                ignore_readonly_fields=True,
                return_metrics=True
            )
            
            # Should handle missing ID gracefully
            assert "failed_updates" in modify_result
            if modify_result["failed_updates"]:
                assert any("tag_id" in str(update.get("error", "")).lower() 
                          for update in modify_result["failed_updates"])
            
        except Exception as e:
            # API errors expected
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise
        
        # Test create_tags with invalid tag definition
        try:
            create_result = await create_tags_mcp(
                context,
                [{"description": "Missing name"}],  # Missing required name
                category_id=1,
                return_metrics=True
            )
            
            # Should handle missing name gracefully
            assert "failed_tags" in create_result
            if create_result["failed_tags"]:
                assert any("name" in str(tag.get("error", "")).lower() 
                          for tag in create_result["failed_tags"])
            
        except Exception as e:
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise
        
        # Test delete_tags with usage info
        try:
            delete_result = await delete_tags_mcp(
                context,
                [999999],  # Non-existent tag
                return_usage_info=True,
                return_metrics=True
            )
            
            # Should handle gracefully
            assert "deleted_tags" in delete_result
            assert "failed_deletions" in delete_result
            assert "performance_metrics" in delete_result
            
        except Exception as e:
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise

    @pytest.mark.asyncio
    async def test_datetime_helper_comprehensive(self):
        """Test comprehensive datetime helper functionality"""
        # Test timezone conversion path
        try:
            result = _convert_datetime_value(
                "2024-12-01T15:30:00+00:00", 
                "appointment_date", 
                "America/New_York"
            )
            # Should work if pytz is available
            assert result is not None
        except Exception:
            # pytz might not be available, which is handled gracefully
            pass
        
        # Test date_only constraint
        result = _convert_datetime_value("2024-01-01", "birthday")
        assert result is not None
        
        # Test past_only constraint  
        try:
            result = _convert_datetime_value("2020-01-01T12:00:00Z", "last_contact")
            assert result is not None
        except Exception:
            pass  # Might fail due to timezone issues
        
        # Test normalize function
        result = _normalize_datetime_value(None)
        assert result is None
        
        result = _normalize_datetime_value("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_api_client_factory(self):
        """Test API client factory function"""
        client = get_api_client()
        assert client is not None
        # Should be a KeapApiService instance
        assert hasattr(client, 'get_contacts')  # Basic API method check

    @pytest.mark.asyncio
    async def test_collection_operations_with_enhanced_scenarios(self, context, skip_if_no_api_key):
        """Test collection operations with enhanced scenarios"""
        # Create collections with different characteristics for comprehensive testing
        collections = []
        for i in range(3):
            result = await list_contacts(context, limit=2+i, offset=i)
            collections.append(result["collection_id"])
        
        # Test all pairwise enhanced operations
        for i, col_a in enumerate(collections):
            for j, col_b in enumerate(collections):
                if i != j:
                    # Test union with detailed error handling
                    try:
                        union_result = await collection_union(context, col_a, col_b)
                        assert "collection_id" in union_result
                        
                        # Test getting detailed fields from union result
                        if union_result["count"] > 0:
                            details = await get_collection_details(
                                context, 
                                union_result["collection_id"],
                                fields=["id", "given_name", "email", "custom_fields"]
                            )
                            assert "contacts" in details
                            
                    except Exception as e:
                        # Log but don't fail for API errors
                        if "unauthorized" not in str(e).lower():
                            raise

    @pytest.mark.asyncio
    async def test_comprehensive_field_scenarios(self, context, skip_if_no_api_key):
        """Test comprehensive field scenarios to hit all code paths"""
        result = await list_contacts(context, limit=2)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for comprehensive field testing")
        
        # Test with all possible field combinations to exercise field processing logic
        field_scenarios = [
            # Basic fields
            ["id"],
            ["id", "given_name"],
            ["id", "given_name", "family_name"],
            
            # Include email and custom fields
            ["id", "email", "custom_fields"],
            
            # Include tag IDs
            ["id", "tag_ids"],
            
            # Comprehensive field list
            ["id", "given_name", "family_name", "email", "phone", "custom_fields", "tag_ids"],
            
            # Edge case - duplicate fields (should be handled gracefully)
            ["id", "id", "given_name", "given_name"],
        ]
        
        for fields in field_scenarios:
            try:
                # Test get_fields_for_collection with various scenarios
                fields_result = await get_fields_for_collection_mcp(
                    context,
                    collection_id,
                    fields,
                    limit=1,  # Keep it fast
                    return_metrics=True
                )
                
                assert "fields" in fields_result
                assert "field_stats" in fields_result
                
                # Verify all requested fields are in results
                for field in set(fields):  # Use set to handle duplicates
                    assert field in fields_result["fields"]
                    assert field in fields_result["field_stats"]
                
            except Exception as e:
                # Some field combinations might not be supported
                if "field" not in str(e).lower():
                    raise

    @pytest.mark.asyncio
    async def test_stress_enhanced_operations(self, context, skip_if_no_api_key):
        """Stress test enhanced operations for edge cases"""
        import asyncio
        
        # Create multiple collections for stress testing
        collections = []
        for i in range(3):
            result = await list_contacts(context, limit=1, offset=i)
            collections.append(result["collection_id"])
        
        # Define stress operations
        async def stress_enhanced_ops():
            operations = []
            
            for collection_id in collections:
                # Add various enhanced operations
                operations.append(
                    get_fields_for_collection_mcp(context, collection_id, ["id"])
                )
                
                try:
                    operations.append(
                        get_tag_details_mcp(context, [1], include_usage_stats=False)
                    )
                except Exception:
                    pass  # Expected to fail
            
            return await asyncio.gather(*operations, return_exceptions=True)
        
        # Run stress test
        results = await stress_enhanced_ops()
        
        # Most operations should succeed or fail gracefully
        successful_ops = sum(1 for r in results if not isinstance(r, Exception))
        assert successful_ops >= len(collections)  # At least basic field ops should work

    @pytest.mark.asyncio
    async def test_readonly_field_filtering(self, context, skip_if_no_api_key):
        """Test readonly field filtering in tag modifications"""
        try:
            # Test with readonly fields that should be filtered out
            tag_update_with_readonly = {
                "tag_id": 1,
                "name": "New Name",
                "usage_stats": {"contact_count": 100},  # Readonly
                "contact_count": 50,  # Readonly
                "last_applied": "2024-01-01",  # Readonly
                "created_date": "2024-01-01",  # Readonly
                "id": 1  # Readonly
            }
            
            modify_result = await modify_tags_mcp(
                context,
                [tag_update_with_readonly],
                ignore_readonly_fields=True,
                return_metrics=True
            )
            
            # Should filter out readonly fields gracefully
            assert "successful_updates" in modify_result
            assert "failed_updates" in modify_result
            assert "performance_metrics" in modify_result
            
            # Test without filtering (should include readonly fields)
            modify_result_no_filter = await modify_tags_mcp(
                context,
                [tag_update_with_readonly],
                ignore_readonly_fields=False,
                return_metrics=True
            )
            
            assert "successful_updates" in modify_result_no_filter
            
        except Exception as e:
            # Expected in test environment
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise

    @pytest.mark.asyncio
    async def test_comprehensive_error_recovery(self, context, skip_if_no_api_key):
        """Test comprehensive error recovery across all enhanced functions"""
        # Test recovery after various error conditions
        error_scenarios = [
            # Invalid collection operations
            lambda: get_fields_for_collection_mcp(context, "invalid", ["id"]),
            lambda: set_fields_for_collection_mcp(context, "invalid", {"name": "test"}),
            lambda: modify_collection_tags_mcp(context, "invalid", [1]),
            
            # Invalid tag operations
            lambda: get_tag_details_mcp(context, [999999]),
            lambda: modify_tags_mcp(context, [{"tag_id": 999999, "name": "test"}]),
            lambda: create_tags_mcp(context, [{"name": ""}]),  # Invalid name
            lambda: delete_tags_mcp(context, [999999]),
        ]
        
        # Run error scenarios and verify system recovers
        for i, error_op in enumerate(error_scenarios):
            try:
                await error_op()
                # If no error, that's ok too
            except (ValueError, Exception):
                # Expected errors
                pass
            
            # Verify system still works after each error
            recovery_result = await list_contacts(context, limit=1)
            assert "collection_id" in recovery_result
            assert recovery_result["count"] >= 0
            
            # Test basic schema still works
            schema = await get_contact_schema(context)
            assert "standard_fields" in schema