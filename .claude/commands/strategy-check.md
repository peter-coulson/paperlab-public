You are conducting a **Strategic Implementation Order Validation Check** for this codebase.

Think hard about the implementation order and task sequencing - this requires careful analysis of dependencies, foundations, complexity ordering, and potential rework scenarios.

## Objective

Validate that the implementation order in CURRENT.md is optimal given:
1. Technical dependencies (hard and soft)
2. Structural foundations (patterns and abstractions)
3. Complexity sequencing (simple before complex)
4. Rework minimization (avoid rebuilding)

Also validate integration coherence across short-term (CURRENT.md) → medium-term (milestones) → long-term (vision) strategy.

## Core Philosophy

**This check assumes your high-level strategy is sound.** It validates tactical sequencing and integration, not strategic direction. The order you build things matters more than almost anything else.

## Prerequisites

**CRITICAL:** Before starting:
- Context system is healthy (run /context-check if uncertain)
- This checks IMPLEMENTATION ORDER, not strategy quality
- Assumes context documentation is accurate and current

## Context Files to Read

Required reading:
- `CURRENT.md` - Task order (PRIMARY FOCUS)
- `context/` directory - Technical approach and architecture
  - Read `context/README.md` for navigation
- `specs/` - Planned implementations (if exists)
- `src/` - What's actually implemented (determines what exists vs. planned)
- Previous strategy reports in `.quality/strategy/` (to track changes, if exist)

## Implementation Order Checks

### 1. Hard Dependency Validation

**Goal:** Ensure tasks are sequenced so dependencies exist before they're needed

**Check:**
- Map dependencies between all tasks in CURRENT.md
- Identify tasks that literally cannot be done without prior tasks
- Check if order respects hard dependencies

**Examples of hard dependencies:**
- "Implement marking engine" → "Build score aggregator" (aggregator needs engine)
- "Design schema" → "Create database migrations" (migrations need schema)
- "Parse questions" → "Match to mark scheme" (matching needs parsed questions)

**Violations:**
- Task #3 requires output from Task #5
- Task depends on module that doesn't exist and isn't in earlier tasks
- Circular dependencies between tasks

### 2. Soft Dependency Optimization

**Goal:** Order tasks so later tasks benefit from earlier work

**Check:**
- Does task #1 create patterns/infrastructure that task #2 leverages?
- Is task #2 significantly easier if done after task #1?
- Would doing task #2 first create duplicate work?

**Examples:**
- "Implement Question entity" → "Implement Paper entity" (Paper uses Question patterns)
- "Build JSON parser" → "Build mark scheme parser" (second parser uses first as template)

**Violations:**
- Building specific before generic (should build generic utilities first)
- Building complex before simple (should learn from simple case first)
- Building feature before foundation (foundation would make feature easier)

### 3. Structural Foundation Sequencing

**Goal:** Build foundational patterns and abstractions before features that use them

**Check:**
- Are we building core abstractions before concrete implementations?
- Do foundational patterns come first?

**Foundation-first examples:**
- Core domain entities before services that use them
- Validation framework before specific validators
- Error handling patterns before features that throw errors

**Violations:**
- Building 3 different parsers before extracting common parser pattern
- Implementing features before core domain model exists
- Creating multiple similar implementations before abstracting

### 4. Simplicity Sequencing (Simple → Complex)

**Goal:** Build simple cases before complex ones to understand patterns

**Check:**
- Are we starting with simplest cases?
- Do simple implementations inform complex ones?
- Are we building complexity incrementally?

**Simple-first examples:**
- Single question type before multiple question types
- Basic marking before edge cases
- Happy path before error handling

**Violations:**
- Building full feature with all edge cases before basic version
- Implementing complex variations before simple base case
- Premature generalization before seeing patterns

### 5. Rework Minimization

**Goal:** Sequence tasks to avoid throwaway work and major refactors

**Check:**
- Will current order cause us to rebuild things?
- Are we making decisions that will need to be undone?

**Rework-causing patterns:**
- Building UI before API is defined (UI will need rework)
- Implementing features before data model is stable (features need rework)
- Creating specific solutions before seeing the pattern (will need generalization refactor)

### 6. Short-Term → Medium-Term Alignment

**Goal:** Verify CURRENT.md tasks support next milestone

**Check:**
- Do tasks in CURRENT.md directly advance current milestone?
- Is there a clear path from current tasks to milestone completion?
- Are there gaps between current work and milestone goals?

**Violations:**
- Tasks that don't contribute to current milestone
- Missing tasks needed for milestone completion
- Milestone unreachable with current task list

## Output Format

Generate a timestamped report and save to `.quality/strategy/{TIMESTAMP}.md`

