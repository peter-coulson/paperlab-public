# Validation Models

*High-level validation approach for LLM responses*

---

## Purpose

Pydantic models validate LLM response structure before storage. Ensures type safety and catches malformed responses early.

---

## Validation Flow

```
1. LLM returns JSON response
2. Pydantic validates structure (types, ranges, required fields)
3. Match array index to mark_criteria UUIDs
4. Validate marks_awarded ≤ marks_available
5. Store parsed results + raw response
```

---

## What Gets Validated

**LLM Response Structure:**
- Correct field types (int, str, float)
- Required fields present
- Value ranges (marks ≥ 0, confidence 0.0-1.0)
- Non-empty feedback strings
- Criteria list not empty

**Against Database:**
- Criteria count matches expected
- marks_awarded ≤ marks_available per criterion
- Array-index mapping to criterion UUIDs
- Dependency validation: marks awarded only when prerequisites met (e.g., cannot award A1 if M1 got 0 marks)

---

## Error Handling

**Pydantic ValidationError** → LLM returned invalid structure (wrong types, missing fields, invalid ranges)

**Criteria Count Mismatch** → LLM returned wrong number of criteria - likely prompt issue

**Marks Exceeded** → LLM awarded more marks than available - validation logic issue

**Dependency Violation** → LLM awarded dependent marks without prerequisite (e.g., A1 awarded when M1 got 0) - indicates LLM misunderstood mark scheme dependencies

**All errors:** Store raw LLM response for debugging, even on validation failure

---

## Implementation

Pydantic model definitions and validation logic live in `src/paperlab/marking/models.py`.
