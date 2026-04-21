# JSON Input Formats

Format specification for paper and mark scheme JSON files.

---

## Overview

**Two-file system:**
1. **Paper JSON** - Question structure and content (`{paper_id}.json`)
2. **Mark Scheme JSON** - Marking criteria (`{paper_id}_marks.json`)

**Storage:** `data/papers/structured/{board}/{level}/{subject}/`

**Schema definition:**
- Paper: `src/paperlab/loading/models/papers.py`
- Marks: `src/paperlab/loading/models/marks.py`

**Working examples:** `data/papers/structured/pearson-edexcel/gcse/mathematics/*.json`

**Loading:** Papers must be loaded before mark schemes (referential integrity).

---

## Key Patterns

### NULL Part Pattern

**Every question has a NULL part** (`display_order=0`, `part_letter=null`):
- Contains general question content (shared text/diagrams)
- Shows before lettered parts (a, b, c)
- May contain GENERAL mark criteria (question-level guidance)

**Three mark scheme patterns:**

1. **Structural placeholder** (no guidance):
   - Empty criterion with `mark_type_code: null`
   - Not inserted into database (JSON validation only)

2. **General guidance** (question-level instructions):
   - `mark_type_code: "GENERAL"`, `marks_available: 0`
   - Example: "Accept equivalent algebraic forms throughout"
   - Inserted into database

3. **Questions without parts** (all marks at question level):
   - `mark_type_code: "M"`, actual marks
   - All marking criteria at display_order=0

**Rationale:** Consistent structure simplifies loader logic and mirrors database schema exactly.

### Display Order Semantics

**Parts:** Start at 0 (NULL part always first)
- NULL part: `display_order=0`
- Part (a): `display_order=1`
- Part (b): `display_order=2`

**Content blocks:** Start at 1 within each part

**Mark criteria:** Absolute numbering across entire question (not per-part)
- Part (a) M1: `display_order=1`
- Part (a) A1: `display_order=2`
- Part (b) M1: `display_order=3` ← continues from part (a)
- Part (b) A1: `display_order=4`

**Rationale:** Dependencies can cross part boundaries (part b depends on part a). Maps directly to database `criterion_index` field (UNIQUE per question).

### Part Identity

**Format:**
- `part_letter`: Single lowercase character (a-z) or `null`
- `sub_part_letter`: Lowercase roman numerals (i, ii, iii, ...) or `null`
- `display_order`: Sequential integers starting from 0

**Examples:**
- NULL part: `part_letter: null, sub_part_letter: null, display_order: 0`
- Part (a): `part_letter: "a", sub_part_letter: null, display_order: 1`
- Part (b)(i): `part_letter: "b", sub_part_letter: "i", display_order: 2`
- Part (b)(ii): `part_letter: "b", sub_part_letter: "ii", display_order: 3`

### Mathematical Expressions

**Use LaTeX notation:**

**Inline math:** `$...$`
- Examples: `$x^2 + 5x$`, `$\frac{dy}{dx}$`, `$2 \times 3$`

**Display math:** `$$...$$`
- For standalone equations

**Rationale:** LaTeX works with LLMs, UI renderers (KaTeX), and markdown. Subject-agnostic standard.

**See:** Working examples in `data/papers/structured/pearson-edexcel/gcse/mathematics/*.json`

### Expected Answer

**Every question part should include `expected_answer`:**

**Format:**
- LaTeX for math: `"$6$"`, `"$\\frac{3}{4}$"`, `"$x = 5$"`
- Plain text: `"France"`, `"metaphor"`
- `null` for structural NULL parts or GENERAL-only guidance

**Business rule (Mathematics):**
- Parts with actual marking criteria must have `expected_answer`
- NULL parts with only GENERAL criteria may have `null`

**Rationale:** Enables automated answer checking. Lives at part level (answers correspond to parts, not individual marking steps).

### Tiered Marking (Partial Credit)

**Pattern:** Some criteria offer tiered scoring where students receive ONLY the highest mark they qualify for (not a sum).

**JSON representation:** Create ONE criterion (not two) with the higher marks_available value. Combine both descriptions with conditional wording in content_blocks.

