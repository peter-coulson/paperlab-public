You are reviewing an implementation against its spec and codebase principles.

## Phase 1: Scope Discovery

Ask the user:
1. **"What changes do you want reviewed?"** (unstaged, last commit, branch vs main, specific files, etc.)
2. **"Which spec does this implement?"** (path to spec file)

---

## Phase 2: Spec vs Implementation Analysis

Read the spec and get the diff.

Compare what was planned vs what was built. Identify divergences:

- **Improvement** - Implementation is better than spec suggested.
- **Regression** - Missing something from spec, or worse approach than planned.
- **Neutral** - Different but equivalent. No impact.

---

## Phase 3: Principles Review

Read surrounding context to understand integration.

Validate against `CLAUDE.md` principles (already loaded - apply rigorously).

Check:
- Does implementation follow codebase principles?
- Does it integrate correctly with existing code?
- Any bugs, edge cases, or issues?

---

## Output

Present findings in chat:

### Spec Alignment
List divergences with categorization (Improvement / Regression / Neutral) and brief explanation of each.

### Code Quality
Issues with severity levels:
- **Blocking** - Must fix. Violates principles, introduces bugs, or breaks integration.
- **Warning** - Should address. Gaps or potential issues.
- **Suggestion** - Consider improving. Minor enhancements.

---

## Actions

If code issues found, offer: **"Would you like me to fix these issues?"**

If divergences found (Improvements or Neutral), **update the spec to reflect the actual implementation.** The spec must be the source of truth for context-update.

If regressions found, warn user: **"Regressions should be resolved before running context-update."**

Do not automatically fix code. Wait for user confirmation.
