#!/usr/bin/env python3
"""
Flutter UI Test CLI - Self-contained agentic UI testing.

Manages Flutter app lifecycle and provides UI interaction capabilities.
No external MCP dependencies - all functionality is built-in.

Lifecycle Commands:
    python ui.py launch               Launch Flutter app (uses stored project/device)
    python ui.py stop                 Stop the running app
    python ui.py screenshot [path]    Capture window screenshot
    python ui.py hot-reload           Hot reload the app (preserves state)
    python ui.py hot-restart          Hot restart the app (resets state)
    python ui.py devices              List available Flutter devices

UI Commands:
    python ui.py elements [options]   Get interactive elements
    python ui.py tap <id_or_text>     Tap by element ID or text search
    python ui.py swipe <id> <dir>     Swipe element (left/right/up/down)
    python ui.py longpress <id>       Long press element

State Commands:
    python ui.py status               Show current connection state
    python ui.py clear                Clear stored state

Element filtering:
    python ui.py elements --type=button
    python ui.py elements --type=slidable
    python ui.py elements --text="Paper"

Examples:
    python ui.py launch --project=/path/to/app --device=macos
    python ui.py elements
    python ui.py tap 4
    python ui.py screenshot /tmp/screen.png
    python ui.py stop
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# State file location
STATE_FILE = Path.home() / ".flutter_ui_test_state.json"

# Element type aliases for filtering
TYPE_ALIASES = {
    "button": ["button", "icon_button"],
    "input": ["text_field"],
    "list": ["list_item", "slidable"],
    "slidable": ["slidable"],
    "interactive": ["interactive"],
}


def load_state() -> dict[str, Any]:
    """Load persisted state from file."""
    if STATE_FILE.exists():
        try:
            result: dict[str, Any] = json.loads(STATE_FILE.read_text())
            return result
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def save_state(state: dict[str, Any]) -> None:
    """Save state to file."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def clear_state() -> None:
    """Clear persisted state."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    print("State cleared.")


def extract_vm_uri_from_logs(logs_json: str) -> str | None:
    """Extract VM service URI from MCP app logs.

    The VM service URI is in the app.debugPort event and ends with /ws.
    Example: ws://127.0.0.1:53258/Y3pjGkdGhjU=/ws
    """
    try:
        data = json.loads(logs_json)
        logs = data.get("logs", [])
    except json.JSONDecodeError:
        # Maybe it's just a list of log lines
        if isinstance(logs_json, str):
            logs = logs_json.strip().split("\n")
        else:
            return None

    # Pattern for VM service URI (ends with /ws)
    uri_pattern = r'ws://[^"]+/ws'

    for line in logs:
        if "app.debugPort" in str(line) or "wsUri" in str(line):
            match = re.search(uri_pattern, str(line))
            if match:
                return match.group(0)

    # Fallback: search all lines
    for line in logs:
        match = re.search(uri_pattern, str(line))
        if match:
            return match.group(0)

    return None


def extract_dtd_uri_from_logs(logs_json: str) -> str | None:
    """Extract DTD URI from MCP app logs.

    The DTD URI is in the app.dtd event and does NOT end with /ws.
    Example: ws://127.0.0.1:53257/F6fE71d3hTo=
    """
    try:
        data = json.loads(logs_json)
        logs = data.get("logs", [])
    except json.JSONDecodeError:
        if isinstance(logs_json, str):
            logs = logs_json.strip().split("\n")
        else:
            return None

    # Pattern for DTD URI in app.dtd event
    dtd_pattern = r'"uri"\s*:\s*"(ws://[^"]+[^/])"'

    for line in logs:
        if "app.dtd" in str(line):
            match = re.search(dtd_pattern, str(line))
            if match:
                uri = match.group(1)
                # Ensure it's not the VM service URI
                if not uri.endswith("/ws"):
                    return uri

    return None


def kill_existing_instances(project_root: str) -> int:
    """Kill any existing Flutter app instances for this project.

    Only kills processes that match the exact app bundle path pattern.
    Returns the number of processes killed.
    """
    app_name = os.path.basename(project_root) if project_root else "paperlab"
    # Match the exact macOS app bundle path pattern
    app_bundle_pattern = f"{project_root}/build/macos/Build/Products/Debug/{app_name}.app"

    killed_count = 0

    # First: kill tracked PIDs from state (both app_pid and flutter_pid)
    state = load_state()
    tracked_app_pid = state.get("app_pid") or state.get("pid")
    tracked_flutter_pid = state.get("flutter_pid")
    killed_pids: set[int] = set()

    if tracked_app_pid:
        try:
            os.kill(tracked_app_pid, 0)  # Check if running
            print(f"Stopping tracked app (PID {tracked_app_pid})...")
            os.kill(tracked_app_pid, 15)  # SIGTERM
            killed_count += 1
            killed_pids.add(tracked_app_pid)
        except (OSError, ProcessLookupError):
            pass  # Already dead

    if tracked_flutter_pid and tracked_flutter_pid != tracked_app_pid:
        try:
            os.kill(tracked_flutter_pid, 0)  # Check if running
            print(f"Stopping tracked flutter process (PID {tracked_flutter_pid})...")
            os.kill(tracked_flutter_pid, 15)  # SIGTERM
            killed_count += 1
            killed_pids.add(tracked_flutter_pid)
        except (OSError, ProcessLookupError):
            pass  # Already dead

    # Second: find and kill any other instances of this specific app
    # Use ps to find processes matching the exact app bundle path
    try:
        result = subprocess.run(
            ["pgrep", "-f", app_bundle_pattern],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            pids = [int(p) for p in result.stdout.strip().split("\n") if p]
            for pid in pids:
                if pid in killed_pids:
                    continue  # Already handled
                try:
                    print(f"Stopping untracked {app_name} instance (PID {pid})...")
                    os.kill(pid, 15)  # SIGTERM
                    killed_count += 1
                except (OSError, ProcessLookupError):
                    pass  # Already dead
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # pgrep not available or timed out, skip

    if killed_count > 0:
        # Clear state since we killed things
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        # Give processes time to exit gracefully
        time.sleep(0.5)

    return killed_count


def get_project_root() -> str:
    """Get the project root from state, script location, or current directory."""
    state = load_state()
    stored_root = state.get("project_root", "")
    if isinstance(stored_root, str) and stored_root:
        return stored_root

    # Try to find project root relative to this script
    # Script is at: <project>/.claude/skills/flutter-ui-test/scripts/ui.py
    script_dir = Path(__file__).resolve().parent
    potential_root = script_dir.parent.parent.parent.parent  # Go up 4 levels

    if (potential_root / "bin" / "agent_cli.dart").exists():
        return str(potential_root)

    # Fallback to current directory
    cwd: str = os.getcwd()
    return cwd


def run_agent_cli(
    command: str,
    args: list[str] | None = None,
    needs_uri: bool = True,
    project_override: str | None = None,
) -> dict[str, Any]:
    """Run agent_cli command and return parsed result.

    Prefers native binary (bin/agent_cli) for 10x faster execution.
    Falls back to JIT (dart bin/agent_cli.dart) if binary not found.
    """
    state = load_state()
    project_root = project_override or get_project_root()

    # Prefer native binary for ~10x faster execution
    native_path = os.path.join(project_root, "bin", "agent_cli")
    dart_path = os.path.join(project_root, "bin", "agent_cli.dart")

    if os.path.exists(native_path):
        cmd = [native_path]
    elif os.path.exists(dart_path):
        cmd = ["dart", dart_path]
    else:
        print(f"ERROR: agent_cli not found at {native_path} or {dart_path}", file=sys.stderr)
        sys.exit(1)

    # Add URI for commands that need it
    if needs_uri:
        vm_uri = state.get("vm_uri")
        if not vm_uri:
            print("ERROR: No VM URI stored. Launch an app first.", file=sys.stderr)
            print("\nTo launch:", file=sys.stderr)
            print("  python ui.py launch --project=/path/to/app --device=macos", file=sys.stderr)
            sys.exit(1)
        cmd.append(f"--uri={vm_uri}")

    cmd.append(command)
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, timeout=120)

        if result.returncode != 0:
            error_msg = result.stderr.strip()

            # Detect connection errors
            if "CONNECTION_REFUSED" in error_msg or "CONNECTION_STALE" in error_msg:
                print("Connection error. The stored URI may be stale.", file=sys.stderr)
                print("\nRecovery steps:", file=sys.stderr)
                print("  1. Check status: python ui.py status", file=sys.stderr)
                print("  2. Try hot reload: python ui.py hot-reload", file=sys.stderr)
                print("  3. Or restart: python ui.py stop && python ui.py launch", file=sys.stderr)
            else:
                print(f"ERROR: {error_msg}", file=sys.stderr)
            sys.exit(1)

        output = result.stdout.strip()
        if output:
            try:
                parsed: dict[str, Any] = json.loads(output)
                return parsed
            except json.JSONDecodeError:
                return {"raw": output}
        return {}

    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out. App may be unresponsive.", file=sys.stderr)
        print("Try: python ui.py hot-reload", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: 'dart' command not found. Ensure Flutter SDK is in PATH.", file=sys.stderr)
        sys.exit(1)


def cmd_launch(args: argparse.Namespace) -> None:
    """Launch a Flutter app."""
    project = args.project or get_project_root()
    device = args.device or "macos"
    target = args.target or "lib/driver_main.dart"
    # Default dart-defines for driver mode:
    # - SKIP_AUTH=true: Skip Supabase init so app launches without backend
    # - ENVIRONMENT=development: Use local API endpoints
    dart_define = (
        args.dart_define if args.dart_define else ["SKIP_AUTH=true", "ENVIRONMENT=development"]
    )

    # Kill any existing instances before launching
    killed = kill_existing_instances(project)
    if killed > 0:
        print(f"Cleaned up {killed} existing instance(s).\n")

    print("Launching Flutter app...")
    print(f"  Project: {project}")
    print(f"  Device: {device}")
    print(f"  Target: {target}")
    if dart_define:
        print(f"  Dart defines: {dart_define}")

    # Call agent_cli.dart launch
    cli_args = [
        f"--project={project}",
        f"--device={device}",
        f"--target={target}",
    ]
    # Add dart-define arguments
    for define in dart_define:
        cli_args.append(f"--dart-define={define}")
    result = run_agent_cli("launch", cli_args, needs_uri=False, project_override=project)

    if not result.get("vm_uri"):
        print("ERROR: Launch failed - no VM URI returned", file=sys.stderr)
        sys.exit(1)

    # Save state - track both flutter_pid (for VM service) and app_pid (for screenshots/status)
    state = {
        "flutter_pid": result.get("flutter_pid"),
        "app_pid": result.get("app_pid"),
        "pid": result.get("pid"),  # Backwards compatibility - prefer app_pid
        "vm_uri": result.get("vm_uri"),
        "dtd_uri": result.get("dtd_uri"),
        "log_file": result.get("log_file"),
        "project_root": project,
        "device": device,
        "target": target,
    }
    save_state(state)

    print("\nApp launched successfully!")
    print(f"  App PID: {state.get('app_pid', 'unknown')}")
    print(f"  Flutter PID: {state.get('flutter_pid', 'unknown')}")
    print(f"  VM URI: {state['vm_uri']}")


def cmd_stop(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Stop the running Flutter app."""
    state = load_state()
    app_pid = state.get("app_pid") or state.get("pid")
    flutter_pid = state.get("flutter_pid")
    project_root = state.get("project_root", "")

    if not app_pid and not flutter_pid:
        print("No app is currently tracked. Nothing to stop.")
        return

    # Get app name from project path for fallback
    app_name = os.path.basename(project_root) if project_root else "paperlab"

    # Stop the app process first (if we have app_pid)
    if app_pid:
        print(f"Stopping app (PID {app_pid})...")
        result = run_agent_cli("stop", [f"--pid={app_pid}", f"--app={app_name}"], needs_uri=False)
        if result.get("killed"):
            print("App stopped successfully.")
        else:
            print("App may have already stopped.")

    # Also stop the flutter process (if different from app_pid)
    if flutter_pid and flutter_pid != app_pid:
        print(f"Stopping flutter process (PID {flutter_pid})...")
        try:
            os.kill(flutter_pid, 15)  # SIGTERM
            print("Flutter process stopped.")
        except (OSError, ProcessLookupError):
            print("Flutter process may have already stopped.")

    clear_state()