**Critical:** Do NOT create two separate criteria totaling 3 marks when maximum is 2.

**Rationale:** Prevents double-counting. Reflects actual semantics (partial credit is alternative, not additive).

### Dependencies

**Criteria can depend on earlier criteria** via `depends_on_display_order` field.

**Rules:**
- Must reference earlier criterion (lower `display_order`)
- `null` means independent
- Database enforces dependency references exist

**Example:** A1 (accuracy) depends on M1 (method). If student gets M0, they cannot receive A1.

### Additional Guidance

**Format:** `[Guidance: {text}]` appended to criterion content

**Rationale:** Keeps guidance with criterion. Square brackets distinguish from criteria text. No schema changes needed.

### Content Block Sequencing

**Rules:**
- Sequential `display_order` starting from 1 within each part
- No consecutive blocks of same type

**Validation:**
- Invalid: Two text blocks adjacent (combine into one)
- Invalid: Two diagram blocks adjacent (add text between)
- Valid: Alternating text and diagrams
- Valid: All text (single block)

**Rationale:** Consecutive text blocks should be combined. Consecutive diagrams suggest missing descriptive text.

**Enforcement:** Database trigger prevents consecutive diagrams. Pydantic validation prevents consecutive text.

### Diagram Image Paths

**Diagram paths are derived from convention, not stored in database or JSON.**

**API endpoint:** `/api/diagrams/{board}/{level}/{subject}/{paper_stem}/q{NN}.png`

**Local file convention:** `data/papers/structured/{board}/{level}/{subject}/diagrams/{paper_stem}/q{NN}.png`

**Paper stem format:** `{paper_code}_{exam_date}` with underscores (e.g., `1ma1_1h_2023_11_08`)

**Rationale:** Convention-based paths eliminate duplication and ensure consistency. The API layer derives paths from paper metadata (board, level, subject, paper_code, exam_date) and question number.

---

## File Naming Convention

**Pattern:** `{paper_code}_{exam_date}.json` and `{paper_code}_{exam_date}_marks.json`

**Examples:**
- `1ma1_1h_2023_11_08.json` (paper)
- `1ma1_1h_2023_11_08_marks.json` (marks)

**Location:** `data/papers/structured/{board}/{level}/{subject}/`

---

## Validation

**Three layers ensure data quality:**

1. **Pydantic (Structural):** Type checking, required fields, sequential numbering, format validation, length limits
2. **Business Logic:** Database references exist, marks totals match, no duplicates, mark type rules
3. **Database:** Foreign keys, uniqueness constraints, CHECK constraints, triggers

**See:** `DATA-LOADING.md` for complete validation strategy and implementation details.

---

## Design Rationale

**Why NULL part at display_order=0?**
- Consistent structure across all questions (no special cases)
- Simplifies loader logic and validation
- Enables general content and marking guidance
- Mirrors database schema exactly

**Why expected_answer at part level?**
- Answers correspond to question parts, not marking steps
- Single source of truth for automated checking
- Matches conceptual model (students answer parts, not criteria)

**Why LaTeX for math?**
- Works with LLMs, UI renderers, and markdown
- Prevents notation ambiguity
- Subject-agnostic standard
- Industry standard for mathematical typesetting

**Why separate paper/marks files?**
- Papers loaded before marks (referential integrity)
- Different LLM extraction prompts
- Independent update cycles
- Clear separation of concerns

**Why content_blocks array?**
- Preserves content ordering (text, diagrams, more text)
- Enables alternating text and diagrams
- Maps directly to database structure
- Flexible for future content types

**Why absolute criterion numbering?**
- Dependencies can cross part boundaries
- Maps to database `criterion_index` (UNIQUE per question)
- Simpler validation than relative ordering

---

## Related Documentation

- **DATA-LOADING.md** → Validation strategy and loading pipeline
- **DESIGN.md** → Domain concepts (mark types, question-level marking)
- **Pydantic models:** `src/paperlab/loading/models/papers.py`, `src/paperlab/loading/models/marks.py`
- **Working examples:** `data/papers/structured/pearson-edexcel/gcse/mathematics/`
