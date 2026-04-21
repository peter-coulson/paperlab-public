# Code Check - Recommendations

Analyze recent code changes and recommend which module code checks should be run.

## Objective

Help prioritize code quality checks by analyzing:
1. When each module was last checked
2. How much each module has changed since last check
3. How recently changes occurred (weight recent changes higher)

**Output:** Terminal display only - no report file created

## Analysis Steps

### Step 1: Find Last Check Dates

For each module, find the most recent code quality check report:

```bash
# Extract timestamp from most recent report for each module
for module in data loading evaluation cli domain services config utils api; do
  latest=$(ls -t .quality/code/${module}-*.md 2>/dev/null | head -1)
  if [ -n "$latest" ]; then
    # Extract commit from report
    commit=$(grep "^\*\*Commit:\*\*" "$latest" | head -1 | awk '{print $2}')
    date=$(git log -1 --format='%ci' "$commit" 2>/dev/null | cut -d' ' -f1)
    echo "$module|$commit|$date"
  else
    echo "$module|never|never"
  fi
done
```

### Step 2: Calculate Changes Per Module

For each module, count files changed since last check:

```bash
# For modules with previous checks
git diff --name-only {last_check_commit}..HEAD -- src/paperlab/{module}/ | wc -l

# For modules never checked
find src/paperlab/{module}/ -name "*.py" | wc -l
```

Also get recency of changes (days since last change):

```bash
# Most recent change in module
git log -1 --format='%ci' -- src/paperlab/{module}/ | cut -d' ' -f1
```

### Step 3: Calculate Priority Scores (0-10)

For each module, calculate a recommendation score based on:

**Factors:**
- **Days since last check** (weight: 30%)
  - Never checked: 10 points
  - >7 days: 8-10 points (linear)
  - 4-7 days: 5-7 points
  - 1-3 days: 2-4 points
  - <1 day: 0-1 points

- **Files changed since last check** (weight: 40%)
  - Calculate as percentage of module files changed
  - 0%: 0 points
  - 1-10%: 2-4 points
  - 11-25%: 5-6 points
  - 26-50%: 7-8 points
  - >50%: 9-10 points

- **Recency of changes** (weight: 30%)
  - Changed today: 10 points
  - Changed yesterday: 8 points
  - Changed 2-3 days ago: 6 points
  - Changed 4-7 days ago: 4 points
  - Changed >7 days ago: 2 points
  - No changes since last check: 0 points

**Final Score:** Weighted average, rounded to 1 decimal

## Output Format

Display directly in terminal (no file created):

```
📊 Code Check Recommendations

Time period analyzed: Last 7 days
Current commit: {hash}

┌─────────────┬──────────┬────────────────┬──────────────┬──────────────┬────────────────────┐
│ Module      │ Priority │ Last Checked   │ Days Ago     │ Files Chgd   │ Last Change        │
├─────────────┼──────────┼────────────────┼──────────────┼──────────────┼────────────────────┤
│ loading     │ 🔴  9.2  │ 2025-10-30     │ 7 days       │ 12 / 23      │ Today              │
│ evaluation  │ 🟠  7.8  │ 2025-11-01     │ 5 days       │ 6 / 21       │ Yesterday          │
│ domain      │ 🟠  6.5  │ Never          │ Never        │ N/A          │ 3 days ago         │
│ cli         │ 🟡  4.2  │ 2025-11-04     │ 2 days       │ 2 / 12       │ 2 days ago         │
│ services    │ 🟡  3.1  │ 2025-11-05     │ 1 day        │ 1 / 5        │ Yesterday          │
│ data        │ 🟢  1.8  │ 2025-11-05     │ 1 day        │ 0 / 38       │ 5 days ago         │
│ config      │ 🟢  0.5  │ 2025-11-04     │ 2 days       │ 0 / 5        │ 7 days ago         │
│ utils       │ 🟢  0.0  │ 2025-11-03     │ 3 days       │ 0 / 5        │ 10 days ago        │
│ api         │ 🟠  6.0  │ 2025-11-02     │ 4 days       │ 3 / 11       │ Today              │
└─────────────┴──────────┴────────────────┴──────────────┴──────────────┴────────────────────┘

Legend:
🔴 High Priority (8-10)    - Run check now
🟠 Medium Priority (5-7.9) - Run check soon
🟡 Low Priority (2-4.9)    - Can wait
🟢 Minimal (0-1.9)         - No check needed

Recommendations:
1. Run /code-check-loading (priority: 9.2) - Heavy changes, long time since check
2. Run /code-check-evaluation (priority: 7.8) - Multiple files changed recently
3. Run /code-check-domain (priority: 6.5) - Never checked before

{If >3 high priority (≥8.0):}
⚠️  4+ modules need checking. Consider running /code-check-all to check all modules in parallel.
    This will be faster than running individual checks sequentially.

{If 2-3 high priority:}
💡 Run individual module checks: /code-check-{module1} /code-check-{module2}

{If 0-1 high priority:}
💡 Run the single high-priority check: /code-check-{module}

{If all low priority:}
✅ All modules recently checked with minimal changes. No checks urgently needed.
```

## Efficiency Notes

- Use bash/grep/awk for data extraction (don't read full report files)
- Use git commands for file stats (don't load actual file contents)
- No file I/O beyond metadata
- Fast execution (<2 seconds for all modules)

## When to Use

- **Daily:** Check before starting work to see what needs attention
- **Before commits:** Validate modules you've been working on
- **Pre-release:** Identify any missed quality checks
- **After merges:** See what modules were affected by merged changes
