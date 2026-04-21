---
name: flutter-ui
description: |
  Agentic UI automation for Flutter apps. Use when interacting with Flutter UI,
  automating workflows, taking screenshots, or navigating screens programmatically.
  Triggers: "tap on", "click", "navigate to", "screenshot", "UI elements",
  "swipe", "interact with the app", "automate", "what's on screen",
  "check what buttons are available", "launch the app", "hot reload"
---

# Flutter UI

Run: `flutter-ui <command>`

## Setup

The `flutter-ui` alias must be configured in `~/.zshrc`:

```bash
alias flutter-ui="python .claude/skills/flutter-ui/scripts/ui.py"
```

## Quick Reference

| Command | Use |
|---------|-----|
| `elements` | Navigate - see what's tappable |
| `tap N` | Tap element by ID |
| `screenshot` | Verify visuals (saves to /tmp/screen.png) |

## When to Use What

**Use `elements` for navigation** - fast, gives IDs to tap
**Use `screenshot` only for visual verification** - checking layout, colors, text rendering

## Commands

`status` · `stop` · `hot-reload` · `hot-restart`

| Command | Example |
|---------|---------|
| elements | `elements` or `elements -v` (verbose) |
| tap | `tap 3` or `tap "Confirm"` |
| swipe | `swipe 4 left` |
| screenshot | `screenshot` (no args needed) |
| launch | `launch --device=macos` |

## Recovery

Connection failed: `status` → `stop` → `launch`
