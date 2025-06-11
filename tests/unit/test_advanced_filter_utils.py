"""
Unit tests for advanced filter utilities functionality.
"""

import pytest
from datetime import datetime, timezone

from src.utils.filter_utils import (
    filter_by_name_pattern,
    validate_filter_conditions,
    evaluate_filter_condition,
    evaluate_logical_group,
    apply_complex_filters,
    get_nested_value,
    parse_date_value,
    optimize_filters_for_api,
)


class TestFilterByNamePattern:
    """Test filter_by_name_pattern functionality."""

    def test_filter_exact_match(self):
        """Test filtering with exact name match."""
        items = [
            {"name": "John", "id": 1},
            {"name": "Jane", "id": 2},
            {"name": "Bob", "id": 3},
        ]

        result = filter_by_name_pattern(items, "John")

        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_filter_wildcard_prefix(self):
        """Test filtering with wildcard prefix."""
        items = [
            {"name": "John", "id": 1},
            {"name": "Jane", "id": 2},
            {"name": "Bob", "id": 3},
        ]

        result = filter_by_name_pattern(items, "J*")

        assert len(result) == 2
        assert {item["id"] for item in result} == {1, 2}

    def test_filter_wildcard_suffix(self):
        """Test filtering with wildcard suffix."""
        items = [
            {"name": "Johnson", "id": 1},
            {"name": "Jackson", "id": 2},
            {"name": "Smith", "id": 3},
        ]

        result = filter_by_name_pattern(items, "*son")

        assert len(result) == 2
        assert {item["id"] for item in result} == {1, 2}

    def test_filter_case_insensitive(self):
        """Test case insensitive filtering."""
        items = [
            {"name": "John", "id": 1},
            {"name": "jane", "id": 2},
            {"name": "BOB", "id": 3},
        ]

        result = filter_by_name_pattern(items, "john")

        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_filter_empty_pattern(self):
        """Test filtering with empty pattern."""
        items = [{"name": "John", "id": 1}, {"name": "Jane", "id": 2}]

        result = filter_by_name_pattern(items, "")

        assert result == items

    def test_filter_empty_items(self):
        """Test filtering empty items list."""
        result = filter_by_name_pattern([], "John")

        assert result == []

    def test_filter_items_without_name(self):
        """Test filtering items without name field."""
        items = [{"id": 1}, {"name": "John", "id": 2}, {"title": "Manager", "id": 3}]

        result = filter_by_name_pattern(items, "John")

        assert len(result) == 1
        assert result[0]["id"] == 2


class TestValidateFilterConditions:
    """Test validate_filter_conditions functionality."""

    def test_validate_valid_filters(self):
        """Test validating valid filter conditions."""
        filters = [
            {"field": "name", "operator": "=", "value": "John"},
            {"field": "age", "operator": ">=", "value": 25},
        ]

        # Should not raise an exception
        validate_filter_conditions(filters)

    def test_validate_empty_filters(self):
        """Test validating empty filters."""
        # Should not raise an exception
        validate_filter_conditions([])
        validate_filter_conditions(None)

    def test_validate_missing_field(self):
        """Test validation with missing field."""
        filters = [{"operator": "=", "value": "John"}]

        with pytest.raises(ValueError, match="field"):
            validate_filter_conditions(filters)

    def test_validate_missing_operator(self):
        """Test validation with missing operator."""
        filters = [{"field": "name", "value": "John"}]

        with pytest.raises(ValueError, match="operator"):
            validate_filter_conditions(filters)

    def test_validate_missing_value(self):
        """Test validation with missing value."""
        filters = [{"field": "name", "operator": "="}]

        with pytest.raises(ValueError, match="value"):
            validate_filter_conditions(filters)

    def test_validate_logical_group(self):
        """Test validating logical group conditions."""
        filters = [
            {
                "operator": "AND",
                "conditions": [
                    {"field": "name", "operator": "=", "value": "John"},
                    {"field": "age", "operator": ">=", "value": 25},
                ],
            }
        ]

        # Should not raise an exception
        validate_filter_conditions(filters)

    def test_validate_invalid_logical_operator(self):
        """Test validation with invalid logical operator."""
        filters = [
            {
                "operator": "INVALID",
                "conditions": [{"field": "name", "operator": "=", "value": "John"}],
            }
        ]

        with pytest.raises(ValueError, match="operator"):
            validate_filter_conditions(filters)


