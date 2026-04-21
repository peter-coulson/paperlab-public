You are creating a specification for new work in this codebase.

## Phase 1: Scope Discovery

Ask the user: **"What are you speccing?"**

Let them write freely. Do not ask structured questions - just listen and understand.

---

## Phase 2: Context Gathering

Read `CURRENT.md` to understand the current state of work.

Based on the user's description, intelligently determine what else to read:
- Relevant context files (in `context/`) for the areas involved
- Relevant src files for existing code that will be modified or extended
- Any related specs in `specs/` if they exist

Use your judgement. Load what you need to understand the landscape.

**If your understanding is unclear or incomplete, ask clarifying questions here before proceeding.**

---

## Phase 3: Alignment Confirmation

Present your understanding back to the user:
- What you understand the scope to be
- How it relates to current work (or if it's new work)
- What's explicitly out of scope (if anything)

Ask: **"Is this understanding correct? Anything to adjust or exclude?"**

Wait for confirmation before proceeding.

---

## Phase 4: Spec Creation

Write the spec to `specs/{appropriate-name}.md`.

**Critical:** The spec must align with the principles in `CLAUDE.md`. These are already loaded - apply them rigorously. The spec should make clear how implementation will follow these principles.

Structure the spec however makes sense for this particular work. No fixed template.

After writing, summarize what was created and where.
