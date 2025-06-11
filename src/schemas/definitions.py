"""
Pydantic model definitions for Keap MCP service.

This module contains all the data models used throughout the application.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


class FilterOperator(str, Enum):
    """Supported filter operators."""

    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    BETWEEN = "BETWEEN"
    IN = "IN"
    NOT_IN = "NOT_IN"
    SINCE = "SINCE"
    UNTIL = "UNTIL"


class FilterCondition(BaseModel):
    """A single filter condition."""

    field: str = Field(..., description="Field name to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Union[str, int, float, List[Any]] = Field(..., description="Filter value")


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class LogicalGroup(BaseModel):
    """Group of filter conditions with logical operator."""

    operator: LogicalOperator = Field(..., description="Logical operator")
    conditions: List[Union[FilterCondition, "LogicalGroup"]] = Field(
        ..., description="Conditions in this group"
    )


class ContactQueryRequest(BaseModel):
    """Request model for contact queries."""

    filters: List[Union[FilterCondition, LogicalGroup]] = Field(
        default=[], description="Filter conditions"
    )
    limit: int = Field(default=200, ge=1, le=1000, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    order_by: Optional[str] = Field(default=None, description="Field to order by")
    order_direction: str = Field(default="ASC", description="Order direction")
    include: Optional[List[str]] = Field(
        default=None, description="Fields to include in response"
    )

    @validator("order_direction")
    def validate_order_direction(cls, v):
        if v.upper() not in ["ASC", "DESC"]:
            raise ValueError("order_direction must be ASC or DESC")
        return v.upper()


class TagQueryRequest(BaseModel):
    """Request model for tag queries."""

    filters: List[Union[FilterCondition, LogicalGroup]] = Field(
        default=[], description="Filter conditions"
    )
    include_categories: bool = Field(
        default=True, description="Include category information"
    )
    limit: int = Field(default=1000, ge=1, le=5000, description="Maximum results")


class ModifyTagsRequest(BaseModel):
    """Request model for modifying tags on contacts."""

    contact_ids: List[int] = Field(..., min_items=1, description="Contact IDs")
    tags_to_add: Optional[List[int]] = Field(default=[], description="Tag IDs to add")
    tags_to_remove: Optional[List[int]] = Field(
        default=[], description="Tag IDs to remove"
    )
    use_v2_api: bool = Field(default=True, description="Use V2 API for bulk operations")
    batch_size: Optional[int] = Field(
        default=50, ge=1, le=100, description="Batch size"
    )

    @validator("contact_ids")
    def validate_contact_ids(cls, v):
        if not v:
            raise ValueError("contact_ids cannot be empty")
        if any(id <= 0 for id in v):
            raise ValueError("All contact IDs must be positive")
        return v

    @validator("tags_to_add")
    def validate_tags_to_add(cls, v):
        if v and any(id <= 0 for id in v):
            raise ValueError("All tag IDs must be positive")
        return v

    @validator("tags_to_remove")
    def validate_tags_to_remove(cls, v):
        if v and any(id <= 0 for id in v):
            raise ValueError("All tag IDs must be positive")
        return v

    @validator("batch_size")
    def validate_batch_size(cls, v, values):
        if "contact_ids" in values and v:
            return min(v, len(values["contact_ids"]))
        return v


class ContactIncludeSpec(BaseModel):
    """Specification for which contact fields to include."""

    fields: List[str] = Field(default=[], description="Field names to include")
    include_tags: bool = Field(default=False, description="Include tag information")
    include_custom_fields: bool = Field(
        default=False, description="Include custom field data"
    )


class TagIncludeSpec(BaseModel):
    """Specification for which tag fields to include."""

    include_category: bool = Field(
        default=True, description="Include category information"
    )
    include_description: bool = Field(
        default=True, description="Include tag description"
    )


class Contact(BaseModel):
    """Contact data model."""

    id: int = Field(..., description="Contact ID")
    given_name: Optional[str] = Field(default=None, description="First name")
    family_name: Optional[str] = Field(default=None, description="Last name")
    email: Optional[str] = Field(default=None, description="Primary email")
    phone1: Optional[str] = Field(default=None, description="Primary phone")
    phone2: Optional[str] = Field(default=None, description="Secondary phone")
    company: Optional[str] = Field(default=None, description="Company name")
    website: Optional[str] = Field(default=None, description="Website URL")
    address: Optional[Dict[str, Any]] = Field(
        default=None, description="Address information"
    )
    tags: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Associated tags"
    )
    custom_fields: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Custom field data"
    )
    date_created: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    last_updated: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )


class Tag(BaseModel):
    """Tag data model."""

    id: int = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    description: Optional[str] = Field(default=None, description="Tag description")
    category: Optional[Dict[str, Any]] = Field(default=None, description="Tag category")


class TagCategory(BaseModel):
    """Tag category data model."""

    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(default=None, description="Category description")


class ApiCallInfo(BaseModel):
    """Information about an API call."""

    endpoint: str = Field(..., description="API endpoint called")
    method: str = Field(..., description="HTTP method")
    duration_ms: float = Field(..., description="Call duration in milliseconds")
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    cached: bool = Field(default=False, description="Whether result was cached")


class QueryMetadata(BaseModel):
    """Metadata about query execution."""

    total_duration_ms: float = Field(..., description="Total execution time")
    api_calls: List[ApiCallInfo] = Field(..., description="API calls made")
    cache_hit: bool = Field(default=False, description="Whether cache was hit")
    strategy_used: Optional[str] = Field(
        default=None, description="Query strategy used"
    )
    filters_applied: int = Field(default=0, description="Number of filters applied")
    results_count: int = Field(default=0, description="Number of results returned")


class QueryResponse(BaseModel):
    """Response model for queries."""

    data: List[Dict[str, Any]] = Field(..., description="Query results")
    metadata: QueryMetadata = Field(..., description="Query metadata")
    pagination: Optional[Dict[str, Any]] = Field(
        default=None, description="Pagination information"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class HealthStatus(BaseModel):
    """Health check status model."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
    checks: Dict[str, Any] = Field(default={}, description="Individual health checks")
    response_time_ms: float = Field(
        default=0, description="Response time in milliseconds"
    )


# Update forward references
LogicalGroup.model_rebuild()
