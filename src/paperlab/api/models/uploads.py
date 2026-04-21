"""API models for upload endpoints (Flow 2).

Request/response models for presigned URL generation and staging management.
"""

from pydantic import BaseModel, ConfigDict, Field


class PresignedUrlRequest(BaseModel):
    """Request to generate presigned upload URL."""

    attempt_uuid: str = Field(..., description="Attempt this upload belongs to")
    filename: str = Field(
        ...,
        description="UUID-based filename, e.g., 'f8e9d0c1-b2a3-4567-8901-23456789abcd.jpg'",
    )

    model_config = ConfigDict(populate_by_name=True)


class PresignedUrlResponse(BaseModel):
    """Response with presigned upload URL."""

    upload_url: str = Field(..., description="Presigned PUT URL (1-hour expiry)")
    staging_key: str = Field(..., description="Full staging key for client tracking")


class StagingListResponse(BaseModel):
    """Response listing staging images for an attempt."""

    staging_keys: list[str]
