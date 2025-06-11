"""
Tests for Pydantic schema definitions.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.schemas.definitions import (
    FilterOperator,
    FilterCondition,
    LogicalOperator,
    LogicalGroup,
    ContactQueryRequest,
    TagQueryRequest,
    ModifyTagsRequest,
    ContactIncludeSpec,
    TagIncludeSpec,
    Contact,
    Tag,
    TagCategory,
    ApiCallInfo,
    QueryMetadata,
    QueryResponse,
    ErrorResponse,
    HealthStatus,
)


class TestFilterOperator:
    def test_filter_operator_values(self):
        """Test filter operator enum values."""
        assert FilterOperator.EQUALS == "EQUALS"
        assert FilterOperator.CONTAINS == "CONTAINS"
        assert FilterOperator.GREATER_THAN == "GREATER_THAN"
        assert FilterOperator.BETWEEN == "BETWEEN"

    def test_filter_operator_membership(self):
        """Test filter operator membership."""
        assert FilterOperator.EQUALS in FilterOperator
        assert "EQUALS" in [op.value for op in FilterOperator]


class TestFilterCondition:
    def test_filter_condition_valid(self):
        """Test valid filter condition creation."""
        condition = FilterCondition(
            field="email", operator=FilterOperator.CONTAINS, value="@example.com"
        )

        assert condition.field == "email"
        assert condition.operator == FilterOperator.CONTAINS
        assert condition.value == "@example.com"

    def test_filter_condition_string_operator(self):
        """Test filter condition with string operator."""
        condition = FilterCondition(field="name", operator="EQUALS", value="John")

        assert condition.operator == FilterOperator.EQUALS

    def test_filter_condition_list_value(self):
        """Test filter condition with list value."""
        condition = FilterCondition(
            field="id", operator=FilterOperator.IN, value=[1, 2, 3]
        )

        assert condition.value == [1, 2, 3]

    def test_filter_condition_missing_field(self):
        """Test filter condition validation with missing field."""
        with pytest.raises(ValidationError):
            FilterCondition(operator=FilterOperator.EQUALS, value="test")


class TestLogicalGroup:
    def test_logical_group_valid(self):
        """Test valid logical group creation."""
        condition1 = FilterCondition(field="name", operator="EQUALS", value="John")
        condition2 = FilterCondition(
            field="email", operator="CONTAINS", value="@example"
        )

        group = LogicalGroup(
            operator=LogicalOperator.AND, conditions=[condition1, condition2]
        )

        assert group.operator == LogicalOperator.AND
        assert len(group.conditions) == 2

    def test_logical_group_nested(self):
        """Test nested logical groups."""
        inner_condition = FilterCondition(
            field="age", operator="GREATER_THAN", value=18
        )
        inner_group = LogicalGroup(
            operator=LogicalOperator.NOT, conditions=[inner_condition]
        )

        outer_condition = FilterCondition(field="active", operator="EQUALS", value=True)
        outer_group = LogicalGroup(
            operator=LogicalOperator.AND, conditions=[outer_condition, inner_group]
        )

        assert len(outer_group.conditions) == 2
        assert isinstance(outer_group.conditions[1], LogicalGroup)


class TestContactQueryRequest:
    def test_contact_query_request_basic(self):
        """Test basic contact query request."""
        request = ContactQueryRequest()

        assert request.filters == []
        assert request.limit == 200
        assert request.offset == 0
        assert request.order_by is None
        assert request.order_direction == "ASC"
        assert request.include is None

    def test_contact_query_request_with_filters(self):
        """Test contact query request with filters."""
        condition = FilterCondition(
            field="email", operator="CONTAINS", value="@example"
        )
        request = ContactQueryRequest(
            filters=[condition],
            limit=100,
            offset=50,
            order_by="name",
            order_direction="DESC",
        )

        assert len(request.filters) == 1
        assert request.limit == 100
        assert request.offset == 50
        assert request.order_by == "name"
        assert request.order_direction == "DESC"

    def test_contact_query_request_invalid_limit(self):
        """Test contact query request with invalid limit."""
        with pytest.raises(ValidationError):
            ContactQueryRequest(limit=0)

    def test_contact_query_request_invalid_offset(self):
        """Test contact query request with invalid offset."""
        with pytest.raises(ValidationError):
            ContactQueryRequest(offset=-1)


class TestTagQueryRequest:
    def test_tag_query_request_basic(self):
        """Test basic tag query request."""
        request = TagQueryRequest()

        assert request.filters == []
        assert request.include_categories is True
        assert request.limit == 1000

    def test_tag_query_request_custom(self):
        """Test custom tag query request."""
        request = TagQueryRequest(include_categories=False, limit=500)

        assert request.include_categories is False
        assert request.limit == 500


class TestModifyTagsRequest:
    def test_modify_tags_request_basic(self):
        """Test basic modify tags request."""
        request = ModifyTagsRequest(contact_ids=[101, 102], tags_to_add=[1, 2])

        assert request.contact_ids == [101, 102]
        assert request.tags_to_add == [1, 2]
        assert request.tags_to_remove == []

    def test_modify_tags_request_remove(self):
        """Test modify tags request for removal."""
        request = ModifyTagsRequest(contact_ids=[101], tags_to_remove=[1])

        assert request.tags_to_remove == [1]
        assert request.tags_to_add == []

    def test_modify_tags_request_invalid_contact_ids(self):
        """Test modify tags request with invalid contact IDs."""
        with pytest.raises(ValidationError):
            ModifyTagsRequest(
                contact_ids=[0, -1],  # Invalid IDs
                tags_to_add=[1],
            )


class TestIncludeSpecs:
    def test_contact_include_spec(self):
        """Test contact include specification."""
        spec = ContactIncludeSpec(
            fields=["id", "given_name", "email"],
            include_tags=True,
            include_custom_fields=True,
        )

        assert "id" in spec.fields
        assert spec.include_tags is True
        assert spec.include_custom_fields is True

    def test_tag_include_spec(self):
        """Test tag include specification."""
        spec = TagIncludeSpec(include_category=True, include_description=False)

        assert spec.include_category is True
        assert spec.include_description is False


class TestContact:
    def test_contact_creation(self):
        """Test contact model creation."""
        contact = Contact(
            id=1, given_name="John", family_name="Doe", email="john@example.com"
        )

        assert contact.id == 1
        assert contact.given_name == "John"
        assert contact.family_name == "Doe"
        assert contact.email == "john@example.com"

    def test_contact_optional_fields(self):
        """Test contact with optional fields."""
        contact = Contact(id=1)

        assert contact.id == 1
        assert contact.given_name is None
        assert contact.email is None
        assert contact.phone1 is None
        assert contact.address is None

    def test_contact_with_all_fields(self):
        """Test contact with all fields populated."""
        now = datetime.now()
        contact = Contact(
            id=1,
            given_name="John",
            family_name="Doe",
            email="john@example.com",
            phone1="555-1234",
            phone2="555-5678",
            company="ACME Corp",
            website="https://acme.com",
            address={"line1": "123 Main St", "city": "Anytown"},
            custom_fields=[{"id": 7, "content": "VIP"}],
            tags=[{"id": 1, "name": "Customer"}],
            date_created=now,
            last_updated=now,
        )

        assert contact.given_name == "John"
        assert contact.email == "john@example.com"
        assert contact.company == "ACME Corp"
        assert contact.date_created == now


class TestTag:
    def test_tag_creation(self):
        """Test tag model creation."""
        tag = Tag(id=1, name="VIP Customer")

        assert tag.id == 1
        assert tag.name == "VIP Customer"
        assert tag.description is None
        assert tag.category is None

    def test_tag_with_category(self):
        """Test tag with category."""
        tag = Tag(
            id=1,
            name="VIP Customer",
            description="High value customer",
            category={"id": 1, "name": "Customer Types"},
        )

        assert tag.description == "High value customer"
        assert tag.category["name"] == "Customer Types"


class TestTagCategory:
    def test_tag_category_creation(self):
        """Test tag category creation."""
        category = TagCategory(
            id=1,
            name="Customer Types",
            description="Categories for customer segmentation",
        )

        assert category.id == 1
        assert category.name == "Customer Types"
        assert category.description == "Categories for customer segmentation"


class TestApiCallInfo:
    def test_api_call_info_creation(self):
        """Test API call info creation."""
        info = ApiCallInfo(
            method="GET",
            endpoint="/contacts",
            duration_ms=150.5,
            status_code=200,
            cached=False,
        )

        assert info.method == "GET"
        assert info.endpoint == "/contacts"
        assert info.status_code == 200
        assert info.duration_ms == 150.5
        assert info.cached is False

    def test_api_call_info_validation(self):
        """Test API call info validation."""
        with pytest.raises(ValidationError):
            ApiCallInfo(
                method="INVALID",
                endpoint="/contacts",
                status_code=200,
                response_time_ms=150.0,
                timestamp=datetime.now(),
            )


class TestQueryMetadata:
    def test_query_metadata_creation(self):
        """Test query metadata creation."""
        api_call = ApiCallInfo(
            method="GET",
            endpoint="/contacts",
            status_code=200,
            duration_ms=150.0,
            cached=False,
        )

        metadata = QueryMetadata(
            total_duration_ms=200.0,
            api_calls=[api_call],
            cache_hit=False,
            strategy_used="server_side",
            filters_applied=2,
            results_count=50,
        )

        assert metadata.total_duration_ms == 200.0
        assert len(metadata.api_calls) == 1
        assert metadata.cache_hit is False
        assert metadata.strategy_used == "server_side"
        assert metadata.filters_applied == 2
        assert metadata.results_count == 50


class TestQueryResponse:
    def test_query_response_creation(self):
        """Test query response creation."""
        contact = Contact(id=1, given_name="John")
        metadata = QueryMetadata(
            total_duration_ms=100.0, api_calls=[], cache_hit=False, results_count=1
        )

        response = QueryResponse(data=[contact.dict()], metadata=metadata)

        assert len(response.data) == 1
        assert response.metadata.total_duration_ms == 100.0
        assert response.metadata.results_count == 1


class TestErrorResponse:
    def test_error_response_creation(self):
        """Test error response creation."""
        now = datetime.now()
        error = ErrorResponse(
            error="INVALID_REQUEST", message="Missing required field", timestamp=now
        )

        assert error.error == "INVALID_REQUEST"
        assert error.message == "Missing required field"
        assert error.timestamp == now
        assert error.details is None

    def test_error_response_with_details(self):
        """Test error response with details."""
        error = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Field validation failed",
            details={"field": "email", "reason": "invalid format"},
        )

        assert error.details["field"] == "email"
        assert error.details["reason"] == "invalid format"


class TestHealthStatus:
    def test_health_status_creation(self):
        """Test health status creation."""
        now = datetime.now()
        health = HealthStatus(
            status="healthy",
            timestamp=now,
            checks={"api_available": True, "cache_available": True},
            response_time_ms=50.0,
        )

        assert health.status == "healthy"
        assert health.timestamp == now
        assert health.checks["api_available"] is True
        assert health.checks["cache_available"] is True
        assert health.response_time_ms == 50.0

    def test_health_status_validation(self):
        """Test health status validation."""
        # Test with valid status
        health = HealthStatus(
            status="healthy",
            timestamp=datetime.now(),
            checks={"api_available": True},
            response_time_ms=100.0,
        )
        assert health.status == "healthy"


class TestSchemaIntegration:
    def test_complex_query_request(self):
        """Test complex query request with nested structures."""
        # Create nested filter conditions
        name_condition = FilterCondition(
            field="given_name", operator="EQUALS", value="John"
        )
        email_condition = FilterCondition(
            field="email", operator="CONTAINS", value="@example"
        )

        # Create logical group
        and_group = LogicalGroup(
            operator="AND", conditions=[name_condition, email_condition]
        )

        # Create main request
        request = ContactQueryRequest(
            filters=[and_group],
            limit=50,
            include=["id", "given_name", "email_addresses"],
        )

        assert len(request.filters) == 1
        assert isinstance(request.filters[0], LogicalGroup)
        assert len(request.filters[0].conditions) == 2

    def test_response_with_multiple_contacts(self):
        """Test response with multiple contacts."""
        contacts = [
            Contact(id=1, given_name="John", family_name="Doe"),
            Contact(id=2, given_name="Jane", family_name="Smith"),
        ]

        metadata = QueryMetadata(
            total_duration_ms=50.0, api_calls=[], cache_hit=True, results_count=2
        )

        response = QueryResponse(data=[c.dict() for c in contacts], metadata=metadata)

        assert len(response.data) == 2
        assert response.data[0]["given_name"] == "John"
        assert response.data[1]["given_name"] == "Jane"
        assert response.metadata.cache_hit is True

    def test_schema_serialization(self):
        """Test schema serialization to dict."""
        contact = Contact(
            id=1, given_name="John", family_name="Doe", email="john@example.com"
        )

        contact_dict = contact.dict()

        assert contact_dict["id"] == 1
        assert contact_dict["given_name"] == "John"
        assert contact_dict["email"] == "john@example.com"

    def test_schema_json_export(self):
        """Test schema JSON export."""
        tag = Tag(id=1, name="VIP Customer", description="High value customer")
        tag_json = tag.json()

        assert '"id":1' in tag_json.replace(" ", "")
        assert '"name":"VIPCustomer"' in tag_json.replace(" ", "")
        assert '"description":"Highvaluecustomer"' in tag_json.replace(" ", "")
