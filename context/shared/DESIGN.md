# Design Decisions

Core design decisions and educational context.

---

## Core Principles

**Question-level marking**: All marking happens at the question level. Questions are the fundamental unit of analysis.

**Why:** Enables mistake pattern identification (core competitive advantage), aligns with mark schemes, provides granular feedback, can aggregate up but cannot disaggregate down.

**Multiple attempts**: Students can attempt the same question multiple times. Each attempt is stored separately with unique ID, enabling progress tracking over time.

---

## GCSE Mark Scheme Structure

### Mark Types in GCSE Maths

- **M marks (Method)**: For correct method or process, can be awarded even with arithmetic errors
- **A marks (Accuracy)**: For correct final answer, dependent on preceding M marks (M0 A1 cannot be awarded)
- **B marks (Independent)**: Awarded independent of method, for facts, statements, or correct steps
- **P marks (Process)**: For correct process as part of problem-solving
- **C marks (Communication)**: For explanations or conclusions supported by working

### How Marks Are Grouped

**Each line in a mark scheme represents one marking criterion.** Each criterion awards a specific number of marks (usually 1, sometimes 2 or 3).

**Example:**
```
M2 for a complete method, eg 4 – 2 + 3/15 − 10/15
(M1 for finding two fractions with correct common denominator)
A1 for correct answer 8 1/15
Total: 3 marks as M2+A1 OR M1+A1
```

### Key Observations

1. **Clear grouping**: Each mark scheme line is one criterion worth M1, M2, A1, etc.
2. **Hierarchical dependencies**: Some marks depend on others (e.g., "M1dep", "A1 dep on M1")
3. **Alternative paths**: Parentheses show alternatives (M2 OR M1 for partial credit)
4. **Follow-through marks**: Later marks can be awarded based on earlier incorrect work (ft)

### Implication for Data Structure

Each marking criterion should specify:
- What mark type it is (M1, M2, A1, B1, etc.)
- How many marks it's worth (1, 2, or 3)
- What the criterion is for (description)
- Dependencies on other criteria (if any)

This directly mirrors how GCSE mark schemes are structured.

**Implementation:** The `mark_criteria` table includes `depends_on_criterion_index` field to capture simple 1:1 dependencies (e.g., A1 depends on M1). This enables validation that dependent marks cannot be awarded when prerequisites score zero. For M1 milestone: complex dependencies (alternative paths, follow-through marks) are deferred.

---

## Display Mapping

How marking results map to student view:

```
Question 4: 3/5 marks (60%)

(a) Write down the 20th odd number [1/1 ✓]
    ✓ M1: Correct method for finding 20th odd number (1 mark)
    Excellent! 39 is correct.

(b) Find the smaller of these two odd numbers [2/2 ✓]
    ✓ M1: Set up equation x + (x+2) = 48 (1 mark)
    ✓ A1: Solved correctly to get x = 23 (1 mark)
    Great work showing all your steps.

(c) Is 42 a term of this sequence? [0/2 ✗]
    ✗ M1: No formula for nth term shown (1 mark)
    ✗ A1: No verification shown (1 mark)
    Remember to find the nth term formula (3n + 2) and test if 42 = 3n + 2
    has an integer solution.
```

For questions with no sub-parts, display as "Question 1: 3/3 ✓" (no letter label).

---

## Technical Implementation

See:
- `context/backend/schema/` for data models and schema design
- `specs/` for detailed implementation guidance
