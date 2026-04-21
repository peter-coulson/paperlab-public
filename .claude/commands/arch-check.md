You are conducting an **Architecture Compliance Check** for this codebase.

Think hard about the architectural patterns, layer boundaries, and design principles - this requires deep reasoning about system structure, SOLID principles, and architectural compliance.

## Objective

Validate that the codebase structure and design adhere to the architectural principles and design patterns defined in project documentation. This is a structural analysis focused on system-level design decisions.

## Prerequisites

**CRITICAL:** Before starting, verify context health:
- Run /context-check if uncertain about documentation integrity
- Check that `CLAUDE.md` exists and is valid
- Check that context documentation exists (read context/README.md for navigation)
- If these don't exist or have issues, STOP and report the problem

## Context Files to Read

Required reading:
- `CLAUDE.md` - Core architectural principles
- `context/` directory - Architectural decisions, design patterns, and technical approach
  - Read `context/README.md` first for navigation to architecture docs
- `src/` directory structure (if exists)

## Architectural Principles to Validate

### From CLAUDE.md

#### Architecture (Design Decisions)
1. **Question-level foundation** - Questions are fundamental unit of analysis
2. **Subject-agnostic design** - Core logic identical for all subjects and levels
3. **Layered architecture** - Clear separation: CLI → Domain Logic → Data Access → Database
4. **Extreme modularity** - Each module has one reason to change

#### Implementation
5. **Expand through data, not code** - New boards/subjects/levels add config, never conditionals

### SOLID Principles

6. **Single Responsibility Principle (SRP)** - Each module/class has one reason to change
7. **Open/Closed Principle (OCP)** - Open for extension, closed for modification
8. **Liskov Substitution Principle (LSP)** - Subtypes must be substitutable for base types
9. **Interface Segregation Principle (ISP)** - Many specific interfaces over one general interface
10. **Dependency Inversion Principle (DIP)** - Depend on abstractions, not concretions

### Design Patterns

11. **Composition over Inheritance** - Favor object composition over class inheritance
12. **Dependency Injection** - Dependencies passed in, not created internally
13. **Strategy Pattern** - For subject/level variations (if applicable)

## Checks to Perform

### 1. Question-Level Foundation
- Is the Question entity central to the domain model?
- Do other entities compose/reference Questions rather than bypass them?
- Is question parsing/analysis the core abstraction?

**Violations:**
- Paper entity that doesn't use Question
- Mark calculations that bypass Question entity
- Analysis logic that operates on raw data instead of Question objects

### 2. Subject-Agnostic Design
- **Critical:** No subject-specific or level-specific conditionals in core logic
- Subject/level differences implemented through:
  - Configuration files
  - Strategy pattern
  - Data-driven behavior

**Violations:**
- `if (subject === 'maths')` in domain/core code
- Hard-coded subject names in business logic
- Level-specific code paths in marking engine

### 3. Layered Architecture

**Expected layers:**
```
CLI Layer (commands, user interaction)
  ↓ depends on
Domain Layer (business logic, entities, services)
  ↓ depends on
Data Access Layer (repositories, queries)
  ↓ depends on
Database Layer (schema, connections)
```

**Check:**
- No reverse dependencies (lower layers importing higher layers)
- CLI doesn't import database directly
- Domain layer is framework-agnostic
- Clear boundaries between layers
- **Connection management:** CLI opens connections and passes to business logic/repositories as parameters
- Business logic NEVER opens connections (receives as parameters)
- Repository layer NEVER opens connections (receives as parameters)

**Violations:**
- CLI directly imports database
- Data access layer imports CLI
- Domain logic contains SQL queries
- Database schema leaked to CLI
- Business logic opens database connections using `with connection()`
- Repository functions open connections using `with connection()`
- Business logic imports `connection` from `database.py`

**How to check:**
- Search loading/, evaluation/, marking/ for `with connection(` or `from paperlab.data.database import connection`
- Search data/repositories/ for `with connection(`
- Valid: CLI layer (src/paperlab/cli/commands/) opening connections
- Exception: BatchMarker creates connections per worker thread (thread safety)

### 4. Extreme Modularity (SRP)

**Check each module:**
- Single, clear responsibility
- One reason to change
- High cohesion within module
- Loose coupling between modules

**Violations:**
- Module handling both parsing AND marking
- Service doing validation AND persistence
- Utility file with unrelated functions

### 5. Expand Through Data, Not Code (OCP)

**Check:**
- New subjects/boards/levels require ONLY config changes
- No conditional logic for different exam boards
- Extensible through data files or database entries

**Violations:**
- Switch statements on board names
- Conditional imports based on subject
- Hard-coded mark schemes per board

### 6-10. SOLID Principles

**SRP:** Already covered in #4

**OCP:**
- Can add new features without modifying existing code?
- Using interfaces/abstract classes for extension points?

**LSP:**
- Can substitute implementations without breaking behavior?
- Derived classes honor base class contracts?

**ISP:**
- Interfaces are focused and specific?
- No "fat interfaces" forcing unused method implementations?

**DIP:**
- High-level modules don't depend on low-level modules?
- Both depend on abstractions (interfaces)?
- Dependency injection used instead of direct instantiation?

### 11. Composition Over Inheritance

**Check:**
- Minimal inheritance hierarchies (ideally none beyond 1 level)
- Behavior added through composition
- Interfaces used for contracts, not base classes

**Violations:**
- Deep inheritance trees (>2 levels)
- Behavior only available through inheritance
- Abstract classes used where interfaces would work

### 12. Directory Structure

**Expected structure:**
```
src/
  cli/           # CLI layer
  domain/        # Business logic
    entities/    # Domain objects
    services/    # Business operations
  data/          # Data access layer
    repositories/
  db/            # Database layer
    schema/
```

