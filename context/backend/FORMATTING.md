# Formatting

Output format conventions and presentation patterns.

---

## Overview

**Purpose:** Define how data from repositories is transformed into markdown for human/LLM consumption.

**Key principle:** Markdown utilities contain NO business logic. They are pure data-to-markdown transformations only.

**Location:** `src/paperlab/markdown/`

**Usage:**
- CLI commands (paper export for verification)
- Marking pipeline (LLM prompt assembly)

---

## Output Format Conventions

### Markdown Dialect

**Base:** CommonMark specification

**Extensions:**
- LaTeX math (inline: `$...$`, display: `$$...$$`)
- Blockquotes for semantic markup (diagrams)

**Compatibility:** LLM consumption, UI rendering (KaTeX), human readability

---

## Content Block Formatting

### Text Blocks

Plain markdown with embedded LaTeX. Pass through unchanged.

### Diagram Blocks

**Current format (text-only):**
```markdown
> **Diagram:** Right-angled triangle labeled ABC with sides 3cm, 4cm, 5cm
```

**Why blockquote format:**
- Standard markdown (no custom syntax)
- Semantically clear to LLMs
- Visually distinct from question text
- Easy migration to image syntax when available

**Future format:** Standard markdown image syntax `![alt](path.png)`

---

## Structural Formatting

### Header Levels

**Dynamic hierarchy via `base_level` parameter.**

| Content | Default Level |
|---------|--------------|
| Paper title | 1 |
| Questions | 2 |
| Question parts | 3 |
| Mark schemes | 4 |

**Why dynamic:** Enables different contexts (standalone question vs full paper export).

### Part Labels

Format: `(a)`, `(b)(i)`, `(c)(iii)`

### Mark Annotations

Format: `[1 mark]`, `[5 marks]` (singular/plural aware)

### Criterion Identifiers

Format: `M1 (1 mark)`, `A2 (2 marks)`, `B3 (3 marks)`

---

## Separator Conventions

- **Between content blocks:** Double newline
- **Between sections:** Markdown headers

---

## Design Principles

### Standard Markdown First

**Prefer standard markdown over custom syntax.**

**Why:** LLMs are trained on markdown, better prompt comprehension.

### Semantic Clarity

**Use clear keywords and structure.**

**Why:** LLMs recognize semantic patterns (bold keywords, blockquotes).

### No Business Logic

**Formatters never:**
- Make domain decisions
- Access database directly
- Validate data

**Formatters only:**
- Arrange data into presentation structure
- Apply consistent formatting rules

### Future-Proof

Design conventions for easy migration to future formats (text → images, markdown → HTML/JSON).

---

## Module Structure

| Module | Purpose |
|--------|---------|
| `question_formatter.py` | Questions + mark schemes → markdown |
| `paper_formatter.py` | Paper metadata → markdown |
| `mark_types_formatter.py` | Mark type definitions → markdown |
| `_helpers.py` | Shared utilities (headers, labels, annotations) |

---

## Related Documentation

- `ARCHITECTURE.md` - Where formatting fits in system
- `DATA-LOADING.md` - What data formatters receive