class TestEvaluateFilterCondition:
    """Test evaluate_filter_condition functionality."""

    def test_evaluate_string_equals(self):
        """Test evaluating string equals condition."""
        item = {"name": "John", "age": 30}
        condition = {"field": "name", "operator": "EQUALS", "value": "John"}

        result = evaluate_filter_condition(item, condition)

        assert result is True

    def test_evaluate_string_not_equals(self):
        """Test evaluating string not equals condition."""
        item = {"name": "John", "age": 30}
        condition = {"field": "name", "operator": "NOT_EQUALS", "value": "Jane"}

        result = evaluate_filter_condition(item, condition)

        assert result is True

    def test_evaluate_numeric_greater_than(self):
        """Test evaluating numeric greater than condition."""
        item = {"name": "John", "age": 30}
        condition = {"field": "age", "operator": "GREATER_THAN", "value": 25}

        result = evaluate_filter_condition(item, condition)

        assert result is True

    def test_evaluate_numeric_less_than(self):
        """Test evaluating numeric less than condition."""
        item = {"name": "John", "age": 30}
        condition = {"field": "age", "operator": "LESS_THAN", "value": 25}

        result = evaluate_filter_condition(item, condition)

        assert result is False

    def test_evaluate_contains(self):
        """Test evaluating contains condition."""
        item = {"email": "john.doe@company.com"}
        condition = {"field": "email", "operator": "CONTAINS", "value": "@company.com"}

        result = evaluate_filter_condition(item, condition)

        assert result is True

    def test_evaluate_starts_with(self):
        """Test evaluating starts_with condition."""
        item = {"name": "John Doe"}
        condition = {"field": "name", "operator": "STARTS_WITH", "value": "John"}

        result = evaluate_filter_condition(item, condition)

        assert result is True

    def test_evaluate_ends_with(self):
        """Test evaluating ends_with condition."""
        item = {"name": "John Doe"}
        condition = {"field": "name", "operator": "ENDS_WITH", "value": "Doe"}

        result = evaluate_filter_condition(item, condition)

        assert result is True

    def test_evaluate_in_condition(self):
        """Test evaluating 'in' condition."""
        item = {"status": "active"}
        condition = {
            "field": "status",
            "operator": "IN",
            "value": ["active", "pending"],
        }

        result = evaluate_filter_condition(item, condition)

        assert result is True

    def test_evaluate_between_condition(self):
        """Test evaluating 'between' condition."""
        item = {"age": 30}
        condition = {"field": "age", "operator": "BETWEEN", "value": [25, 35]}

        result = evaluate_filter_condition(item, condition)

        assert result is True

    def test_evaluate_missing_field(self):
        """Test evaluating condition with missing field."""
        item = {"name": "John"}
        condition = {"field": "age", "operator": "EQUALS", "value": 30}

        result = evaluate_filter_condition(item, condition)

        assert result is False

    def test_evaluate_invalid_operator(self):
        """Test evaluating condition with invalid operator."""
        item = {"name": "John"}
        condition = {"field": "name", "operator": "invalid", "value": "John"}

        result = evaluate_filter_condition(item, condition)

        assert result is False


