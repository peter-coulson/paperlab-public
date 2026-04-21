# Context Pruning

Prune context documentation to align with governance principles.

**Scope:** `context/**/*.md` only.

---

## Step 1: Scope Selection

Ask:

"Which context files should I prune?
- `all` - All context files
- Or specify a glob pattern (e.g., `context/backend/**/*.md`)"

Wait for response.

---

## Step 2: Load Principles

Read `context/GOVERNANCE.md` completely. This contains all pruning criteria.

---

## Step 3: Execute Pruning

Glob the pattern. Sort files by line count (largest first).

For each file:
1. **Read** the complete file
2. **Assess** against GOVERNANCE.md principles
3. **Edit** to remove violations, preserve essential WHY/WHERE content
4. **Report:** `✓ {filename}: {before} → {after} lines`

---

## End

Report: `Complete: {N} files, {before} → {after} total lines`