Use format: `YYYY-MM-DD-HHMMSS` for timestamp (e.g., `2025-10-18-143045.md`)

### Report Structure

```markdown
# Strategic Implementation Order Validation
**Run:** {TIMESTAMP}
**Status:** {✅ Optimal | ⚠️ Suboptimal | ❌ Critical Order Issues}

## Executive Summary

**Task order health:** {percentage}%
- Hard dependencies: {✅ Respected | ⚠️ Issues found}
- Soft dependencies: {✅ Optimal | ⚠️ Could improve}
- Foundation sequencing: {✅ Good | ⚠️ Missing foundations}
- Complexity sequencing: {✅ Simple→Complex | ⚠️ Complexity-first}
- Rework risk: {LOW | MEDIUM | HIGH}

**Integration health:** {percentage}%
- Short→Medium term: {✅ Aligned | ⚠️ Gaps found}

## 🔴 Critical Issues [MUST FIX BEFORE PROCEEDING]

{Order problems that will cause major rework or are impossible}

1. **[Category]** Description
   Current order: Task X → Task Y
   Issue: {why this order is impossible/terrible}
   Recommended: Task Y → Task X
   Impact: {time saved, rework avoided}

## 🟡 Warnings [SUBOPTIMAL]

{Order improvements that would make implementation easier}

## 🔵 Info [CONSIDERATIONS]

{Observations and suggestions}

## CURRENT.md Task Order Analysis

**Tasks analyzed:** {count}

### Current Task Sequence
{List tasks 1-N from CURRENT.md with status}

### Dependency Graph
```
{Visual or text representation of dependencies}
Task 1 (foundation)
  ↓
Task 2 (uses Task 1)
  ↓
Task 3 (uses Task 2)
```

## Detailed Order Analysis

### ✅/⚠️/❌ Hard Dependency Validation

**Dependency map:**
{For each task, what it requires}

**Violations found:** {count}
{List any tasks that come before their dependencies}

**Blocked tasks:** {count}
{Tasks that can't be done yet}

**Recommendations:**
{Specific reorderings to fix violations}

### ✅/⚠️/❌ Soft Dependency Optimization

**Ease analysis:**
{Which tasks would be easier if reordered}

**Suboptimal sequences:**
{Where order makes work harder than necessary}

**Recommendations:**
{Reorderings for ease of implementation}

**Estimated complexity reduction:** {percentage}% if reordered

### ✅/⚠️/❌ Structural Foundation Sequencing

**Foundation analysis:**
{What foundational patterns are needed}

**Missing foundations:**
{Patterns needed but not in task list}

**Foundation-first check:**
{Are foundations coming before features that need them?}

**Recommendations:**
{Foundational tasks to add or move earlier}

### ✅/⚠️/❌ Simplicity Sequencing

**Complexity ranking:**
{Tasks ordered by complexity}

**Current order vs. optimal:**
- Current: {actual task order}
- Optimal: {simple→complex order}

**Premature complexity:**
{Tasks trying to solve complex cases before simple ones}

**Recommendations:**
{Simpler versions to build first}

### ✅/⚠️/❌ Rework Minimization

**Rework risk assessment:** {LOW | MEDIUM | HIGH}

**Predicted rework points:**
{Where current order will cause rebuilding}

**Examples:**
- Building X before Y will require refactoring X because...
- Task A assumes B, but B will invalidate that assumption

**Rework-free alternative orderings:**
{Sequences that avoid known rework}

**Estimated rework saved:** {hours/days} if reordered

### ✅/⚠️/❌ Short-Term → Medium-Term (CURRENT.md → Milestone)

**Current milestone:** {from CURRENT.md}

**Task completion → Milestone:**
- If all tasks complete: {milestone achieved? percentage?}
- Missing tasks: {what's needed that isn't in CURRENT.md}
- Unnecessary tasks: {tasks not needed for milestone}

**Gap analysis:**
{What's missing between task list and milestone completion}

**Recommendations:**
{Tasks to add, remove, or modify}

## Implementation Status (What Exists)

**From src/ analysis:**
- Implemented: {list modules/features}
- Partially implemented: {list}
- Not started: {list from specs/ or CURRENT.md}

**Implementation vs. Plan:**
- Ahead of plan: {what exists that's not in CURRENT.md}
- Behind plan: {what's marked done but doesn't exist}
- Off plan: {implemented but not documented}

## Optimal Task Order Recommendation

**Recommended sequence:**
{Reordered task list with reasoning}

1. {Task name} - {why first}
2. {Task name} - {why second, what it builds on}
3. {Task name} - {why third}
...

**Changes from current order:**
- Moved earlier: {tasks} - {why}
- Moved later: {tasks} - {why}
- Added: {tasks} - {why needed}
- Removed: {tasks} - {why not needed}

**Expected benefits:**
- Reduced complexity: {percentage}%
- Avoided rework: {hours/days}
- Clearer learning path: {explanation}
- Faster implementation: {percentage}% estimated

## Auto-Fixable Issues

{If any issues can be fixed automatically, list them here}

The following issues can be fixed automatically:

### 🔴 Critical Fixes
1. **{Issue description}**
   - File: `CURRENT.md`
   - Fix: {what will be changed}
   - Risk: {LOW | MEDIUM}

### 🟡 Warning Fixes
1. **{Issue description}**
   - File: `CURRENT.md`
   - Fix: {what will be changed}
   - Risk: {LOW | MEDIUM}

**If no auto-fixable issues:**
"No issues can be automatically fixed. See Recommendations section for manual fixes."

## Metrics

- Task order optimality: {percentage}%
- Dependency respect: {percentage}%
- Foundation-first score: {percentage}%
- Simple→Complex adherence: {percentage}%
- Rework risk: {LOW | MEDIUM | HIGH}
- Integration coherence: {percentage}%

## Action Items

### Immediate (Task Order)
1. **Move** {task} before {task} - {reason}
2. **Add** {task} at position {N} - {reason}
3. **Remove/Defer** {task} - {reason}

### Near-term (Integration)
1. {Action to align short/medium term}

---
*This check focuses on implementation order optimization. For code quality, run /code-check. For architectural compliance, run /arch-check.*
```

