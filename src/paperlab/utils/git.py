"""Git utilities for tracking code versions in test runs."""

import subprocess
from pathlib import Path

from paperlab.config.constants import GitSettings


class GitProvider:
    """Provides git commit hash for tracking test execution versions."""

    def __init__(self, repo_path: Path | None = None) -> None:
        """Initialize git provider.

        Args:
            repo_path: Path to git repository (defaults to current working directory)
        """
        self.repo_path = repo_path

    def get_commit_hash(self) -> str:
        """Get current git commit hash.

        Returns:
            Full SHA-1 commit hash (40 characters)

        Raises:
            RuntimeError: If git command fails or not in a git repository

        Example:
            >>> git = GitProvider()
            >>> hash = git.get_commit_hash()
            >>> len(hash)
            40
        """
        try:
            cmd = ["git", "rev-parse", "HEAD"]
            if self.repo_path:
                cmd.extend(["-C", str(self.repo_path)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            commit_hash = result.stdout.strip()

            # Validate hash format (40 hex characters)
            if len(commit_hash) != GitSettings.SHA1_HASH_LENGTH or not all(
                c in GitSettings.HEX_DIGITS for c in commit_hash
            ):
                raise RuntimeError(
                    f"Invalid git commit hash format: {commit_hash}\n"
                    f"Expected {GitSettings.SHA1_HASH_LENGTH} hexadecimal characters."
                )

            return commit_hash

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to get git commit hash: {e.stderr.strip()}\n"
                "Ensure you are in a git repository and git is installed."
            ) from e
