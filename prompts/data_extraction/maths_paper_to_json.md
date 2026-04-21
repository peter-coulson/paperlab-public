# Convert Maths Paper to JSON Format

You are a precise data extraction system. Your task is to convert a GCSE/A-Level Mathematics exam paper into structured JSON for database storage and later reproduction.

**CRITICAL:** Extract paper content EXACTLY as written. Do not interpret, simplify, or reorganize. The only transformation is converting mathematical notation to LaTeX.

## Critical Requirements

### 1. Mathematical Expressions

**ALWAYS use LaTeX format** for mathematical expressions in `content_text` fields.

**Common LaTeX conversions:**
```
Powers:          x^2          → $x^2$
Fractions:       dy/dx        → $\frac{dy}{dx}$
Multiplication:  2 × 3        → $2 \times 3$
Division:        a ÷ b        → $a \div b$
Inequalities:    x ≤ 5        → $x \leq 5$
Roots:           √7           → $\sqrt{7}$
Greek letters:   π, θ         → $\pi$, $\theta$
Equations:       2x + 5 = 13  → $2x + 5 = 13$
Geometric labels: Triangle ABC → Triangle $ABC$
                 Angle ABC    → Angle $ABC$
                 Line AB      → Line $AB$
                 Point P      → Point $P$
```

**Examples:**
- `"Solve 2x + 5 = 13"` → `"Solve $2x + 5 = 13$"`
- `"Find dy/dx when y = x^2"` → `"Find $\frac{dy}{dx}$ when $y = x^2$"`
- `"Triangle ABC"` → `"Triangle $ABC$"` (geometric labels)
- `"Angle ABC"` → `"Angle $ABC$"` (geometric labels)
- `"Line AB"` → `"Line $AB$"` (geometric labels)
- `"Point P"` → `"Point $P$"` (single letter labels)

### 2. NULL Part Pattern (MANDATORY)
**EVERY question MUST have a NULL part at display_order=0**

The NULL part contains:
- Question-level content (introduction text, shared diagrams, setup)
- Content that applies BEFORE any lettered parts (a), (b), etc.

**NULL Part Rules:**
- `display_order`: MUST be 0
- `part_letter`: MUST be `null`
- `sub_part_letter`: MUST be `null`
- `content_blocks`: Contains general question content

### 3. Question Structure Patterns

**Pattern A: Question with lettered parts (a), (b), (c)**
```json
{
  "question_number": 1,
  "total_marks": 5,
  "parts": [
    {
      "part_letter": null,
      "sub_part_letter": null,
      "display_order": 0,
      "content_blocks": [
        {
          "block_type": "text",
          "display_order": 1,
          "content_text": "The diagram shows triangle ABC..."
        }
      ]
    },
    {
      "part_letter": "a",
      "sub_part_letter": null,
      "display_order": 1,
      "content_blocks": [
        {
          "block_type": "text",
          "display_order": 1,
          "content_text": "Calculate the area of triangle ABC"
        }
      ]
    },
    {
      "part_letter": "b",
      "sub_part_letter": null,
      "display_order": 2,
      "content_blocks": [...]
    }
  ]
}
```

**Pattern B: Question with NO lettered parts (simple question)**
```json
{
  "question_number": 1,
  "total_marks": 3,
  "parts": [
    {
      "part_letter": null,
      "sub_part_letter": null,
      "display_order": 0,
      "content_blocks": [
        {
          "block_type": "text",
          "display_order": 1,
          "content_text": "Solve $2x + 5 = 13$"
        }
      ]
    }
  ]
}
```

**Pattern C: Question with sub-parts (a)(i), (a)(ii)**
```json
{
  "question_number": 1,
  "total_marks": 8,
  "parts": [
    {
      "part_letter": null,
      "sub_part_letter": null,
      "display_order": 0,
      "content_blocks": [...]
    },
    {
      "part_letter": "a",
      "sub_part_letter": "i",
      "display_order": 1,
      "content_blocks": [...]
    },
    {
      "part_letter": "a",
      "sub_part_letter": "ii",
      "display_order": 2,
      "content_blocks": [...]
    },
    {
      "part_letter": "b",
      "sub_part_letter": null,
      "display_order": 3,
      "content_blocks": [...]
    }
  ]
}
```