class TestEvaluateLogicalGroup:
    """Test evaluate_logical_group functionality."""

    def test_evaluate_and_group_all_true(self):
        """Test evaluating AND group where all conditions are true."""
        item = {"name": "John", "age": 30, "status": "active"}
        group = {
            "operator": "AND",
            "conditions": [
                {"field": "name", "operator": "=", "value": "John"},
                {"field": "age", "operator": ">=", "value": 25},
                {"field": "status", "operator": "=", "value": "active"},
            ],
        }

        result = evaluate_logical_group(item, group)

        assert result is True

    def test_evaluate_and_group_one_false(self):
        """Test evaluating AND group where one condition is false."""
        item = {"name": "John", "age": 20, "status": "active"}
        group = {
            "operator": "AND",
            "conditions": [
                {"field": "name", "operator": "=", "value": "John"},
                {"field": "age", "operator": ">=", "value": 25},
                {"field": "status", "operator": "=", "value": "active"},
            ],
        }

        result = evaluate_logical_group(item, group)

        assert result is False

    def test_evaluate_or_group_one_true(self):
        """Test evaluating OR group where one condition is true."""
        item = {"name": "John", "age": 20, "status": "inactive"}
        group = {
            "operator": "OR",
            "conditions": [
                {"field": "name", "operator": "=", "value": "John"},
                {"field": "age", "operator": ">=", "value": 25},
                {"field": "status", "operator": "=", "value": "active"},
            ],
        }

        result = evaluate_logical_group(item, group)

        assert result is True

    def test_evaluate_or_group_all_false(self):
        """Test evaluating OR group where all conditions are false."""
        item = {"name": "Jane", "age": 20, "status": "inactive"}
        group = {
            "operator": "OR",
            "conditions": [
                {"field": "name", "operator": "=", "value": "John"},
                {"field": "age", "operator": ">=", "value": 25},
                {"field": "status", "operator": "=", "value": "active"},
            ],
        }

        result = evaluate_logical_group(item, group)

        assert result is False

    def test_evaluate_not_group_true_condition(self):
        """Test evaluating NOT group with true condition."""
        item = {"name": "John"}
        group = {
            "operator": "NOT",
            "conditions": [{"field": "name", "operator": "EQUALS", "value": "John"}],
        }

        result = evaluate_logical_group(item, group)

        assert result is False

    def test_evaluate_not_group_false_condition(self):
        """Test evaluating NOT group with false condition."""
        item = {"name": "Jane"}
        group = {
            "operator": "NOT",
            "conditions": [{"field": "name", "operator": "EQUALS", "value": "John"}],
        }

        result = evaluate_logical_group(item, group)

        assert result is True

    def test_evaluate_nested_logical_groups(self):
        """Test evaluating nested logical groups."""
        item = {"name": "John", "age": 30, "status": "active", "city": "New York"}
        group = {
            "operator": "AND",
            "conditions": [
                {"field": "name", "operator": "=", "value": "John"},
                {
                    "operator": "OR",
                    "conditions": [
                        {"field": "age", "operator": "<", "value": 25},
                        {"field": "city", "operator": "=", "value": "New York"},
                    ],
                },
            ],
        }

        result = evaluate_logical_group(item, group)

        assert result is True

    def test_evaluate_invalid_logical_operator(self):
        """Test evaluating group with invalid logical operator."""
        item = {"name": "John"}
        group = {
            "operator": "INVALID",
            "conditions": [{"field": "name", "operator": "EQUALS", "value": "John"}],
        }

        result = evaluate_logical_group(item, group)

        assert result is False


class TestApplyComplexFilters:
    """Test apply_complex_filters functionality."""

    def test_apply_simple_filters(self):
        """Test applying simple filters."""
        items = [
            {"name": "John", "age": 30, "status": "active"},
            {"name": "Jane", "age": 25, "status": "inactive"},
            {"name": "Bob", "age": 35, "status": "active"},
        ]

        filters = [
            {"field": "status", "operator": "=", "value": "active"},
            {"field": "age", "operator": ">=", "value": 30},
        ]

        result = apply_complex_filters(items, filters)

        assert len(result) == 2
        assert {item["name"] for item in result} == {"John", "Bob"}

    def test_apply_logical_filters(self):
        """Test applying logical group filters."""
        items = [
            {"name": "John", "age": 30, "status": "active"},
            {"name": "Jane", "age": 25, "status": "active"},
            {"name": "Bob", "age": 35, "status": "inactive"},
        ]

        filters = [
            {
                "operator": "OR",
                "conditions": [
                    {"field": "age", "operator": ">=", "value": 35},
                    {
                        "operator": "AND",
                        "conditions": [
                            {"field": "status", "operator": "=", "value": "active"},
                            {"field": "age", "operator": "<=", "value": 25},
                        ],
                    },
                ],
            }
        ]

        result = apply_complex_filters(items, filters)

        assert len(result) == 2
        assert {item["name"] for item in result} == {"Jane", "Bob"}

    def test_apply_empty_filters(self):
        """Test applying empty filters."""
        items = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

        result = apply_complex_filters(items, [])

        assert result == items

    def test_apply_filters_empty_items(self):
        """Test applying filters to empty items."""
        filters = [{"field": "name", "operator": "=", "value": "John"}]

        result = apply_complex_filters([], filters)

        assert result == []


