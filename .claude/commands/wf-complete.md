You are updating the context system to reflect a completed implementation.

## Phase 1: Scope Discovery

Ask the user: **"Which spec has been implemented?"**

---

## Phase 2: Content Extraction

Read the spec (should reflect actual implementation).

Read `context/GOVERNANCE.md` to understand:
- Domain ownership (backend/, api/, frontend/, shared/)
- Content principles (WHY/WHERE not WHAT/HOW)

**Extract from spec:** List the key concepts that need context documentation.

**Check existing context:** Read relevant context files in affected domains. Identify:
- Concepts that already exist in context (may need updating)
- Concepts that are NEW from this spec
- Existing concepts that may be in the WRONG location

The goal is to map the UNION of existing context + new context to ideal files.

---

## Phase 3: Mapping Evaluation

**For each concept (new and existing), evaluate independently:**

Ignore current file structure. Ask: "In a perfect scenario, what file should this concept live in?"

For each concept, determine:
1. **Domain:** Which domain owns this? (backend, api, frontend, shared)
2. **Concern:** What specific concern does this address? (e.g., patterns, workflows, authentication, storage, data models)
3. **Ideal file:** Based on domain + concern, what file name makes sense?

Present as step-by-step evaluation:

```
### Concept: [name]

**Description:** [what this concept covers]
**Status:** [NEW from spec / EXISTS in X.md / EXISTS but wrong location]
**Domain:** [backend/api/frontend/shared] - [why]
**Concern:** [specific concern] - [why]
**Ideal file:** [domain]/[CONCERN].md

---
```

After evaluating all concepts, group by ideal file:

```
## Proposed File Mapping

| Ideal File | Concepts | Action |
|------------|----------|--------|
| api/WORKFLOWS.md | Paper flow, Practice flow | CREATE |
| api/PATTERNS.md | from_domain, validation | CREATE (extract from README) |
| backend/STORAGE.md | R2 architecture | UPDATE |
```

---

## Phase 4: Context Update

Execute the mapping:

1. For each ideal file:
   - If file doesn't exist: Create it
   - If file exists: Update with new/moved concepts
   - If concept exists elsewhere: Move it to correct location
2. Update README.md files to serve as navigation (not substance)
3. Add cross-references between related files
4. Follow governance content principles (WHY/WHERE not WHAT/HOW)

---

## Phase 5: Summary

Summarize:
- New files created
- Existing files updated
- Content moved between files
- Why each change was made

---

## Phase 6: Spec Cleanup

Ask the user: **"Implementation is now documented in context. Delete the spec?"**

If user confirms, delete the spec file.

If user declines, leave spec in place.