## User Interaction - Auto-Fix

After writing the report, if auto-fixable issues exist, ask:

"I found {X} auto-fixable issues. Apply fixes?

Options:
- 'all' - Apply all {X} fixes
- 'critical' - Only critical ({count})
- 'warnings' - Critical + warnings ({count})
- 'safe' - Only LOW risk fixes ({count})
- 'no' - Skip auto-fix

Your choice: "

**Wait for user response.**

**If user agrees to fixes:**
1. Apply fixes in order (critical → warning → info)
2. For MEDIUM risk: Show diff before applying, ask "Apply this fix? (y/n)"
3. For HIGH risk: Always show full diff, require explicit "yes"
4. Report each fix as completed
5. Summarize changes made

**If user declines:**
"Understood. All issues are documented in the report. You can apply fixes manually."

### Common Auto-Fixable Issues for Strategy Check

**LOW risk:**
- Add missing tasks to CURRENT.md for implemented src/ features
- Update milestone progress percentage based on actual task completion

**MEDIUM risk:**
- Reorder tasks in CURRENT.md to respect hard dependencies
- Add missing foundation tasks before dependent tasks
- Move complex tasks after their simpler prerequisite tasks

**HIGH risk:**
- Remove tasks from CURRENT.md
- Significantly restructure task order

## Chat Output

After writing the report (and handling auto-fix if applicable), display in chat:

```
{✅ | ⚠️ | ❌} Strategy Check Complete

📄 Report: .quality/strategy/{TIMESTAMP}.md

Task Order: {percentage}% optimal
Integration: {percentage}% coherent

{If critical issues:}
🔴 Critical Order Issues:
1. Task {X} must come before Task {Y} (hard dependency)
2. Building {X} before {Y} will cause major refactor

Recommended Reordering:
{Top 3 task moves}

{If warnings:}
🟡 {Y} suboptimal orderings. Could improve implementation ease by {Z}%

{If all clear:}
✅ Task order optimal. Dependencies respected. Foundation-first approach.
   Integration coherent across short/medium term.

---
Tasks analyzed: {count}
Reorderings suggested: {count}
Rework avoided: {estimated hours/days}
```

## Important Notes

- **Focus on task order** - 90% of value is CURRENT.md sequencing
- **Assume strategy is sound** - Not questioning high-level decisions
- **Concrete recommendations** - Always suggest specific reorderings
- **Quantify benefits** - Estimate time/complexity saved from reordering
- **Use src/ as truth** - What exists is definitive, not specs or CURRENT.md
- **Dependency graphs** - Visualize relationships between tasks
- **Simple wins** - Often just moving one task earlier/later makes huge difference
- **Learning optimization** - Order that teaches as you go is better
- **Foundation obsession** - Always check if foundations come first

## What This Prevents

- Building features before foundations exist
- Implementing complex before understanding simple
- Creating code that needs immediate refactor
- Working on blocked tasks
- Missing prerequisite work
- Rework from poor sequencing

## The Core Question

**"Given what we're trying to build and what already exists, are we building things in the order that minimizes total effort and maximizes learning?"**

That's it. Everything else is secondary.
