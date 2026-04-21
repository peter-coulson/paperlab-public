# Data Loading

How external data (JSON) enters the database.

---

## Overview

**Purpose:** Load educational content and evaluation data from JSON into SQL databases.

**Pipelines:**

| Pipeline | Source | Target | Module |
|----------|--------|--------|--------|
| LLM Models | llm_models.json | marking.db | `loading/` |
| Exam Config | exam configs JSON | marking.db | `loading/` |
| Validation Types | validation_types.json | evaluation_results.db | `loading/` |
| Papers | paper.json | marking.db | `loading/` |
| Mark Schemes | marks.json | marking.db | `loading/` |
| Test Cases | test_case.json | evaluation_results.db | `evaluation/` |
| Test Suites | test_suite.json | evaluation_results.db | `evaluation/` |

**Shared Infrastructure:** `src/paperlab/loaders/` - Generic framework for all loaders

---

## Workflow

```
1. db init → creates schema → loads config → loads sample papers
2. LLM extracts structure from PDFs → JSON files
3. Paper loader: paper.json → papers → questions → parts → content
4. Mark scheme loader: marks.json → criteria (attaches to existing parts)
```

**Paper-first rationale:**
- Matches real-world workflow (papers published before mark schemes)
- Simpler implementation (mark scheme attaches to existing structure)
- Better error messages ("Load paper first" vs structure mismatch)

---

## Three-Layer Validation

| Layer | Where | What |
|-------|-------|------|
| **1. Pydantic** | `models/` | Types, required fields, string limits, LaTeX sanitization |
| **2. Business** | `validators/` | References exist, totals match, no duplicates |
| **3. Database** | `schema.sql` | Foreign keys, uniqueness, CHECK constraints |

**Why separate?** Different concerns, different error handling. Fail fast with clear messages.

---

## Key Design Patterns

### NULL Part/Criterion

**Every question has a structural NULL part at `display_order=0`.**

**Purpose:**
- Container for general question content (intro text, shared diagrams)
- Container for general marking guidance or all marks for questions without lettered parts

**Three NULL criterion patterns:**
1. **Structural placeholder** - `mark_type_code = null` → Not inserted (JSON validation only)
2. **General guidance** - `mark_type_code = 'GENERAL'` → Inserted
3. **Questions without parts** - `mark_type_code = 'M1'/etc.` → Inserted

**Why:** Consistent structure, simplifies loader logic, mirrors database schema.

### Part Identity

**Format:**
- `part_letter`: lowercase a-z or null
- `sub_part_letter`: lowercase roman i-x or null
- `display_order`: sequential from 0

**Examples:** `(null, null, 0)`, `('a', null, 1)`, `('b', 'i', 2)`

### Cross-File Consistency

**When loading mark scheme, validates:**
1. Paper exists (via exam_identifier)
2. Questions match (number, total_marks)
3. Parts match (part_letter, sub_part_letter)
4. Marks totals consistent

**Why:** Catches PDF extraction errors, ensures same exam.

---

## Transaction Management

**Pattern:** Loaders manage transactions, repositories execute SQL.

**Flow:**
1. Parse and validate JSON
2. Create records via repositories (no commits in repos)
3. Verify counts before commit
4. Loader commits or rollbacks

**Why:** Enables verification before commit. All operations atomic.

---

## Loader Framework

**All loaders support:**
- `--replace` flag for updates (with confirmation)
- `--force` flag for CI/automation
- Diff calculation (shows changes)
- Destructive change warnings

**Consistent workflow:**
1. Parse JSON → 2. Check exists → 3. If replace: diff → confirm → delete → recreate → 4. Verify → 5. Commit

---

## Design Rationale

**Why two separate paper/marks pipelines?**
- Separate PDF documents with different extraction tasks
- Mark schemes may be updated independently
- Can batch process mark schemes

**Why three validation layers?**
- Pydantic: Fast fail on malformed JSON
- Business: Semantic errors before database
- Database: Final integrity enforcement

**Why NULL part/criterion?**
- Consistent structure across all questions
- No special cases in loader logic
- Enables general content and guidance

---

## JSON Format

**See:** `../shared/JSON-FORMATS.md` for complete specification.

**Storage:** `data/papers/structured/board/level/subject/{paper_code}.json` and `{paper_code}_marks.json`
