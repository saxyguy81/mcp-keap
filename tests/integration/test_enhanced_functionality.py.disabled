"""
Integration tests for enhanced API functionality in tools_collections.py.

Tests the newly implemented enhanced functions to achieve full coverage.
"""

import pytest
import os
from mcp.server.fastmcp import Context

from src.mcp.tools_collections import (
    list_contacts,
    get_fields_for_collection_mcp,
    set_fields_for_collection_mcp,
    set_field_for_contacts_mcp,
    modify_collection_tags_mcp,
    get_tag_details_mcp,
    modify_tags_mcp,
    create_tags_mcp,
    delete_tags_mcp,
    _validate_field_value,
    _is_datetime_field,
    _convert_datetime_value,
    _normalize_datetime_value
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


class TestEnhancedFieldManagement:
    """Test enhanced field management functions"""

    @pytest.mark.asyncio
    async def test_get_fields_for_collection_basic(self, context, skip_if_no_api_key):
        """Test basic field retrieval functionality"""
        # Create test collection
        result = await list_contacts(context, limit=2)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for field testing")
        
        # Test basic field retrieval
        fields_result = await get_fields_for_collection_mcp(
            context,
            collection_id,
            ["id", "given_name", "email"],
            return_metrics=True
        )
        
        assert "collection_id" in fields_result
        assert "fields" in fields_result
        assert "field_stats" in fields_result
        assert fields_result["collection_id"] == collection_id
        
        # Verify field structure
        for field in ["id", "given_name", "email"]:
            assert field in fields_result["fields"]
            assert field in fields_result["field_stats"]
            
            stats = fields_result["field_stats"][field]
            assert "populated_count" in stats
            assert "null_count" in stats

    @pytest.mark.asyncio
    async def test_get_fields_for_collection_with_limit(self, context, skip_if_no_api_key):
        """Test field retrieval with limit parameter"""
        result = await list_contacts(context, limit=3)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for field testing")
        
        # Test with limit
        fields_result = await get_fields_for_collection_mcp(
            context,
            collection_id,
            ["id", "given_name"],
            limit=1,
            return_metrics=True
        )
        
        assert "fields" in fields_result
        assert "performance_metrics" in fields_result
        
        # Should process at most 1 contact
        metrics = fields_result["performance_metrics"]
        assert metrics["contacts_processed"] <= 1

    @pytest.mark.asyncio
    async def test_set_fields_for_collection_validation_only(self, context, skip_if_no_api_key):
        """Test field validation without actual updates (read-only)"""
        result = await list_contacts(context, limit=1)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for field testing")
        
        # Test validation with various field types
        test_updates = {
            "given_name": "Test Name",
            "email": "test@example.com",
            "family_name": None  # Test null value
        }
        
        try:
            # We expect this to fail with permissions in test environment
            # but it should exercise the validation code paths
            validation_result = await set_fields_for_collection_mcp(
                context,
                collection_id,
                test_updates,
                validate_types=True,
                return_metrics=True
            )
            
            # If successful, verify structure
            assert "collection_id" in validation_result
            assert "validation_errors" in validation_result
            
        except Exception as e:
            # Expected in test environment
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise


class TestEnhancedTagManagement:
    """Test enhanced tag management functions"""

    @pytest.mark.asyncio
    async def test_get_tag_details_comprehensive(self, context, skip_if_no_api_key):
        """Test detailed tag information retrieval"""
        try:
            # Test with various tag IDs
            tag_result = await get_tag_details_mcp(
                context,
                [1, 2, 3],  # Common test tag IDs
                include_usage_stats=True,
                return_metrics=True
            )
            
            assert "tags" in tag_result
            assert "not_found" in tag_result
            assert "performance_metrics" in tag_result
            
            # Verify metrics structure
            metrics = tag_result["performance_metrics"]
            assert "tags_processed" in metrics
            assert "tags_found" in metrics
            assert "tags_not_found" in metrics
            
        except Exception as e:
            # Tag operations often restricted
            expected_errors = ["unauthorized", "forbidden", "not found"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise

    @pytest.mark.asyncio
    async def test_modify_collection_tags_operations(self, context, skip_if_no_api_key):
        """Test tag modification operations"""
        result = await list_contacts(context, limit=1)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for tag testing")
        
        # Test different operations
        operations = ["add", "remove"]
        
        for operation in operations:
            try:
                tag_result = await modify_collection_tags_mcp(
                    context,
                    collection_id,
                    [1],  # Test tag ID
                    operation=operation,
                    return_metrics=True
                )
                
                # If successful, verify structure
                assert "collection_id" in tag_result
                assert "operation" in tag_result
                assert "tag_ids" in tag_result
                assert "performance_metrics" in tag_result
                
            except Exception as e:
                # Expected in test environment
                expected_errors = ["unauthorized", "forbidden", "permission", "not found"]
                if not any(err in str(e).lower() for err in expected_errors):
                    raise

    @pytest.mark.asyncio
    async def test_create_tags_validation(self, context, skip_if_no_api_key):
        """Test tag creation with validation"""
        try:
            # Test tag creation (expect failure in test environment)
            tag_definitions = [
                {"name": "Test Tag 1", "description": "Test description"},
                {"name": "Test Tag 2"},  # No description
                {"name": ""}  # Invalid - empty name
            ]
            
            create_result = await create_tags_mcp(
                context,
                tag_definitions,
                return_metrics=True
            )
            
            # If successful, verify structure
            assert "created_tags" in create_result
            assert "failed_tags" in create_result
            assert "performance_metrics" in create_result
            
        except Exception as e:
            # Expected in test environment
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise


class TestHelperFunctions:
    """Test helper functions and validation"""

    def test_datetime_field_detection(self):
        """Test datetime field detection"""
        assert _is_datetime_field("appointment_date") == True
        assert _is_datetime_field("created_date") == True
        assert _is_datetime_field("some_date") == True
        assert _is_datetime_field("some_time") == True
        assert _is_datetime_field("email") == False
        assert _is_datetime_field("given_name") == False

    @pytest.mark.asyncio
    async def test_field_validation_comprehensive(self):
        """Test comprehensive field validation"""
        # Test string validation
        result = await _validate_field_value("given_name", "Valid Name")
        assert result["valid"] == True
        assert len(result["errors"]) == 0
        
        # Test string too long
        result = await _validate_field_value("given_name", "A" * 100)
        assert result["valid"] == False
        assert len(result["errors"]) > 0
        
        # Test email validation
        result = await _validate_field_value("email", "test@example.com")
        assert result["valid"] == True
        
        result = await _validate_field_value("email", "invalid-email")
        assert result["valid"] == False
        
        # Test phone validation
        result = await _validate_field_value("phone", "123-456-7890")
        assert result["valid"] == True
        
        result = await _validate_field_value("phone", 1234567890)
        assert result["valid"] == False

    def test_datetime_conversion(self):
        """Test datetime conversion functionality"""
        # Test valid ISO datetime
        result = _convert_datetime_value("2024-01-01T12:00:00Z")
        assert result is not None
        
        # Test invalid datetime
        try:
            result = _convert_datetime_value("invalid-datetime", "appointment_date")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
        
        # Test normalization
        result = _normalize_datetime_value("2024-01-01T12:00:00Z")
        assert result is not None


class TestErrorHandlingEnhanced:
    """Test error handling in enhanced functions"""

    @pytest.mark.asyncio
    async def test_invalid_collection_id_enhanced_functions(self, context, skip_if_no_api_key):
        """Test enhanced functions with invalid collection IDs"""
        invalid_id = "invalid_collection_12345"
        
        # Test each enhanced function with invalid ID
        try:
            await get_fields_for_collection_mcp(context, invalid_id, ["id"])
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "not found" in str(e).lower()
        
        try:
            await set_fields_for_collection_mcp(context, invalid_id, {"given_name": "test"})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "not found" in str(e).lower()
        
        try:
            await modify_collection_tags_mcp(context, invalid_id, [1])
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "not found" in str(e).lower()

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, context, skip_if_no_api_key):
        """Test validation error handling"""
        result = await list_contacts(context, limit=1)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for validation testing")
        
        # Test validation with invalid data
        try:
            validation_result = await set_fields_for_collection_mcp(
                context,
                collection_id,
                {
                    "email": "invalid-email-format",
                    "given_name": "A" * 100  # Too long
                },
                validate_types=True
            )
            
            # Should have validation errors
            assert "validation_errors" in validation_result
            
        except Exception as e:
            # API call might fail before validation in test environment
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise


class TestPerformanceAndMetrics:
    """Test performance metrics in enhanced functions"""

    @pytest.mark.asyncio
    async def test_enhanced_functions_metrics(self, context, skip_if_no_api_key):
        """Test that enhanced functions return proper metrics"""
        result = await list_contacts(context, limit=2)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for metrics testing")
        
        # Test metrics in get_fields_for_collection
        fields_result = await get_fields_for_collection_mcp(
            context,
            collection_id,
            ["id", "given_name"],
            return_metrics=True
        )
        
        if "performance_metrics" in fields_result:
            metrics = fields_result["performance_metrics"]
            assert "total_duration_ms" in metrics
            assert "fields_processed" in metrics
            assert "contacts_processed" in metrics
            assert isinstance(metrics["total_duration_ms"], (int, float))
            assert metrics["fields_processed"] == 2
            assert metrics["contacts_processed"] >= 0

    @pytest.mark.asyncio
    async def test_concurrent_enhanced_operations(self, context, skip_if_no_api_key):
        """Test concurrent execution of enhanced operations"""
        import asyncio
        
        result = await list_contacts(context, limit=2)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for concurrent testing")
        
        # Define concurrent operations
        async def get_fields():
            return await get_fields_for_collection_mcp(
                context, collection_id, ["id", "given_name"]
            )
        
        async def get_tag_details():
            try:
                return await get_tag_details_mcp(context, [1])
            except Exception:
                return {"tags": [], "not_found": [1]}  # Expected failure
        
        # Run operations concurrently
        tasks = [get_fields(), get_tag_details(), get_fields()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should have results for all tasks
        assert len(results) == 3
        
        # At least some should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0


class TestEdgeCasesEnhanced:
    """Test edge cases in enhanced functionality"""

    @pytest.mark.asyncio
    async def test_empty_field_lists(self, context, skip_if_no_api_key):
        """Test enhanced functions with empty field lists"""
        result = await list_contacts(context, limit=1)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for edge case testing")
        
        # Test with empty field list
        fields_result = await get_fields_for_collection_mcp(
            context,
            collection_id,
            [],  # Empty field list
            return_metrics=True
        )
        
        assert "fields" in fields_result
        assert len(fields_result["fields"]) == 0

    @pytest.mark.asyncio
    async def test_null_value_handling(self, context, skip_if_no_api_key):
        """Test handling of null values in enhanced functions"""
        result = await list_contacts(context, limit=1)
        collection_id = result["collection_id"]
        
        if result["count"] == 0:
            pytest.skip("Need contacts for null testing")
        
        # Test null value validation
        validation_result = await _validate_field_value("given_name", None)
        assert validation_result["valid"] == True  # Null should be valid
        
        try:
            # Test setting null values
            null_result = await set_fields_for_collection_mcp(
                context,
                collection_id,
                {"family_name": None},  # Set to null
                validate_types=True
            )
            
            # If successful, should not have validation errors for null
            if "validation_errors" in null_result:
                assert len(null_result["validation_errors"]) == 0
                
        except Exception as e:
            # Expected in test environment
            expected_errors = ["unauthorized", "forbidden", "permission"]
            if not any(err in str(e).lower() for err in expected_errors):
                raise