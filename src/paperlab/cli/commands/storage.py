"""CLI commands for R2 storage operations.

M3 Scope: Read-only operations for testing R2 connectivity.
Upload operations deferred to M6.
"""

import sys

from paperlab.data.storage import R2Storage


def presigned_url(remote_key: str, expiry: int) -> int:
    """Generate presigned URL for R2 object.

    Args:
        remote_key: R2 object key (e.g., submissions/uuid_page01.jpg)
        expiry: URL expiry in seconds

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        storage = R2Storage()
        url = storage.generate_presigned_url(remote_key, expiry)
        print(f"✓ Presigned URL (expires in {expiry}s):")
        print(url)
        return 0
    except Exception as e:
        print(f"✗ Failed to generate URL: {e}", file=sys.stderr)
        return 1


def download(remote_key: str, local_path: str) -> int:
    """Download image from R2 to local filesystem.

    Args:
        remote_key: R2 object key
        local_path: Local filesystem path to save image

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        storage = R2Storage()
        storage.download_image(remote_key, local_path)
        print(f"✓ Downloaded: {local_path}")
        return 0
    except Exception as e:
        print(f"✗ Download failed: {e}", file=sys.stderr)
        return 1
