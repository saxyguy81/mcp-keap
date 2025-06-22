"""
Unit Tests for Field Name Resolution

Tests the CustomFieldManager and field name to ID resolution functionality
without requiring API calls.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.mcp.tools_collections import CustomFieldManager, get_field_manager, _resolve_custom_field_names_in_filters


class TestCustomFieldManager:
    """Test CustomFieldManager functionality"""

    def test_field_manager_initialization(self):
        """Test CustomFieldManager initializes correctly"""
        manager = CustomFieldManager()
        assert manager.field_definitions == {}
        assert manager.name_to_id_mapping == {}
        assert manager.loaded == False

    def test_manual_field_setup(self):
        """Test manual field definition setup for testing"""
        manager = CustomFieldManager()
        
        # Manually populate for testing (simulating what load_field_definitions does)
        manager.field_definitions[239] = {
            'name': "6FN Next Date/Time",
            'type': 'datetime',
            'definition': {"id": 239, "label": "6FN Next Date/Time"}
        }
        manager.name_to_id_mapping["6FN Next Date/Time"] = 239
        manager.loaded = True
        
        assert 239 in manager.field_definitions
        assert manager.field_definitions[239]['name'] == "6FN Next Date/Time"
        assert manager.name_to_id_mapping["6FN Next Date/Time"] == 239

    def test_get_field_id(self):
        """Test field ID retrieval by name"""
        manager = CustomFieldManager()
        
        # Setup test data
        manager.name_to_id_mapping["6FN Next Date/Time"] = 239
        manager.loaded = True
        
        assert manager.get_field_id("6FN Next Date/Time") == 239
        assert manager.get_field_id("Non-existent Field") is None

    def test_get_all_field_names(self):
        """Test getting all field names"""
        manager = CustomFieldManager()
        
        # Setup test data
        manager.name_to_id_mapping = {
            "6FN Next Date/Time": 239,
            "Member Expire Date": 240
        }
        manager.loaded = True
        
        field_names = manager.get_all_field_names()
        assert "6FN Next Date/Time" in field_names
        assert "Member Expire Date" in field_names
        assert len(field_names) == 2

    def test_singleton_field_manager(self):
        """Test that get_field_manager returns singleton"""
        manager1 = get_field_manager()
        manager2 = get_field_manager()
        assert manager1 is manager2


class TestFieldNameFilters:
    """Test field name filter resolution"""

    @pytest.mark.asyncio
    async def test_resolve_field_names_to_ids(self):
        """Test field name to ID resolution in filters"""
        # Mock the field manager
        field_manager = CustomFieldManager()
        field_manager.name_to_id_mapping["6FN Next Date/Time"] = 239
        field_manager.loaded = True
        
        # Mock get_field_manager to return our test manager
        import src.mcp.tools_collections
        original_get_field_manager = src.mcp.tools_collections.get_field_manager
        src.mcp.tools_collections.get_field_manager = lambda: field_manager
        
        try:
            filters = [
                {"field": "6FN Next Date/Time", "operator": "equals", "value": "2025-06-20T18:30:00.000+0000"}
            ]
            
            resolved_filters = await _resolve_custom_field_names_in_filters(filters)
            
            assert len(resolved_filters) == 1
            assert resolved_filters[0]["field"] == "custom_fields.239"
            assert resolved_filters[0]["operator"] == "equals"
            assert resolved_filters[0]["value"] == "2025-06-20T18:30:00.000+0000"
        
        finally:
            # Restore original function
            src.mcp.tools_collections.get_field_manager = original_get_field_manager

    @pytest.mark.asyncio
    async def test_standard_fields_unchanged(self):
        """Test that standard fields are not modified"""
        field_manager = CustomFieldManager()
        field_manager.loaded = True
        
        import src.mcp.tools_collections
        original_get_field_manager = src.mcp.tools_collections.get_field_manager
        src.mcp.tools_collections.get_field_manager = lambda: field_manager
        
        try:
            filters = [
                {"field": "email", "operator": "contains", "value": "@gmail.com"},
                {"field": "given_name", "operator": "equals", "value": "Scott"}
            ]
            
            resolved_filters = await _resolve_custom_field_names_in_filters(filters)
            
            assert len(resolved_filters) == 2
            assert resolved_filters[0]["field"] == "email"
            assert resolved_filters[1]["field"] == "given_name"
        
        finally:
            src.mcp.tools_collections.get_field_manager = original_get_field_manager

    @pytest.mark.asyncio
    async def test_explicit_field_id_usage(self):
        """Test explicit field_id parameter usage"""
        field_manager = CustomFieldManager()
        field_manager.loaded = True
        
        import src.mcp.tools_collections
        original_get_field_manager = src.mcp.tools_collections.get_field_manager
        src.mcp.tools_collections.get_field_manager = lambda: field_manager
        
        try:
            filters = [
                {"field_id": "239", "operator": "equals", "value": "test"},
                {"field_id": "custom_fields.240", "operator": "is_not_null", "value": ""}
            ]
            
            resolved_filters = await _resolve_custom_field_names_in_filters(filters)
            
            assert len(resolved_filters) == 2
            assert resolved_filters[0]["field"] == "custom_fields.239"
            assert resolved_filters[1]["field"] == "custom_fields.240"
            assert "field_id" not in resolved_filters[0]
            assert "field_id" not in resolved_filters[1]
        
        finally:
            src.mcp.tools_collections.get_field_manager = original_get_field_manager

    @pytest.mark.asyncio
    async def test_unknown_field_name_warning(self):
        """Test handling of unknown field names"""
        field_manager = CustomFieldManager()
        field_manager.loaded = True
        
        import src.mcp.tools_collections
        original_get_field_manager = src.mcp.tools_collections.get_field_manager
        src.mcp.tools_collections.get_field_manager = lambda: field_manager
        
        try:
            filters = [
                {"field": "Unknown Field Name", "operator": "equals", "value": "test"}
            ]
            
            resolved_filters = await _resolve_custom_field_names_in_filters(filters)
            
            # Unknown field should remain unchanged
            assert len(resolved_filters) == 1
            assert resolved_filters[0]["field"] == "Unknown Field Name"
        
        finally:
            src.mcp.tools_collections.get_field_manager = original_get_field_manager