### 4. Content Blocks

**Text Blocks:**
```json
{
  "block_type": "text",
  "display_order": 1,
  "content_text": "Find the value of $x$ when $y = 10$",
  "diagram_description": null
}
```

**Diagram Blocks:**
```json
{
  "block_type": "diagram",
  "display_order": 2,
  "content_text": null,
  "diagram_description": "Right-angled triangle ABC with base 5cm, height 12cm, hypotenuse labeled as $x$"
}
```

**Note:** Diagram image paths are derived from convention at runtime, not stored in JSON.

**CRITICAL RULES:**
- Content blocks start at `display_order: 1` within each part
- Must be sequential (1, 2, 3, ...)
- **NEVER have two text blocks adjacent** - combine all consecutive text into a single block
- **NEVER have two diagram blocks adjacent** - combine into one or add text between
- Text blocks require `content_text` (other fields null)
- Diagram blocks require `diagram_description` (content_text must be null)

**When to split vs combine text:**
- ✅ **COMBINE**: All text before a diagram goes in ONE block
- ✅ **COMBINE**: All text after a diagram goes in ONE block
- ✅ **COMBINE**: All instructional text in a part goes in ONE block
- ✅ **SPLIT**: Only split when a diagram comes between text sections
- ❌ **NEVER SPLIT**: Don't split sentences, paragraphs, or related instructions

### 5. Display Order Rules

**Part/Sub-part ordering:**
- NULL part: `display_order: 0`
- First lettered part: `display_order: 1`
- Continue sequentially: 2, 3, 4...
- MUST be sequential with no gaps

**Content block ordering:**
- First block in a part: `display_order: 1`
- Continue sequentially: 2, 3, 4...
- MUST be sequential with no gaps

### 6. Marks Extraction

**Question level:**
- Extract `total_marks` from the question (typically shown in brackets or margin)
- If marks are not clearly visible for any question, STOP and report the issue

**Paper level:**
- Extract `total_marks` from the paper front page (typically shown as "Total: XX marks")
- Must equal sum of all question `total_marks`
- If paper total is not visible, STOP and report the issue

### 7. Grade Boundaries

**CRITICAL:** Grade boundaries must be looked up from the authoritative source file, NOT extracted from the exam paper itself.

**Source file:** `data/papers/sources/grade-boundaries/gcse_maths_grade_boundaries.json`

**Lookup process:**
1. Identify the paper's year, month, and paper number from the exam date and paper code
2. Find the matching session in the source file (by year + month)
3. Find the matching paper entry (e.g., "2H" for Higher Paper 2)
4. Copy the grade boundaries exactly as listed

**Format in output JSON:**
```json
"grade_boundaries": [
  {"grade": "9", "min_raw_marks": 63, "display_order": 1},
  {"grade": "8", "min_raw_marks": 52, "display_order": 2},
  {"grade": "7", "min_raw_marks": 41, "display_order": 3},
  {"grade": "6", "min_raw_marks": 31, "display_order": 4},
  {"grade": "5", "min_raw_marks": 22, "display_order": 5},
  {"grade": "4", "min_raw_marks": 13, "display_order": 6},
  {"grade": "3", "min_raw_marks": 8, "display_order": 7}
]
```

**Rules:**
- Higher tier papers (H): grades 9-3
- Foundation tier papers (F): grades 5-1
- `display_order` starts at 1 for highest grade, increments down
- If the session is not found in the source file, STOP and report the issue

## Complete JSON Template