def cmd_screenshot(args: argparse.Namespace) -> None:
    """Take a screenshot of the app window."""
    state = load_state()
    # Use app_pid for screenshots (the actual running app window)
    pid = state.get("app_pid") or state.get("pid")
    project_root = state.get("project_root", "")

    if not pid:
        print("ERROR: No app tracked. Run: launch", file=sys.stderr)
        sys.exit(1)

    # Default to fixed path - always overwrites, no arg needed
    output = args.output or "/tmp/screen.png"

    # Get app name from project path for window fallback
    app_name = os.path.basename(project_root) if project_root else "paperlab"

    result = run_agent_cli(
        "screenshot",
        [f"--pid={pid}", f"--output={output}", f"--app={app_name}"],
        needs_uri=False,
    )

    if result.get("success"):
        print(f"Screenshot saved to: {output}")
    else:
        print(f"Screenshot result: {result}")


def cmd_hot_reload(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Hot reload the running app (preserves state)."""
    result = run_agent_cli("hot-reload", needs_uri=True)

    if result.get("success"):
        print("Hot reload successful!")
    else:
        print(f"Hot reload result: {result}")


def cmd_hot_restart(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Hot restart the running app (resets state)."""
    result = run_agent_cli("hot-restart", needs_uri=True)

    if result.get("success"):
        print("Hot restart successful! App state has been reset.")
    else:
        print(f"Hot restart result: {result}")


def cmd_devices(args: argparse.Namespace) -> None:  # noqa: ARG001
    """List available Flutter devices."""
    try:
        result = subprocess.run(
            ["flutter", "devices", "--machine"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            print(f"ERROR: flutter devices failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        devices_list = json.loads(result.stdout.strip())
        devices = [
            {
                "id": d.get("id"),
                "name": d.get("name"),
                "platform": d.get("targetPlatform"),
                "available": d.get("isSupported", True),
            }
            for d in devices_list
        ]

    except FileNotFoundError:
        print("ERROR: 'flutter' command not found. Ensure Flutter SDK is in PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: flutter devices timed out", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse flutter devices output: {e}", file=sys.stderr)
        sys.exit(1)

    if not devices:
        print("No devices found.")
        return

    print(f"Found {len(devices)} device(s):\n")
    for d in devices:
        status = "available" if d.get("available", True) else "unavailable"
        print(
            f"  {d['id']:<20s} | {d['name']:<30s} | {d.get('platform', 'unknown'):<15s} | {status}"
        )


def cmd_elements(args: argparse.Namespace) -> None:
    """Get interactive elements with optional filtering."""
    result = run_agent_cli("elements")
    elements = result.get("elements", [])

    # Filter by type
    if args.type:
        type_filter = TYPE_ALIASES.get(args.type, [args.type])
        elements = [e for e in elements if e.get("type") in type_filter]

    # Filter by text
    if args.text:
        search = args.text.lower()
        elements = [e for e in elements if search in e.get("desc", "").lower()]

    if args.json:
        print(json.dumps({"elements": elements}, indent=2))
    elif not elements:
        print("No elements.")
    elif args.verbose:
        # Verbose multi-line output
        for e in elements:
            gestures = ", ".join(e.get("gestures", []))
            print(f"[{e['id']}] {e['type']}: {e['desc'][:50]} ({e.get('x')},{e.get('y')})")
            if gestures:
                print(f"    gestures: {gestures}")
    else:
        # Compact single-line output (default) - optimized for LLM token efficiency
        for e in elements:
            desc = e.get("desc", "")[:35]
            print(f"[{e['id']}] {desc}")


def cmd_tap(args: argparse.Namespace) -> None:
    """Tap element by ID or text search."""
    target = args.target

    # Check if target is numeric (ID) or text (search)
    try:
        element_id = int(target)
        result = run_agent_cli("tap", [f"--id={element_id}"])
    except ValueError:
        # Search for element by text
        elements_result = run_agent_cli("elements")
        elements = elements_result.get("elements", [])

        search = target.lower()
        matches = [e for e in elements if search in e.get("desc", "").lower()]

        if not matches:
            print(f"ERROR: No element found matching '{target}'", file=sys.stderr)
            print("\nAvailable elements:", file=sys.stderr)
            for e in elements[:5]:
                print(f"  [{e['id']}] {e['desc']}", file=sys.stderr)
            sys.exit(1)

        if len(matches) > 1:
            print(f"Multiple matches for '{target}':", file=sys.stderr)
            for e in matches:
                print(f"  [{e['id']}] {e['desc']}", file=sys.stderr)
            print(f"\nUsing first match: [{matches[0]['id']}] {matches[0]['desc']}")

        element_id = matches[0]["id"]
        result = run_agent_cli("tap", [f"--id={element_id}"])

    if result.get("success"):
        print(f"Tapped element {element_id}")
    else:
        print(f"Tap result: {result}")


def cmd_swipe(args: argparse.Namespace) -> None:
    """Swipe element by ID."""
    direction = args.direction.lower()
    if direction not in ["left", "right", "up", "down"]:
        print(
            f"ERROR: Invalid direction '{direction}'. Use: left, right, up, down", file=sys.stderr
        )
        sys.exit(1)

    cli_args = [f"--id={args.id}", f"--direction={direction}"]
    if args.distance:
        cli_args.append(f"--distance={args.distance}")

    result = run_agent_cli("swipe", cli_args)

    if result.get("success"):
        print(f"Swiped element {args.id} {direction}")
    else:
        print(f"Swipe result: {result}")


def cmd_longpress(args: argparse.Namespace) -> None:
    """Long press element by ID."""
    result = run_agent_cli("longpress", [f"--id={args.id}"])

    if result.get("success"):
        print(f"Long pressed element {args.id}")
    else:
        print(f"Long press result: {result}")


def cmd_status(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Show current connection state."""
    state = load_state()

    if not state:
        print("No app tracked. Launch one with: python ui.py launch")
        return

    app_pid = state.get("app_pid") or state.get("pid")
    flutter_pid = state.get("flutter_pid")
    app_running = False
    flutter_running = False

    # Check if app process is still running
    if app_pid:
        try:
            os.kill(app_pid, 0)  # Signal 0 = check if process exists
            app_running = True
        except (OSError, ProcessLookupError):
            app_running = False

    # Check if flutter process is still running
    if flutter_pid:
        try:
            os.kill(flutter_pid, 0)
            flutter_running = True
        except (OSError, ProcessLookupError):
            flutter_running = False

    print("Current state:")
    print(f"  App PID: {app_pid} ({'running' if app_running else 'NOT RUNNING'})")
    if flutter_pid and flutter_pid != app_pid:
        print(f"  Flutter PID: {flutter_pid} ({'running' if flutter_running else 'NOT RUNNING'})")
    print(f"  VM URI: {state.get('vm_uri', 'Not set')}")
    print(f"  Project: {state.get('project_root', 'Unknown')}")
    print(f"  Device: {state.get('device', 'Unknown')}")
    print(f"  Target: {state.get('target', 'Unknown')}")

    if not app_running and app_pid:
        print("\nWARNING: The tracked app is no longer running.")
        print("  To restart: python ui.py launch")
        print("  To clear state: python ui.py clear")


def cmd_clear(args: argparse.Namespace) -> None:  # noqa: ARG001
    """Clear stored state."""
    clear_state()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flutter UI Test CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # launch
    launch_parser = subparsers.add_parser("launch", help="Launch Flutter app")
    launch_parser.add_argument("--project", "-p", help="Project root directory")
    launch_parser.add_argument("--device", "-d", help="Device ID (default: macos)")
    launch_parser.add_argument("--target", "-t", help="Target file (default: lib/main.dart)")
    launch_parser.add_argument(
        "--dart-define",
        dest="dart_define",
        action="append",
        default=[],
        help="Dart compile-time variable (can be repeated). Default: SKIP_AUTH=true",
    )
    launch_parser.set_defaults(func=cmd_launch)

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop the running app")
    stop_parser.set_defaults(func=cmd_stop)

    # screenshot
    screenshot_parser = subparsers.add_parser("screenshot", help="Capture window screenshot")
    screenshot_parser.add_argument("output", nargs="?", help="Output file path")
    screenshot_parser.set_defaults(func=cmd_screenshot)

    # hot-reload
    reload_parser = subparsers.add_parser("hot-reload", help="Hot reload the app (preserves state)")
    reload_parser.set_defaults(func=cmd_hot_reload)

    # hot-restart
    restart_parser = subparsers.add_parser("hot-restart", help="Hot restart the app (resets state)")
    restart_parser.set_defaults(func=cmd_hot_restart)

    # devices
    devices_parser = subparsers.add_parser("devices", help="List available Flutter devices")
    devices_parser.set_defaults(func=cmd_devices)

    # elements
    elements_parser = subparsers.add_parser("elements", help="Get interactive elements")
    elements_parser.add_argument("--type", help="Filter by type (button, input, list, slidable)")
    elements_parser.add_argument("--text", help="Filter by description text")
    elements_parser.add_argument("--json", action="store_true", help="Output as JSON")
    elements_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output with coordinates"
    )
    elements_parser.set_defaults(func=cmd_elements)

    # tap
    tap_parser = subparsers.add_parser("tap", help="Tap element")
    tap_parser.add_argument("target", help="Element ID (number) or text to search")
    tap_parser.set_defaults(func=cmd_tap)

    # swipe
    swipe_parser = subparsers.add_parser("swipe", help="Swipe element")
    swipe_parser.add_argument("id", type=int, help="Element ID")
    swipe_parser.add_argument("direction", help="Direction: left, right, up, down")
    swipe_parser.add_argument("--distance", type=int, help="Swipe distance in pixels")
    swipe_parser.set_defaults(func=cmd_swipe)

    # longpress
    longpress_parser = subparsers.add_parser("longpress", help="Long press element")
    longpress_parser.add_argument("id", type=int, help="Element ID")
    longpress_parser.set_defaults(func=cmd_longpress)

    # status
    status_parser = subparsers.add_parser("status", help="Show connection state")
    status_parser.set_defaults(func=cmd_status)

    # clear
    clear_parser = subparsers.add_parser("clear", help="Clear stored state")
    clear_parser.set_defaults(func=cmd_clear)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