**Check:**
- Structure reflects layered architecture
- Clear separation of concerns
- No circular directory dependencies

### 13. Cross-Cutting Concerns

**Check:**
- Logging: Consistent, not scattered
- Validation: At layer boundaries
- Error handling: Centralized strategy
- Configuration: Single source of truth

## Output Format

Generate a timestamped report and save to `.quality/arch/{TIMESTAMP}.md`

Use format: `YYYY-MM-DD-HHMMSS` for timestamp (e.g., `2025-10-18-143045.md`)

### Report Structure

```markdown
# Architecture Compliance Check
**Run:** {TIMESTAMP}
**Commit:** {git hash if available}
**Status:** {✅ All Clear | ⚠️ Issues Found | ❌ Critical Issues}

## Summary
- Modules analyzed: {count}
- Principles checked: 13
- Issues found: {Critical: X, Warning: Y, Info: Z}
- Architecture compliance: {percentage}%

## 🔴 Critical Issues [MUST FIX BEFORE PROCEEDING]

1. **[Principle Violated]** Description
   Location: `{file:line}`
   Issue: {what's wrong}
   Impact: {why this is critical}
   Fix: {concrete refactoring steps}

## 🟡 Warnings [SHOULD FIX SOON]

{Same format}

## 🔵 Info [CONSIDER]

{Same format}

## Detailed Analysis

### ✅/⚠️/❌ Question-Level Foundation
{Analysis}

### ✅/⚠️/❌ Subject-Agnostic Design
{Analysis + specific violations if any}

### ✅/⚠️/❌ Layered Architecture
{Dependency graph, violations}

### ✅/⚠️/❌ Extreme Modularity (SRP)
{Per-module analysis}

### ✅/⚠️/❌ Expand Through Data (OCP)
{Config vs code analysis}

### ✅/⚠️/❌ SOLID Compliance
- **SRP:** {score/analysis}
- **OCP:** {score/analysis}
- **LSP:** {score/analysis}
- **ISP:** {score/analysis}
- **DIP:** {score/analysis}

### ✅/⚠️/❌ Composition Over Inheritance
{Inheritance tree analysis}

### ✅/⚠️/❌ Directory Structure
{Structure validation}

### ✅/⚠️/❌ Cross-Cutting Concerns
{Logging, validation, errors, config}

## Metrics

- Total modules: {count}
- Layering violations: {count}
- Subject-specific conditionals found: {count}
- Inheritance depth (max): {number}
- Circular dependencies: {count}
- Single responsibility compliance: {percentage}%

## Auto-Fixable Issues

{If any issues can be fixed automatically, list them here}

The following issues can be fixed automatically:

### 🔴 Critical Fixes
1. **{Issue description}**
   - File: `{file:line}`
   - Fix: {what will be changed}
   - Risk: {LOW | MEDIUM}

### 🟡 Warning Fixes
1. **{Issue description}**
   - File: `{file:line}`
   - Fix: {what will be changed}
   - Risk: {LOW | MEDIUM}

### 🔵 Info Fixes
1. **{Issue description}**
   - File: `{file:line}`
   - Fix: {what will be changed}
   - Risk: {LOW}

**If no auto-fixable issues:**
"No issues can be automatically fixed. See Recommendations section for manual fixes."

## Recommendations

{Prioritized list of refactoring actions}

1. **[HIGH]** {action}
2. **[MEDIUM]** {action}
3. **[LOW]** {action}

## Architecture Health Trend

{If previous reports exist, show improvement/regression}

---
*Next Steps: Fix critical issues before proceeding to /code-check*
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

### Common Auto-Fixable Issues for Architecture Check

**LOW risk:**
- Extract hard-coded subject names to config files
- Add missing type exports to barrel files
- Reorder imports alphabetically

**MEDIUM risk:**
- Move imports to fix layer violations
- Extract shared types to eliminate circular dependencies
- Rename files/modules to match conventions

**HIGH risk:**
- Refactor to break layer violations
- Extract business logic from data access layer
- Restructure modules for SRP compliance

## Chat Output

After writing the report (and handling auto-fix if applicable), display in chat:

```
{✅ | ⚠️ | ❌} Architecture Check Complete

📄 Report: .quality/arch/{TIMESTAMP}.md
Status: {X Critical, Y Warnings, Z Info}
Compliance: {percentage}%

{If critical issues:}
🔴 Critical Issues:
1. {Principle} - {file:line} - {brief description}
2. {Principle} - {file:line} - {brief description}

Top Recommendations:
1. {action}
2. {action}

{If critical:}
⚠️  Fix critical architectural issues before running /code-check

{If warnings only:}
✅ No blocking issues. Can proceed to /code-check
   Consider addressing {Y} warnings for better architecture.

{If all clear:}
✅ Architecture fully compliant. Safe to run /code-check
```

## Important Notes

- **Be strict** - Architecture violations compound over time
- **Provide concrete examples** - Show the violating code
- **Suggest specific fixes** - Not just "fix this", but HOW to fix it
- **Consider scalability** - Will this design support 10+ exam boards?
- **Check extension points** - Is it actually easy to add new subjects?
- **Use grep to find violations** - Search for subject names, conditionals, etc.
- **Analyze imports** - Build dependency graph to find layer violations
- **If no src/ exists yet** - Check if specs/architecture align with principles

## Common Violations to Watch For

- Hard-coded subject names anywhere in src/
- Direct database imports in CLI layer
- Business logic in data access layer
- Multiple responsibilities in single module
- Deep inheritance hierarchies
- Fat interfaces with many methods
- New/direct instantiation instead of dependency injection
- Conditional logic for different exam boards
