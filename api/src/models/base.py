"""
Base models for the sales/inventory system.

This module contains base Pydantic models and common utilities
for data validation and serialization.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseEntity(BaseModel):
    """
    Base model for all entities in the system.

    Provides common fields and configuration for all models.
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )

    id: Optional[int] = Field(None, description="Unique identifier")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    def model_dump_json_safe(self) -> dict:
        """
        Export model data with JSON-safe types.

        Returns:
            Dictionary with JSON-safe values
        """
        return self.model_dump(mode="json")


class APIResponse(BaseModel):
    """
    Standard API response wrapper.
    """

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Response message")
    data: Optional[dict] = Field(None, description="Response data")
    errors: Optional[list] = Field(None, description="Error details")


class PaginationParams(BaseModel):
    """
    Standard pagination parameters.
    """

    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size
