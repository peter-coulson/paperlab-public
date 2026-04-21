"""CLI entry point for paperlab application."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from paperlab.cli.commands import db, eval, llm, load, paper, storage
from paperlab.cli.loading_utils import add_pipeline_args
from paperlab.config import CLICommands
from paperlab.startup import validate_environment


def _determine_validation_requirements(argv: list[str]) -> tuple[bool, bool]:
    """Determine environment validation requirements based on command.

    Args:
        argv: Command-line arguments (sys.argv)

    Returns:
        (skip_validation, require_llm) tuple
    """
    # Skip validation for db commands (chicken-and-egg: db init creates database)
    skip_validation = len(argv) >= 2 and argv[1] == CLICommands.DB

    # No CLI commands require LLM functionality anymore (all marking via API)
    require_llm = False

    return skip_validation, require_llm


def _setup_db_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Setup database command parser."""
    db_parser = subparsers.add_parser(CLICommands.DB, help="Database operations")
    db_subparsers = db_parser.add_subparsers(dest="db_command", help="Database commands")

    # db init
    init_parser = db_subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt (for CI/testing)",
    )
    init_parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before deletion",
    )


def _setup_storage_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Setup storage command parser."""
    storage_parser = subparsers.add_parser(
        CLICommands.STORAGE, help="Cloud storage operations (R2)"
    )
    storage_subparsers = storage_parser.add_subparsers(
        dest="storage_command", help="Storage commands"
    )

    # storage presigned-url
    presigned_url_parser = storage_subparsers.add_parser(
        "presigned-url", help="Generate presigned URL for R2 object"
    )
    presigned_url_parser.add_argument(
        "remote_key",
        type=str,
        help="R2 object key (e.g., submissions/uuid_page01.jpg)",
    )
    presigned_url_parser.add_argument(
        "--expiry",
        type=int,
        default=3600,
        help="URL expiry in seconds (default: 3600 = 1 hour)",
    )

    # storage download
    download_parser = storage_subparsers.add_parser(
        "download", help="Download image from R2 to local filesystem"
    )
    download_parser.add_argument(
        "remote_key",
        type=str,
        help="R2 object key (e.g., submissions/uuid_page01.jpg)",
    )
    download_parser.add_argument(
        "local_path",
        type=str,
        help="Local filesystem path to save image",
    )


def _setup_llm_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Setup LLM command parser."""
    llm_parser = subparsers.add_parser(CLICommands.LLM, help="LLM operations")
    llm_subparsers = llm_parser.add_subparsers(dest="llm_command", help="LLM commands")

    # llm test
    test_parser = llm_subparsers.add_parser("test", help="Test LLM API connection")
    test_parser.add_argument(
        "--provider",
        type=str,
        help="Provider to test (e.g., anthropic, openai)",
    )
    test_parser.add_argument(
        "--all",
        action="store_true",
        dest="all_providers",
        help="Test all configured providers",
    )

    # llm models
    models_parser = llm_subparsers.add_parser("models", help="List available models")
    models_parser.add_argument(
        "--provider",
        type=str,
        help="Filter by provider (e.g., anthropic, openai)",
    )


def _setup_paper_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Setup paper command parser."""
    paper_parser = subparsers.add_parser(CLICommands.PAPER, help="Paper operations")
    paper_subparsers = paper_parser.add_subparsers(dest="paper_command", help="Paper commands")

    # paper create
    create_parser = paper_subparsers.add_parser("create", help="Export paper to markdown")
    create_parser.add_argument("paper_id", type=int, help="Database ID of paper to export")
    create_parser.add_argument(
        "format_type",
        choices=["questions", "markscheme", "full"],
        help="Type of output to generate",
    )
    create_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: data/exports/markdown)",
    )


def _setup_load_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Setup load command parser."""
    load_parser = subparsers.add_parser("load", help="Loading operations")
    load_subparsers = load_parser.add_subparsers(dest="load_command", help="Load commands")

    # load paper
    load_paper_parser = load_subparsers.add_parser("paper", help="Load paper structure from JSON")
    load_paper_parser.add_argument(
        "json_path",
        type=str,
        help="Path to paper JSON file",
    )
    add_pipeline_args(load_paper_parser)

    # load marks
    load_marks_parser = load_subparsers.add_parser("marks", help="Load mark scheme from JSON")
    load_marks_parser.add_argument(
        "json_path",
        type=str,
        help="Path to mark scheme JSON file",
    )
    add_pipeline_args(load_marks_parser)

    # load llm-models
    load_llm_models_parser = load_subparsers.add_parser(
        "llm-models", help="Load LLM models configuration from JSON"
    )
    load_llm_models_parser.add_argument(
        "--json-path",
        type=str,
        help="Path to models JSON file (default: data/config/llm_models.json)",
    )
    add_pipeline_args(load_llm_models_parser)

    # load validation-types
    load_validation_types_parser = load_subparsers.add_parser(
        "validation-types", help="Load validation types configuration from JSON"
    )
    load_validation_types_parser.add_argument(
        "--json-path",
        type=str,
        help="Path to validation types JSON file "
        "(default: data/evaluation/config/validation_types.json)",
    )
    add_pipeline_args(load_validation_types_parser)

    # load exam-config
    load_exam_config_parser = load_subparsers.add_parser(
        "exam-config", help="Load exam configuration (papers + mark types) from JSON"
    )
    load_exam_config_parser.add_argument(
        "board",
        type=str,
        help="Exam board name (e.g., 'Pearson Edexcel')",
    )
    load_exam_config_parser.add_argument(
        "level",
        type=str,
        help="Qualification level (e.g., 'GCSE')",
    )
    load_exam_config_parser.add_argument(
        "subject",
        type=str,
        help="Subject name (e.g., 'Mathematics')",
    )
    load_exam_config_parser.add_argument(
        "--json-path",
        type=str,
        help="Path to config JSON file (default: data/config/{board}/{level}/{subject}.json)",
    )
    add_pipeline_args(load_exam_config_parser)


