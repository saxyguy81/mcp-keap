"""
Unit tests for core tools_collections functions.

Tests critical helper functions and utilities without requiring API calls.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, List, Any

from src.mcp.tools_collections import (
    _normalize_email,
    _extract_email, 
    _field_matches_condition,
    _email_matches_condition,
    _contact_matches_filters,
    _apply_filters,
    CustomFieldManager
)


class TestEmailNormalization:
    """Test email normalization functions"""
    
    def test_normalize_email_basic(self):
        """Test basic email normalization"""
        assert _normalize_email("test@example.com") == "test@example.com"
        assert _normalize_email("  test@example.com  ") == "test@example.com"
    
    def test_normalize_email_with_prefixes(self):
        """Test email normalization with various prefixes"""
        assert _normalize_email("mailto:test@example.com") == "test@example.com"
        assert _normalize_email("email:test@example.com") == "test@example.com"
        assert _normalize_email("Email:test@example.com") == "test@example.com"
        assert _normalize_email("MAILTO:test@example.com") == "test@example.com"
    
    def test_normalize_email_edge_cases(self):
        """Test email normalization edge cases"""
        assert _normalize_email("") == ""
        assert _normalize_email(None) is None
        assert _normalize_email("not-an-email") == "not-an-email"
        assert _normalize_email("mailto:") == ""


class TestEmailExtraction:
    """Test email extraction from contact data"""
    
    def test_extract_email_from_email_addresses_array(self):
        """Test extracting email from email_addresses array"""
        contact = {
            "id": 123,
            "email_addresses": [
                {"email": "test@example.com", "field": "EMAIL1"},
                {"email": "second@example.com", "field": "EMAIL2"}
            ]
        }
        assert _extract_email(contact) == "test@example.com"
    
    def test_extract_email_with_mailto_prefix(self):
        """Test extracting email with mailto prefix removal"""
        contact = {
            "id": 123,
            "email_addresses": [
                {"email": "mailto:test@example.com", "field": "EMAIL1"}
            ]
        }
        assert _extract_email(contact) == "test@example.com"
    
    def test_extract_email_fallback_to_direct_field(self):
        """Test fallback to direct email field"""
        contact = {
            "id": 123,
            "email": "direct@example.com",
            "email_addresses": []
        }
        assert _extract_email(contact) == "direct@example.com"
    
    def test_extract_email_no_email_found(self):
        """Test when no email is found"""
        contact = {
            "id": 123,
            "email_addresses": []
        }
        assert _extract_email(contact) is None
    
    def test_extract_email_invalid_email_format(self):
        """Test invalid email format handling"""
        contact = {
            "id": 123,
            "email_addresses": [
                {"email": "not-an-email", "field": "EMAIL1"},
                {"email": "valid@example.com", "field": "EMAIL2"}
            ]
        }
        assert _extract_email(contact) == "valid@example.com"


class TestFieldMatching:
    """Test field matching conditions"""
    
    def test_field_matches_condition_string_equals(self):
        """Test string equals condition"""
        contact = {"given_name": "John", "family_name": "Doe"}
        assert _field_matches_condition(contact, "given_name", "equals", "John") == True
        assert _field_matches_condition(contact, "given_name", "equals", "Jane") == False
    
    def test_field_matches_condition_string_contains(self):
        """Test string contains condition"""
        contact = {"given_name": "John", "family_name": "Doe"}
        assert _field_matches_condition(contact, "given_name", "contains", "oh") == True
        assert _field_matches_condition(contact, "given_name", "contains", "Jane") == False
    
    def test_field_matches_condition_email_special_handling(self):
        """Test email field special handling"""
        contact = {
            "email_addresses": [
                {"email": "john@example.com", "field": "EMAIL1"}
            ]
        }
        assert _field_matches_condition(contact, "email", "contains", "john") == True
        assert _field_matches_condition(contact, "email", "contains", "jane") == False
    
    def test_field_matches_condition_numeric(self):
        """Test numeric field conditions"""
        contact = {"id": 123, "age": 25}
        assert _field_matches_condition(contact, "id", "equals", 123) == True
        assert _field_matches_condition(contact, "age", "greater_than", 20) == True
        assert _field_matches_condition(contact, "age", "less_than", 30) == True
    
    def test_field_matches_condition_missing_field(self):
        """Test missing field handling"""
        contact = {"given_name": "John"}
        assert _field_matches_condition(contact, "family_name", "equals", "Doe") == False


class TestEmailMatching:
    """Test email-specific matching conditions"""
    
    def test_email_matches_condition_contains(self):
        """Test email contains matching"""
        contact = {
            "email_addresses": [
                {"email": "john.doe@example.com", "field": "EMAIL1"},
                {"email": "john@work.com", "field": "EMAIL2"}
            ]
        }
        assert _email_matches_condition(contact, "contains", "john") == True
        assert _email_matches_condition(contact, "contains", "example.com") == True
        assert _email_matches_condition(contact, "contains", "jane") == False
    
    def test_email_matches_condition_equals(self):
        """Test email equals matching"""
        contact = {
            "email_addresses": [
                {"email": "john@example.com", "field": "EMAIL1"}
            ]
        }
        assert _email_matches_condition(contact, "equals", "john@example.com") == True
        assert _email_matches_condition(contact, "equals", "jane@example.com") == False
    
    def test_email_matches_condition_starts_with(self):
        """Test email starts_with matching"""
        contact = {
            "email_addresses": [
                {"email": "john.doe@example.com", "field": "EMAIL1"}
            ]
        }
        assert _email_matches_condition(contact, "starts_with", "john") == True
        assert _email_matches_condition(contact, "starts_with", "jane") == False
    
    def test_email_matches_condition_no_emails(self):
        """Test email matching with no emails"""
        contact = {"email_addresses": []}
        assert _email_matches_condition(contact, "contains", "john") == False


class TestContactMatching:
    """Test complete contact filter matching"""
    
    def test_contact_matches_filters_single_filter(self):
        """Test contact matching with single filter"""
        contact = {
            "given_name": "John",
            "email_addresses": [
                {"email": "john@example.com", "field": "EMAIL1"}
            ]
        }
        filters = [{"field": "given_name", "operator": "equals", "value": "John"}]
        assert _contact_matches_filters(contact, filters) == True
        
        filters = [{"field": "given_name", "operator": "equals", "value": "Jane"}]
        assert _contact_matches_filters(contact, filters) == False
    
    def test_contact_matches_filters_multiple_filters(self):
        """Test contact matching with multiple filters (AND logic)"""
        contact = {
            "given_name": "John",
            "family_name": "Doe",
            "email_addresses": [
                {"email": "john@example.com", "field": "EMAIL1"}
            ]
        }
        filters = [
            {"field": "given_name", "operator": "equals", "value": "John"},
            {"field": "email", "operator": "contains", "value": "example.com"}
        ]
        assert _contact_matches_filters(contact, filters) == True
        
        filters = [
            {"field": "given_name", "operator": "equals", "value": "John"},
            {"field": "email", "operator": "contains", "value": "other.com"}
        ]
        assert _contact_matches_filters(contact, filters) == False
    
    def test_contact_matches_filters_empty_filters(self):
        """Test contact matching with empty filters"""
        contact = {"given_name": "John"}
        assert _contact_matches_filters(contact, []) == True


class TestApplyFilters:
    """Test filter application to contact lists"""
    
    def test_apply_filters_basic(self):
        """Test basic filter application"""
        contacts = [
            {"id": 1, "given_name": "John", "email_addresses": [{"email": "john@example.com"}]},
            {"id": 2, "given_name": "Jane", "email_addresses": [{"email": "jane@example.com"}]},
            {"id": 3, "given_name": "Bob", "email_addresses": [{"email": "bob@other.com"}]}
        ]
        filters = [{"field": "given_name", "operator": "contains", "value": "J"}]
        
        result = _apply_filters(contacts, filters)
        assert len(result) == 2
        assert result[0]["given_name"] == "John"
        assert result[1]["given_name"] == "Jane"
    
    def test_apply_filters_no_matches(self):
        """Test filter application with no matches"""
        contacts = [
            {"id": 1, "given_name": "John"},
            {"id": 2, "given_name": "Jane"}
        ]
        filters = [{"field": "given_name", "operator": "equals", "value": "Bob"}]
        
        result = _apply_filters(contacts, filters)
        assert len(result) == 0
    
    def test_apply_filters_empty_filters(self):
        """Test filter application with empty filters"""
        contacts = [
            {"id": 1, "given_name": "John"},
            {"id": 2, "given_name": "Jane"}
        ]
        
        result = _apply_filters(contacts, [])
        assert len(result) == 2
        assert result == contacts
    
    def test_apply_filters_empty_contacts(self):
        """Test filter application with empty contact list"""
        filters = [{"field": "given_name", "operator": "equals", "value": "John"}]
        
        result = _apply_filters([], filters)
        assert len(result) == 0


class TestCustomFieldManagerUnit:
    """Test CustomFieldManager unit functionality"""
    
    def test_custom_field_manager_initialization(self):
        """Test CustomFieldManager initialization"""
        manager = CustomFieldManager()
        assert manager.field_definitions == {}
        assert manager.name_to_id_mapping == {}
        assert manager.loaded == False
    
    def test_get_field_id_success(self):
        """Test successful field ID retrieval"""
        manager = CustomFieldManager()
        manager.name_to_id_mapping["Test Field"] = 123
        manager.loaded = True
        
        assert manager.get_field_id("Test Field") == 123
    
    def test_get_field_id_not_found(self):
        """Test field ID retrieval for non-existent field"""
        manager = CustomFieldManager()
        manager.loaded = True
        
        assert manager.get_field_id("Non-existent Field") is None
    
    def test_get_all_field_names(self):
        """Test getting all field names"""
        manager = CustomFieldManager()
        manager.name_to_id_mapping = {
            "Field 1": 123,
            "Field 2": 456,
            "Field 3": 789
        }
        manager.loaded = True
        
        field_names = manager.get_all_field_names()
        assert len(field_names) == 3
        assert "Field 1" in field_names
        assert "Field 2" in field_names
        assert "Field 3" in field_names
    
    def test_get_all_field_names_empty(self):
        """Test getting field names when none exist"""
        manager = CustomFieldManager()
        manager.loaded = True
        
        field_names = manager.get_all_field_names()
        assert field_names == []