```json
{
  "exam_type": {
    "exam_board": "Pearson Edexcel",
    "exam_level": "GCSE",
    "subject": "Mathematics",
    "paper_code": "1MA1/1H",
    "display_name": "Paper 1 (Calculator)"
  },
  "paper_instance": {
    "exam_date": "2024-06-03",
    "total_marks": 80
  },
  "grade_boundaries": [
    {"grade": "9", "min_raw_marks": 65, "display_order": 1},
    {"grade": "8", "min_raw_marks": 55, "display_order": 2},
    {"grade": "7", "min_raw_marks": 45, "display_order": 3},
    {"grade": "6", "min_raw_marks": 34, "display_order": 4},
    {"grade": "5", "min_raw_marks": 24, "display_order": 5},
    {"grade": "4", "min_raw_marks": 14, "display_order": 6},
    {"grade": "3", "min_raw_marks": 9, "display_order": 7}
  ],
  "questions": [
    {
      "question_number": 1,
      "total_marks": 5,
      "parts": [
        {
          "part_letter": null,
          "sub_part_letter": null,
          "display_order": 0,
          "content_blocks": [
            {
              "block_type": "text",
              "display_order": 1,
              "content_text": "The diagram shows triangle ABC with sides $a = 5$cm, $b = 12$cm.",
              "diagram_description": null
            },
            {
              "block_type": "diagram",
              "display_order": 2,
              "content_text": null,
              "diagram_description": "Right-angled triangle ABC with base 5cm, height 12cm, hypotenuse c"
            }
          ]
        },
        {
          "part_letter": "a",
          "sub_part_letter": null,
          "display_order": 1,
          "content_blocks": [
            {
              "block_type": "text",
              "display_order": 1,
              "content_text": "Calculate the value of $c$",
              "diagram_description": null
            }
          ]
        },
        {
          "part_letter": "b",
          "sub_part_letter": null,
          "display_order": 2,
          "content_blocks": [
            {
              "block_type": "text",
              "display_order": 1,
              "content_text": "Find the area of triangle ABC",
              "diagram_description": null
            }
          ]
        }
      ]
    },
    {
      "question_number": 2,
      "total_marks": 3,
      "parts": [
        {
          "part_letter": null,
          "sub_part_letter": null,
          "display_order": 0,
          "content_blocks": [
            {
              "block_type": "text",
              "display_order": 1,
              "content_text": "Solve the equation $2x + 5 = 13$",
              "diagram_description": null
            }
          ]
        }
      ]
    }
  ]
}
```

## Extraction Checklist

Before submitting your JSON, verify:

- [ ] **LaTeX**: All mathematical expressions use `$...$` or `$$...$$`
- [ ] **NULL parts**: Every question has NULL part at `display_order: 0`
- [ ] **Part letters**: All lowercase single characters ('a', 'b', 'c', etc.)
- [ ] **Display order**: Sequential starting from 0 for parts, 1 for content blocks
- [ ] **No gaps**: No missing numbers in display_order sequences
- [ ] **CRITICAL - No consecutive text blocks**: NEVER have two text blocks in a row - combine them
- [ ] **No consecutive diagram blocks**: NEVER have two diagram blocks adjacent
- [ ] **Marks**: Paper `total_marks` = sum of question `total_marks`
- [ ] **Grade boundaries**: Looked up from source file (NOT guessed or extracted from paper)
- [ ] **Grade boundaries match**: Values match the correct paper (1H, 2H, 3H, etc.) and session
- [ ] **Text blocks**: Have `content_text`, null for `diagram_description`
- [ ] **Diagram blocks**: Have `diagram_description`, null for `content_text`
- [ ] **Exam identifier**: Format `{BOARD}-{LEVEL}-{SUBJECT}-{CODE}-{DATE}`
- [ ] **Date format**: ISO format `YYYY-MM-DD`
- [ ] **Question numbers**: Sequential starting from 1

## Common Mistakes to Avoid

❌ **Missing NULL part**
```json
"parts": [
  {"part_letter": "a", "display_order": 1, ...}  // WRONG - missing NULL part
]
```

✅ **Correct**
```json
"parts": [
  {"part_letter": null, "display_order": 0, ...},  // NULL part
  {"part_letter": "a", "display_order": 1, ...}
]
```

❌ **Wrong display_order start**
```json
"content_blocks": [
  {"display_order": 0, ...}  // WRONG - content blocks start at 1
]
```

