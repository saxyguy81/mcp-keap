"""
Advanced unit tests for filter utilities - covering missing functionality
"""

import pytest
from datetime import datetime

from src.utils.filter_utils import (
    apply_complex_filters,
    filter_by_name_pattern,
    validate_filter_conditions,
    optimize_filters_for_api,
    evaluate_filter_condition,
    evaluate_logical_group,
    get_nested_value,
    parse_date_value,
)


class TestAdvancedFilterUtils:
    """Test advanced filter utilities functionality"""

    @pytest.fixture
    def sample_contacts(self):
        """Sample contact data for testing"""
        return [
            {
                "id": 1,
                "given_name": "John",
                "family_name": "Doe",
                "email_addresses": [
                    {"email": "john@example.com", "field": "EMAIL1"},
                    {"email": "j.doe@work.com", "field": "EMAIL2"},
                ],
                "tag_ids": [10, 20, 30],
                "custom_fields": [
                    {"id": 7, "content": "VIP"},
                    {"id": 8, "content": "Premium"},
                ],
                "date_created": "2024-01-15T10:30:00Z",
                "last_updated": "2024-01-20T14:45:00Z",
            },
            {
                "id": 2,
                "given_name": "Jane",
                "family_name": "Smith",
                "email_addresses": [
                    {"email": "jane.smith@company.org", "field": "EMAIL1"}
                ],
                "tag_ids": [10, 40],
                "custom_fields": [
                    {"id": 7, "content": "Regular"},
                    {"id": 9, "content": "Monthly"},
                ],
                "date_created": "2024-02-01T09:15:00Z",
                "last_updated": "2024-02-05T16:20:00Z",
            },
            {
                "id": 3,
                "given_name": "Bob",
                "family_name": "Johnson",
                "email_addresses": [{"email": "bob@personal.net", "field": "EMAIL1"}],
                "tag_ids": [30, 50],
                "custom_fields": [],
                "date_created": "2023-12-10T08:00:00Z",
                "last_updated": "2024-01-05T12:30:00Z",
            },
        ]

    def test_apply_complex_filters_nested_groups(self, sample_contacts):
        """Test applying complex nested filter groups"""
        filters = [
            {
                "type": "group",
                "operator": "AND",
                "conditions": [
                    {"field": "given_name", "operator": "!=", "value": "Bob"},
                    {
                        "type": "group",
                        "operator": "OR",
                        "conditions": [
                            {"field": "family_name", "operator": "=", "value": "Doe"},
                            {"field": "family_name", "operator": "=", "value": "Smith"},
                        ],
                    },
                ],
            }
        ]

        result = apply_complex_filters(sample_contacts, filters)

        assert len(result) == 2
        assert {contact["id"] for contact in result} == {1, 2}

    def test_apply_complex_filters_simple_conditions(self, sample_contacts):
        """Test applying complex filters with simple conditions"""
        filters = [{"field": "given_name", "operator": "contains", "value": "J"}]

        result = apply_complex_filters(sample_contacts, filters)

        assert len(result) == 2
        assert {contact["id"] for contact in result} == {1, 2}

    def test_filter_by_name_pattern_wildcard(self):
        """Test filtering by name pattern with wildcard"""
        items = [
            {"name": "john@example.com"},
            {"name": "jane@test.com"},
            {"name": "bob@personal.net"},
        ]

        result = filter_by_name_pattern(items, "*@example.com")

        assert len(result) == 1
        assert result[0]["name"] == "john@example.com"

    def test_filter_by_name_pattern_exact_match(self):
        """Test filtering by exact name pattern"""
        items = [{"name": "John"}, {"name": "Jane"}, {"name": "Bob"}]

        result = filter_by_name_pattern(items, "John")

        assert len(result) == 1
        assert result[0]["name"] == "John"

    def test_validate_filter_conditions_valid(self):
        """Test validation of valid filter conditions"""
        filters = [
            {"field": "given_name", "operator": "=", "value": "John"},
            {"field": "email", "operator": "contains", "value": "@example.com"},
            {"field": "date_created", "operator": ">=", "value": "2024-01-01"},
        ]

        # Should not raise an exception
        validate_filter_conditions(filters)

    def test_validate_filter_conditions_empty(self):
        """Test validation with empty filter list"""
        # Should not raise an exception
        validate_filter_conditions([])

    def test_optimize_filters_for_api_basic(self):
        """Test basic filter optimization for API"""
        filters = [
            {"field": "email", "operator": "=", "value": "test@example.com"},
            {"field": "given_name", "operator": "contains", "value": "John"},
        ]

        api_filters, client_filters = optimize_filters_for_api(filters)

        assert isinstance(api_filters, dict)
        assert isinstance(client_filters, list)

    def test_evaluate_filter_condition_equals(self, sample_contacts):
        """Test evaluating filter condition with equals operator"""
        condition = {"field": "given_name", "operator": "=", "value": "John"}

        result = evaluate_filter_condition(sample_contacts[0], condition)
        assert result is True

        result = evaluate_filter_condition(sample_contacts[1], condition)
        assert result is False

    def test_evaluate_filter_condition_contains(self, sample_contacts):
        """Test evaluating filter condition with contains operator"""
        condition = {"field": "given_name", "operator": "contains", "value": "J"}

        result = evaluate_filter_condition(sample_contacts[0], condition)
        assert result is True

        result = evaluate_filter_condition(sample_contacts[2], condition)
        assert result is False

    def test_evaluate_logical_group_and(self, sample_contacts):
        """Test evaluating logical group with AND operator"""
        group = {
            "operator": "AND",
            "conditions": [
                {"field": "given_name", "operator": "=", "value": "John"},
                {"field": "family_name", "operator": "=", "value": "Doe"},
            ],
        }

        result = evaluate_logical_group(sample_contacts[0], group)
        assert result is True

        result = evaluate_logical_group(sample_contacts[1], group)
        assert result is False

    def test_evaluate_logical_group_or(self, sample_contacts):
        """Test evaluating logical group with OR operator"""
        group = {
            "operator": "OR",
            "conditions": [
                {"field": "given_name", "operator": "=", "value": "John"},
                {"field": "given_name", "operator": "=", "value": "Jane"},
            ],
        }

        result = evaluate_logical_group(sample_contacts[0], group)
        assert result is True

        result = evaluate_logical_group(sample_contacts[1], group)
        assert result is True

        result = evaluate_logical_group(sample_contacts[2], group)
        assert result is False

    def test_get_nested_value_simple(self, sample_contacts):
        """Test getting nested value with simple field path"""
        value = get_nested_value(sample_contacts[0], "given_name")
        assert value == "John"

        value = get_nested_value(sample_contacts[0], "id")
        assert value == 1

    def test_get_nested_value_missing_field(self, sample_contacts):
        """Test getting nested value for missing field"""
        value = get_nested_value(sample_contacts[0], "nonexistent")
        assert value is None

    def test_parse_date_value_iso_string(self):
        """Test parsing date value from ISO string"""
        date_str = "2024-01-15T10:30:00Z"
        result = parse_date_value(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_value_datetime_object(self):
        """Test parsing date value from datetime object"""
        date_obj = datetime(2024, 1, 15, 10, 30, 0)
        result = parse_date_value(date_obj)

        assert result == date_obj

    def test_parse_date_value_invalid(self):
        """Test parsing invalid date value"""
        with pytest.raises(ValueError):
            parse_date_value("invalid-date")

    def test_apply_complex_filters_empty_filters(self, sample_contacts):
        """Test applying empty filter list"""
        result = apply_complex_filters(sample_contacts, [])

        assert len(result) == len(sample_contacts)
        assert result == sample_contacts

    def test_apply_complex_filters_no_matches(self, sample_contacts):
        """Test applying filters that match nothing"""
        filters = [{"field": "given_name", "operator": "=", "value": "NonExistent"}]

        result = apply_complex_filters(sample_contacts, filters)

        assert len(result) == 0

    def test_filter_by_name_pattern_empty_pattern(self):
        """Test filtering with empty pattern"""
        items = [{"name": "John"}, {"name": "Jane"}]

        result = filter_by_name_pattern(items, "")
        assert result == items

    def test_filter_by_name_pattern_empty_items(self):
        """Test filtering empty items list"""
        result = filter_by_name_pattern([], "test")
        assert result == []

    def test_evaluate_filter_condition_missing_field(self, sample_contacts):
        """Test evaluating condition with missing field"""
        condition = {"field": "nonexistent", "operator": "=", "value": "test"}

        result = evaluate_filter_condition(sample_contacts[0], condition)
        assert result is False

    def test_evaluate_logical_group_empty_conditions(self, sample_contacts):
        """Test evaluating logical group with empty conditions"""
        group = {"operator": "AND", "conditions": []}

        result = evaluate_logical_group(sample_contacts[0], group)
        assert result is True  # Empty AND group should return True

    def test_optimize_filters_for_api_empty_filters(self):
        """Test optimizing empty filter list"""
        api_filters, client_filters = optimize_filters_for_api([])

        assert isinstance(api_filters, dict)
        assert isinstance(client_filters, list)
        assert len(client_filters) == 0