def _setup_eval_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Setup eval command parser."""
    eval_parser = subparsers.add_parser(CLICommands.EVAL, help="Evaluation operations")
    eval_subparsers = eval_parser.add_subparsers(dest="eval_command", help="Evaluation commands")

    # eval load-case
    load_case_parser = eval_subparsers.add_parser("load-case", help="Load test case from JSON")
    load_case_parser.add_argument(
        "json_path",
        type=str,
        help="Path to test case JSON file",
    )
    add_pipeline_args(load_case_parser)

    # eval load-folder
    load_folder_parser = eval_subparsers.add_parser(
        "load-folder", help="Load all test case JSONs from a folder"
    )
    load_folder_parser.add_argument(
        "folder_path",
        type=str,
        help="Path to folder containing test case JSON files",
    )

    # eval load-suite
    load_suite_parser = eval_subparsers.add_parser("load-suite", help="Load test suite from JSON")
    load_suite_parser.add_argument(
        "test_suite_json_path",
        type=str,
        help="Path to test suite JSON file",
    )
    add_pipeline_args(load_suite_parser)

    # eval audit-sanity-cases
    eval_subparsers.add_parser(
        "audit-sanity-cases",
        help="Audit questions for missing sanity test cases",
    )

    # eval generate-sanity-cases
    eval_subparsers.add_parser(
        "generate-sanity-cases",
        help="Generate sanity test case JSONs for all missing questions",
    )

    # eval run-suite
    run_suite_parser = eval_subparsers.add_parser(
        "run-suite", help="Run test suite with specified model"
    )
    run_suite_parser.add_argument(
        "suite_name",
        type=str,
        help="Name of test suite to run",
    )
    run_suite_parser.add_argument(
        "--model",
        dest="model_identifier",
        type=str,
        default=None,
        help=(
            "LLM model identifier (e.g., claude-sonnet-4-5-20250929). "
            "If not specified, uses default from config."
        ),
    )
    run_suite_parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Optional notes for this test run",
    )

    # eval list-suites
    eval_subparsers.add_parser("list-suites", help="List all available test suites")


def _build_parser() -> argparse.ArgumentParser:
    """Build complete argument parser with all commands.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(description="PaperLab CLI - Automated past paper marking tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup all command groups
    _setup_db_parser(subparsers)
    _setup_storage_parser(subparsers)
    _setup_llm_parser(subparsers)
    _setup_paper_parser(subparsers)
    _setup_load_parser(subparsers)
    _setup_eval_parser(subparsers)

    return parser


# Command registry: maps command paths to handler functions
# Key is tuple of command path (e.g., ("paper", "create"))
# Value is handler function (returns int exit code or Path for paper.create)
COMMAND_REGISTRY: dict[tuple[str, ...], Callable[..., int | Path]] = {
    # Storage commands
    (CLICommands.STORAGE, CLICommands.PRESIGNED_URL): storage.presigned_url,
    (CLICommands.STORAGE, CLICommands.DOWNLOAD): storage.download,
    # DB commands
    (CLICommands.DB, CLICommands.INIT): db.init,
    # Paper commands
    (CLICommands.PAPER, CLICommands.CREATE): paper.create,
    # LLM commands
    (CLICommands.LLM, CLICommands.TEST): llm.test,
    (CLICommands.LLM, CLICommands.MODELS): llm.models_list,
    # Load commands
    (CLICommands.LOAD, CLICommands.PAPER): load.paper,
    (CLICommands.LOAD, CLICommands.MARKS): load.marks,
    (CLICommands.LOAD, CLICommands.LLM_MODELS): load.llm_models,
    (CLICommands.LOAD, CLICommands.VALIDATION_TYPES): load.validation_types,
    (CLICommands.LOAD, CLICommands.EXAM_CONFIG): load.exam_config,
    # Eval commands
    (CLICommands.EVAL, CLICommands.LOAD_CASE): eval.load_case,
    (CLICommands.EVAL, CLICommands.LOAD_FOLDER): eval.load_folder,
    (CLICommands.EVAL, CLICommands.LOAD_SUITE): eval.load_suite,
    (CLICommands.EVAL, CLICommands.AUDIT_SANITY_CASES): eval.audit_sanity_cases,
    (CLICommands.EVAL, CLICommands.GENERATE_SANITY_CASES): eval.generate_sanity_cases,
    (CLICommands.EVAL, CLICommands.RUN_SUITE): eval.run_suite,
    (CLICommands.EVAL, CLICommands.LIST_SUITES): eval.list_suites,
}


def _extract_command_path(args: argparse.Namespace) -> tuple[str, ...]:
    """Extract command path from parsed arguments.

    Args:
        args: Parsed argument namespace

    Returns:
        Tuple of command path segments (e.g., ("paper", "attempt", "submit"))
    """
    path = []

    # Top-level command
    if hasattr(args, "command") and args.command:
        path.append(args.command)

    # Second-level subcommand (command-specific)
    if hasattr(args, "db_command") and args.db_command:
        path.append(args.db_command)
    elif hasattr(args, "storage_command") and args.storage_command:
        path.append(args.storage_command)
    elif hasattr(args, "paper_command") and args.paper_command:
        path.append(args.paper_command)
    elif hasattr(args, "llm_command") and args.llm_command:
        path.append(args.llm_command)
    elif hasattr(args, "load_command") and args.load_command:
        path.append(args.load_command)
    elif hasattr(args, "eval_command") and args.eval_command:
        path.append(args.eval_command)

    return tuple(path)


def _build_handler_kwargs(args: argparse.Namespace, cmd_path: tuple[str, ...]) -> dict[str, Any]:
    """Build kwargs dict for command handler from parsed arguments.

    Args:
        args: Parsed argument namespace
        cmd_path: Command path tuple

    Returns:
        Dictionary of kwargs to pass to handler function
    """
    # Start with all args as dict, remove internal argparse fields
    kwargs = vars(args).copy()

    # Remove argparse internal fields (command hierarchy)
    internal_fields = [
        "command",
        "db_command",
        "storage_command",
        "paper_command",
        "llm_command",
        "load_command",
        "eval_command",
    ]

    for field in internal_fields:
        kwargs.pop(field, None)

    # Special handling for paper.create which needs output_path returned
    if cmd_path == (CLICommands.PAPER, CLICommands.CREATE):
        # paper.create returns output_path, we need to print it
        # Keep kwargs as-is, handle in dispatch
        pass

    return kwargs


def _dispatch_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Dispatch parsed arguments to appropriate command handler.

    Args:
        args: Parsed argument namespace
        parser: ArgumentParser instance (for showing help on errors)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Extract command path
    cmd_path = _extract_command_path(args)

    # Handle no command specified
    if not cmd_path:
        parser.print_help()
        return 1

    # Look up handler in registry
    handler = COMMAND_REGISTRY.get(cmd_path)

    if not handler:
        # No handler found - show help for parent command
        if len(cmd_path) == 1:
            # Top-level command with no subcommand
            parser.parse_args([cmd_path[0], "--help"])
        elif len(cmd_path) == 2:
            # Second-level command with no subcommand
            parser.parse_args([cmd_path[0], cmd_path[1], "--help"])
        else:
            # Unknown command path
            parser.print_help()
        return 1

    # Build kwargs for handler
    kwargs = _build_handler_kwargs(args, cmd_path)

    # Special handling for paper.create (returns output_path)
    if cmd_path == (CLICommands.PAPER, CLICommands.CREATE):
        try:
            output_path = handler(**kwargs)
            print(f"Successfully created: {output_path}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    # Standard handler invocation (all other handlers return int directly)
    result = handler(**kwargs)
    if isinstance(result, Path):
        # Should not happen - paper.create is handled above
        raise TypeError(f"Unexpected Path return from handler: {cmd_path}")
    return result


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Determine validation requirements
    skip_validation, require_llm = _determine_validation_requirements(sys.argv)

    # Validate environment before processing commands
    if not skip_validation:
        try:
            validate_environment(require_llm=require_llm)
        except ValueError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            return 1

    # Build parser
    parser = _build_parser()

    # Parse arguments
    args = parser.parse_args()

    # Dispatch to appropriate handler
    return _dispatch_command(args, parser)


if __name__ == "__main__":
    sys.exit(main())