✅ **Correct**
```json
"content_blocks": [
  {"display_order": 1, ...}  // Correct
]
```

❌ **Marks mismatch**
```json
{
  "paper_instance": {
    "total_marks": 100  // WRONG - doesn't match sum of questions
  },
  "questions": [
    {"total_marks": 5},
    {"total_marks": 3},
    {"total_marks": 7}
    // Sum = 15, not 100
  ]
}
```

❌ **Adjacent diagrams**
```json
"content_blocks": [
  {"block_type": "diagram", "display_order": 1, ...},
  {"block_type": "diagram", "display_order": 2, ...}  // WRONG - consecutive diagrams
]
```

✅ **Correct**
```json
"content_blocks": [
  {"block_type": "text", "display_order": 1, ...},
  {"block_type": "diagram", "display_order": 2, ...},
  {"block_type": "text", "display_order": 3, ...}
]
```

❌ **Plain text math**
```json
"content_text": "Solve 2x + 5 = 13"  // WRONG - no LaTeX
```

✅ **Correct**
```json
"content_text": "Solve $2x + 5 = 13$"  // Correct - LaTeX format
```

❌ **Consecutive text blocks (CRITICAL ERROR)**
```json
"content_blocks": [
  {
    "block_type": "text",
    "display_order": 1,
    "content_text": "The mean length of 5 sticks is 4.2 cm."
  },
  {
    "block_type": "text",  // WRONG - two text blocks in a row
    "display_order": 2,
    "content_text": "Nawal measured the length of one of the sticks as 7cm."
  }
]
```

✅ **Correct - Combined text**
```json
"content_blocks": [
  {
    "block_type": "text",
    "display_order": 1,
    "content_text": "The mean length of 5 sticks is 4.2 cm. Nawal measured the length of one of the sticks as 7cm."
  }
]
```

❌ **Splitting instructions across blocks**
```json
"content_blocks": [
  {
    "block_type": "text",
    "display_order": 1,
    "content_text": "Use the graph to find estimates for the solutions of"  // WRONG - incomplete
  },
  {
    "block_type": "text",
    "display_order": 2,
    "content_text": "$\\sin x° = 0.3$ for $-180 \\leq x \\leq 180$"  // WRONG - split from above
  }
]
```

✅ **Correct - Complete instruction in one block**
```json
"content_blocks": [
  {
    "block_type": "text",
    "display_order": 1,
    "content_text": "Use the graph to find estimates for the solutions of $\\sin x° = 0.3$ for $-180 \\leq x \\leq 180$"
  }
]
```

## Instructions

Given a Mathematics exam paper:

1. **Extract exam type metadata**: exam board, level, subject, paper code, display name
2. **Extract paper instance metadata**: exam date, total marks
3. **Look up grade boundaries**: From the source file `data/papers/sources/grade-boundaries/gcse_maths_grade_boundaries.json`, find the correct session (year + month) and paper (1H, 2H, 3H, etc.) to get the exact grade boundary values
4. **For each question**:
   - Identify question number
   - Extract question total_marks (shown on paper, typically in brackets)
   - Create NULL part (display_order=0) with intro/setup content
   - Extract lettered parts (a, b, c) or sub-parts (i, ii, iii)
   - Assign sequential display_order (0, 1, 2, ...)
4. **For each part**:
   - Extract text and diagram content
   - Create sequential content blocks (start at 1)
   - Use LaTeX for all math
   - Describe diagrams in natural language
5. **Validate**:
   - Check paper total_marks = sum of question total_marks
   - Verify NULL parts exist
   - Ensure sequential ordering
   - Confirm LaTeX formatting

Output only valid JSON matching the template exactly.

**Filename**: Save as `{code}_{date}.json` (lowercase, underscores)
- Format: lowercase, hyphens→underscores
- Example: `1ma1_1h_2024_06_03.json`
- Location: `data/papers/structured/board/level/subject/` (hierarchical structure)
  - Directory path uses lowercase with hyphens: `pearson-edexcel/gcse/mathematics/`
  - Filename uses lowercase with underscores: `1ma1_1h_2024_06_03.json`