class TestGetNestedValue:
    """Test get_nested_value functionality."""

    def test_get_simple_value(self):
        """Test getting simple nested value."""
        item = {"name": "John", "age": 30}

        result = get_nested_value(item, "name")

        assert result == "John"

    def test_get_nested_value_dot_notation(self):
        """Test getting nested value with dot notation."""
        item = {"user": {"profile": {"name": "John Doe"}}}

        result = get_nested_value(item, "user.profile.name")

        assert result == "John Doe"

    def test_get_missing_value(self):
        """Test getting missing nested value."""
        item = {"name": "John"}

        result = get_nested_value(item, "age")

        assert result is None

    def test_get_missing_nested_value(self):
        """Test getting missing deeply nested value."""
        item = {"user": {"profile": {"name": "John"}}}

        result = get_nested_value(item, "user.profile.age")

        assert result is None

    def test_get_nested_value_partial_path(self):
        """Test getting nested value with partial missing path."""
        item = {"user": {"name": "John"}}

        result = get_nested_value(item, "user.profile.age")

        assert result is None


class TestParseDateValue:
    """Test parse_date_value functionality."""

    def test_parse_iso_date_string(self):
        """Test parsing ISO date string."""
        date_str = "2023-01-01T10:30:00Z"

        result = parse_date_value(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_simple_date_string(self):
        """Test parsing simple date string."""
        date_str = "2023-01-01"

        result = parse_date_value(date_str)

        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1

    def test_parse_datetime_object(self):
        """Test parsing datetime object."""
        date_obj = datetime(2023, 1, 1, 10, 30, 0, tzinfo=timezone.utc)

        result = parse_date_value(date_obj)

        assert result == date_obj

    def test_parse_date_with_timezone(self):
        """Test parsing date string with timezone."""
        date_str = "2023-01-01T10:30:00+05:00"

        result = parse_date_value(date_str)

        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_parse_invalid_date_string(self):
        """Test parsing invalid date string."""
        date_str = "invalid-date-string"

        with pytest.raises(ValueError):
            parse_date_value(date_str)

    def test_parse_none_value(self):
        """Test parsing None value."""
        with pytest.raises(ValueError):
            parse_date_value(None)


class TestOptimizeFiltersForApi:
    """Test optimize_filters_for_api functionality."""

    def test_optimize_simple_filters(self):
        """Test optimizing simple filters for API."""
        filters = [
            {"field": "given_name", "operator": "=", "value": "John"},
            {"field": "family_name", "operator": "=", "value": "Doe"},
            {"field": "custom_field", "operator": "=", "value": "VIP"},
        ]

        api_params, client_filters = optimize_filters_for_api(filters)

        # Should separate API-optimizable from client-side filters
        assert isinstance(api_params, dict)
        assert isinstance(client_filters, list)

        # given_name and family_name should be API optimizable
        assert len(api_params) >= 1  # At least some params should be optimizable

        # custom_field should require client-side filtering
        assert len(client_filters) >= 1

    def test_optimize_logical_filters(self):
        """Test optimizing logical group filters."""
        filters = [
            {
                "operator": "AND",
                "conditions": [
                    {"field": "given_name", "operator": "=", "value": "John"},
                    {"field": "email", "operator": "contains", "value": "@company.com"},
                ],
            }
        ]

        api_params, client_filters = optimize_filters_for_api(filters)

        # Logical groups typically require client-side processing
        assert isinstance(client_filters, list)
        assert len(client_filters) >= 1

    def test_optimize_empty_filters(self):
        """Test optimizing empty filters."""
        api_params, client_filters = optimize_filters_for_api([])

        assert api_params == {}
        assert client_filters == []

    def test_optimize_all_client_side_filters(self):
        """Test optimizing filters that are all client-side."""
        filters = [
            {"field": "custom_field", "operator": "=", "value": "VIP"},
            {"field": "tags", "operator": "contains", "value": "customer"},
        ]

        api_params, client_filters = optimize_filters_for_api(filters)

        # Should have minimal or no API params
        assert len(client_filters) >= 1  # Should have client-side filters

    def test_optimize_mixed_filters(self):
        """Test optimizing mix of API and client-side filters."""
        filters = [
            {
                "field": "email",
                "operator": "=",
                "value": "john@example.com",
            },  # API optimizable
            {
                "field": "given_name",
                "operator": "=",
                "value": "John",
            },  # API optimizable
            {
                "field": "custom_field",
                "operator": "=",
                "value": "VIP",
            },  # Client-side only
        ]

        api_params, client_filters = optimize_filters_for_api(filters)

        # Should have both API params and client filters
        assert len(api_params) >= 1  # Should have API parameters
        assert len(client_filters) >= 1  # Should have client-side filters
