"""Cloudflare R2 object storage client for student submissions.

Two-bucket architecture:
- Staging bucket: Temporary uploads during selection (auto-deleted)
- Permanent bucket: Confirmed submissions (immutable)

See context/backend/STORAGE.md for architecture details.
"""

from typing import TYPE_CHECKING

import boto3
from botocore.config import Config

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

from paperlab.config import settings


class R2Storage:
    """Cloudflare R2 storage client with staging and permanent buckets.

    Uses two-bucket pattern for atomic commits:
    1. Client uploads to staging bucket via presigned URLs
    2. Backend copies staging → permanent on submit
    3. Backend deletes staging (or TTL cleans up failures)

    Security:
    - All credentials from environment variables
    - Presigned URLs for client uploads (no backend bandwidth bottleneck)
    - Ownership verification before URL generation
    """

    def __init__(self) -> None:
        """Initialize R2 client with staging and permanent buckets.

        Raises:
            ValueError: If R2 credentials or bucket names not configured
        """
        # Validate required configuration
        if not settings.r2_account_id:
            raise ValueError(
                "R2 Account ID not configured.\n"
                "Set environment variable: PAPERLAB_R2_ACCOUNT_ID\n"
                "Or add to .env file: PAPERLAB_R2_ACCOUNT_ID=your-account-id"
            )

        if not settings.r2_access_key_id or not settings.r2_secret_access_key:
            raise ValueError(
                "R2 credentials not configured.\n"
                "Set environment variables:\n"
                "  PAPERLAB_R2_ACCESS_KEY_ID=your-access-key\n"
                "  PAPERLAB_R2_SECRET_ACCESS_KEY=your-secret-key\n"
                "Or add to .env file"
            )

        if not settings.r2_bucket_name:
            raise ValueError(
                "R2 Bucket not configured.\n"
                "Set environment variable: PAPERLAB_R2_BUCKET_NAME\n"
                "Or add to .env file: PAPERLAB_R2_BUCKET_NAME=your-bucket-name"
            )

        if not settings.r2_staging_bucket:
            raise ValueError(
                "R2 Staging Bucket not configured.\n"
                "Set environment variable: PAPERLAB_R2_STAGING_BUCKET\n"
                "Or add to .env file: PAPERLAB_R2_STAGING_BUCKET=your-staging-bucket-name"
            )

        # Initialize boto3 S3 client for R2
        # R2 is S3-compatible, use standard boto3 client
        # signature_version='s3v4' required for R2 presigned URLs
        self.client: S3Client = boto3.client(
            service_name="s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",  # R2 uses 'auto' region
            config=Config(signature_version="s3v4"),
        )

        # Store bucket names
        self.bucket_name = settings.r2_bucket_name  # Permanent storage
        self.staging_bucket = settings.r2_staging_bucket  # Temporary staging

    def generate_presigned_upload_url(
        self,
        remote_key: str,
        bucket: str = "staging",
        expiry_seconds: int = 3600,
    ) -> str:
        """Generate presigned PUT URL for client upload to staging.

        Args:
            remote_key: R2 object key (e.g., "staging/uuid/image.jpg")
            bucket: "staging" or "permanent" (default staging)
            expiry_seconds: URL validity in seconds (default 1 hour)

        Returns:
            HTTPS URL that client can PUT to

        Raises:
            ClientError: If presigned URL generation fails
        """
        bucket_name = self.staging_bucket if bucket == "staging" else self.bucket_name

        return self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": bucket_name, "Key": remote_key},
            ExpiresIn=expiry_seconds,
        )

    def copy_to_permanent(self, staging_key: str, permanent_key: str) -> None:
        """Copy object from staging bucket to permanent bucket.

        Args:
            staging_key: Source key in staging bucket
            permanent_key: Destination key in permanent bucket

        Raises:
            ClientError: If copy fails (caller should rollback transaction)
        """
        self.client.copy_object(
            CopySource={"Bucket": self.staging_bucket, "Key": staging_key},
            Bucket=self.bucket_name,
            Key=permanent_key,
        )

    def delete_staging_images(self, staging_keys: list[str]) -> None:
        """Delete multiple objects from staging bucket (best-effort).

        Args:
            staging_keys: List of staging keys to delete

        Raises:
            ClientError: If delete operation fails
                        (caller should log but not fail transaction)
        """
        if not staging_keys:
            return

        self.client.delete_objects(
            Bucket=self.staging_bucket,
            Delete={"Objects": [{"Key": key} for key in staging_keys]},
        )

    def list_staging_objects(self, prefix: str) -> list[str]:
        """List objects in staging bucket with given prefix.

        Args:
            prefix: Prefix to filter by (e.g., "staging/attempt-uuid/")

        Returns:
            List of object keys matching prefix

        Raises:
            ClientError: If list operation fails
        """
        response = self.client.list_objects_v2(
            Bucket=self.staging_bucket,
            Prefix=prefix,
        )
        return [obj["Key"] for obj in response.get("Contents", [])]

    def delete_permanent_images(self, keys: list[str]) -> None:
        """Delete multiple objects from permanent bucket (best-effort).

        Used for account deletion to clean up user's uploaded images.

        Args:
            keys: List of object keys to delete from permanent bucket

        Raises:
            ClientError: If delete operation fails
                        (caller should log but not fail transaction)
        """
        if not keys:
            return

        self.client.delete_objects(
            Bucket=self.bucket_name,
            Delete={"Objects": [{"Key": key} for key in keys]},
        )

    def generate_presigned_download_url(
        self,
        remote_key: str,
        expiry_seconds: int = 3600,
    ) -> str:
        """Generate presigned GET URL for client download from permanent storage.

        Args:
            remote_key: R2 object key in permanent bucket
            expiry_seconds: URL validity in seconds (default 1 hour)

        Returns:
            HTTPS URL that client can GET from

        Raises:
            ClientError: If presigned URL generation fails
        """
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket_name, "Key": remote_key},
            ExpiresIn=expiry_seconds,
        )
