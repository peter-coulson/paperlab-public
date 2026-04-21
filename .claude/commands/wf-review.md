You are reviewing a specification for quality and alignment before implementation.

## Phase 1: Scope Discovery

Ask the user: **"Which spec are you reviewing?"**

---

## Phase 2: Validation

Read the spec, then intelligently gather context:
- Relevant src files that the spec will affect
- Related context files for the areas involved
- Current state of the codebase in those areas

Validate the spec against:

1. **Principles alignment** - Does it follow `CLAUDE.md` principles? (already loaded - apply rigorously)
2. **Integration fit** - How does this interact with existing code? Any conflicts, gaps, or false assumptions?
3. **Completeness** - Edge cases, dependencies, or considerations the spec missed?
4. **Feasibility** - Given what exists, is this implementable as written?

---

## Output

Present findings in chat with severity levels:

- **Blocking** - Must fix before implementation. Spec is incorrect, conflicts with existing code, or violates principles.
- **Warning** - Should address. Gaps, ambiguities, or potential issues.
- **Suggestion** - Consider improving. Minor enhancements or clarifications.

If issues are found, offer: **"Would you like me to update the spec to address these issues?"**

Do not automatically fix. Wait for user confirmation.
