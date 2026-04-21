"""Cloudflare R2 storage client for student work images.

This module provides read-only operations for retrieving images from R2 storage
during the marking pipeline. Upload operations are deferred to M6.

Design:
- Similar to repositories but for blob storage instead of SQL
- Belongs in data layer as it handles data persistence
- Uses boto3 (AWS S3-compatible) to interact with R2
- Configured with adaptive retry for transient failures

Architecture:
- Read-only operations (M3 scope): presigned URLs, download fallback
- Write operations (M6 scope): upload, copy from staging
"""

from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from paperlab.config.settings import settings


class R2Storage:
    """Cloudflare R2 storage client for student work images.

    M3 Scope: Read-only operations (presigned URLs, download fallback)
    M6 Scope: Write operations (upload, copy from staging)

    Design: Similar to repositories but for blob storage instead of SQL.
    Belongs in data layer as it handles data persistence.
    """

    def __init__(self) -> None:
        """Initialize R2 client with credentials from environment and retry config.

        Configures boto3 with adaptive retry (3 attempts, exponential backoff).
        This handles transient failures (500, 503, connection timeout) automatically.

        Raises:
            ValueError: If required environment variables missing
        """
        # Validate environment variables
        if not settings.r2_account_id:
            raise ValueError(
                "R2 Account ID not configured.\n"
                "Set environment variable: PAPERLAB_R2_ACCOUNT_ID\n"
                "Or add to .env file: PAPERLAB_R2_ACCOUNT_ID=your-account-id\n"
                "Get credentials from Cloudflare Dashboard → R2 → Manage R2 API Tokens"
            )

        if not settings.r2_access_key_id:
            raise ValueError(
                "R2 Access Key ID not configured.\n"
                "Set environment variable: PAPERLAB_R2_ACCESS_KEY_ID\n"
                "Or add to .env file: PAPERLAB_R2_ACCESS_KEY_ID=your-access-key-id"
            )

        if not settings.r2_secret_access_key:
            raise ValueError(
                "R2 Secret Access Key not configured.\n"
                "Set environment variable: PAPERLAB_R2_SECRET_ACCESS_KEY\n"
                "Or add to .env file: PAPERLAB_R2_SECRET_ACCESS_KEY=your-secret-key"
            )

        if not settings.r2_bucket_name:
            raise ValueError(
                "R2 Bucket Name not configured.\n"
                "Set environment variable: PAPERLAB_R2_BUCKET_NAME\n"
                "Or add to .env file: PAPERLAB_R2_BUCKET_NAME=your-bucket-name"
            )

        # Configure boto3 for R2 (S3-compatible API)
        # Best practices from Cloudflare R2 documentation:
        # - signature_version=s3v4: Required for R2 authentication
        # - addressing_style=virtual: Generates virtual-host style URLs for presigned URLs
        # - region_name=auto: R2 requirement for proper signature calculation
        # - Adaptive retry: Handles transient failures (500, 503, connection timeout)
        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "virtual"},
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

        # R2 endpoint format: https://{account_id}.r2.cloudflarestorage.com
        endpoint_url = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
            config=config,
        )

        self.bucket_name = settings.r2_bucket_name

    def generate_presigned_url(self, remote_key: str, expiry_seconds: int = 86400) -> str:
        """Generate public URL for R2 object access.

        TEMPORARY IMPLEMENTATION (M7): Uses r2.dev public URLs.
        This is a non-production solution for beta testing only.

        TODO (M9): Migrate to custom domain (images.paperlab.app) for production.
        See ROADMAP.md → M9 → R2 custom domain setup.

        PRIMARY USE CASE (M3): Pass URL to LLM APIs for image fetching
        - LLM fetches image directly from R2 (no backend download)
        - Avoids bandwidth bottleneck through backend
        - Faster than download + base64 encode

        SECONDARY USE CASE (M6): Mobile app display of marked work
        - Backend generates URL for frontend image rendering

        Args:
            remote_key: R2 object key (e.g., submissions/uuid_page01.jpg)
            expiry_seconds: Ignored (r2.dev URLs don't expire, custom domains will)

        Returns:
            HTTPS URL that LLM can fetch from

        Raises:
            ValueError: If remote_key format is invalid or r2_public_url not configured
        """
        # Validate path format before URL construction (fail fast)
        from paperlab.loaders.path_utils import validate_r2_path

        validate_r2_path(remote_key)

        # Check r2_public_url is configured
        if not settings.r2_public_url:
            raise ValueError(
                "R2 public URL not configured.\n"
                "Set environment variable: PAPERLAB_R2_PUBLIC_URL\n"
                "Example: PAPERLAB_R2_PUBLIC_URL=https://pub-{hash}.r2.dev\n"
                "Get URL from: Cloudflare Dashboard → R2 → Bucket → Settings → "
                "Public Development URL"
            )

        # Construct public URL: https://pub-{hash}.r2.dev/{key}
        # Note: r2.dev URLs don't require signing or expiry - they're publicly accessible
        public_url = f"{settings.r2_public_url}/{remote_key}"

        return public_url

    def download_image(self, remote_key: str, local_path: str) -> None:
        """Download image from R2 to local filesystem.

        FALLBACK ONLY: Use if presigned URLs fail with LLM providers
        Prefer generate_presigned_url() for marking pipeline (faster, no disk I/O)

        Args:
            remote_key: R2 object key
            local_path: Local filesystem path to save image

        Raises:
            ClientError: If download fails or object doesn't exist
                - NoSuchKey: Object not found in bucket
                - NoSuchBucket: Bucket doesn't exist
                - AccessDenied (403): Invalid credentials or permissions
                - InvalidObjectState: Object in cold storage (Glacier)
                - SlowDown: Rate limited (boto3 retry handles this)
                - RequestTimeout: Network timeout (boto3 retry handles this)
                - InternalError (500): Transient server error (boto3 retry handles this)
                - ServiceUnavailable (503): Transient error (boto3 retry handles this)
            OSError: If local file system write fails
            ValueError: If remote_key format is invalid
        """
        # Validate path format before API call (fail fast)
        from paperlab.loaders.path_utils import validate_r2_path

        validate_r2_path(remote_key)

        try:
            # Ensure parent directory exists
            local_path_obj = Path(local_path)
            local_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Download file from R2
            self.client.download_file(Bucket=self.bucket_name, Key=remote_key, Filename=local_path)

        except ClientError as e:
            # Extract error details from boto3 response
            error_code = (
                e.response.get("Error", {}).get("Code", "Unknown")
                if hasattr(e, "response")
                else "Unknown"
            )

            raise ClientError(
                {
                    "Error": {
                        "Code": error_code,
                        "Message": f"Failed to download {remote_key} to {local_path}: {e}",
                    }
                },
                "download_file",
            ) from e

        except BotoCoreError as e:
            raise ClientError(
                {
                    "Error": {
                        "Code": "BotoCoreError",
                        "Message": f"boto3 error downloading {remote_key}: {e}",
                    }
                },
                "download_file",
            ) from e

        except OSError as e:
            raise OSError(f"Failed to write {remote_key} to {local_path}: {e}") from e

    # DEFERRED TO M6: Upload operations
    # def upload_image(self, file_path: str, remote_key: str) -> str:
    #     """Upload image to R2 (M6 - mobile app integration)"""
    #     pass
