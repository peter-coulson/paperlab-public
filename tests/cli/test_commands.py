"""CLI smoke tests for paperlab commands.

Verifies that CLI commands can be invoked without crashing.
Uses subprocess to test actual command-line invocation.

These are SMOKE tests only:
- Test that commands don't crash
- Test exit codes, not output formatting
- Use --help to avoid side effects
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Final


def _get_cli_base() -> list[str]:
    """Determine the CLI base command based on available tools.

    Prefers 'uv run paperlab' per project convention.
    Falls back to venv paperlab if uv is not available.
    """
    if shutil.which("uv"):
        return ["uv", "run", "paperlab"]
    # Fall back to venv paperlab (for CI/sandbox environments)
    venv_paperlab = Path(__file__).parent.parent.parent / ".venv" / "bin" / "paperlab"
    if venv_paperlab.exists():
        return [str(venv_paperlab)]
    # Last resort: assume paperlab is on PATH
    return ["paperlab"]


# Command to run CLI with proper PYTHONPATH
CLI_BASE: Final[list[str]] = _get_cli_base()

# Environment with PYTHONPATH set correctly
CLI_ENV: Final[dict[str, str]] = {
    **os.environ,
    "PYTHONPATH": "src",
}


def run_cli_command(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run a paperlab CLI command and return the result.

    Args:
        args: Arguments to pass to paperlab CLI (e.g., ["--help"])
        timeout: Maximum seconds to wait for command

    Returns:
        CompletedProcess with stdout, stderr, and returncode
    """
    return subprocess.run(
        CLI_BASE + args,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=CLI_ENV,
        cwd=".",  # Run from project root
    )


class TestCLIHelp:
    """Smoke tests for CLI help commands.

    Each test verifies that --help works for a command group.
    Exit code 0 indicates successful help display.
    """

    def test_main_help(self) -> None:
        """paperlab --help displays help without error."""
        result = run_cli_command(["--help"])
        assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
        # Sanity check that output contains expected content
        assert "paperlab" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_db_help(self) -> None:
        """paperlab db --help displays database command help."""
        result = run_cli_command(["db", "--help"])
        assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
        assert "init" in result.stdout.lower()

    def test_load_help(self) -> None:
        """paperlab load --help displays load command help."""
        result = run_cli_command(["load", "--help"])
        assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
        assert "paper" in result.stdout.lower()

    def test_paper_help(self) -> None:
        """paperlab paper --help displays paper command help."""
        result = run_cli_command(["paper", "--help"])
        assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
        assert "create" in result.stdout.lower()

    def test_llm_help(self) -> None:
        """paperlab llm --help displays LLM command help."""
        result = run_cli_command(["llm", "--help"])
        assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
        assert "test" in result.stdout.lower()

    def test_eval_help(self) -> None:
        """paperlab eval --help displays eval command help."""
        result = run_cli_command(["eval", "--help"])
        assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
        # Check for any eval subcommand
        assert "load" in result.stdout.lower() or "suite" in result.stdout.lower()

    def test_storage_help(self) -> None:
        """paperlab storage --help displays storage command help."""
        result = run_cli_command(["storage", "--help"])
        assert result.returncode == 0, f"Exit code {result.returncode}: {result.stderr}"
        assert "presigned" in result.stdout.lower() or "download" in result.stdout.lower()


class TestCLIErrorHandling:
    """Tests for CLI error handling without external dependencies."""

    def test_unknown_command_exits_nonzero(self) -> None:
        """Unknown command produces non-zero exit code."""
        result = run_cli_command(["nonexistent-command"])
        # argparse returns exit code 2 for invalid arguments
        assert result.returncode != 0

    def test_no_command_shows_help(self) -> None:
        """Running paperlab with no command shows help."""
        result = run_cli_command([])
        # No command returns exit code 1 but shows help
        # Just verify it doesn't crash with traceback
        assert "traceback" not in result.stderr.lower()
