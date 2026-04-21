# Context System Governance

Complete governance for PaperLab strategic context documentation.

---

## Principles (CRITICAL - Must Follow)

### Context System Principles

- **DRY** - One source of truth per piece of information
- **Separation of concerns** - Backend, API, frontend, and shared docs are isolated
- **Assume intelligence** - Self-documenting structure over verbose explanation
- **Minimum required context** - Provide orientation, not exhaustive detail

### Content Principles

**Golden Rule:** Document WHY and WHERE, not WHAT and HOW

**Context should document:**
- Architecture decisions and rationale (WHY we built this way)
- Design patterns to follow (WHERE to look for examples)
- Domain concepts not evident from code
- Project standards and conventions
- Navigation (WHERE to find things)

**Context should NOT duplicate:**
- CLI command usage (use `--help`)
- Schema field definitions (see `data/db/schema.sql` or Pydantic models)
- API reference (see official docs)
- Complete code examples (see actual files in repo)
- Implementation tutorials (code shows HOW)
- Step-by-step numbered instructions
- Field-by-field schema walkthroughs
- SQL query examples and seed data listings
- Alternative patterns considered and rejected
- Complete class/function definitions (show pattern only)

**Code examples:**
- Maximum 5-10 lines to illustrate a principle
- NOT complete implementations (30-50 line classes, widgets, etc.)
- ALWAYS include pointer to actual file for full implementation (e.g., "See `cli/commands/load.py`")

**Exemplar files** (show right level of detail):
- `backend/DATABASE.md` - Database patterns (connection mgmt, transactions)
- `api/README.md` - API patterns (from_domain, validation layers)

**Exceptions to WHY/WHERE rule:**

Brand identity documentation (`shared/BRANDING.md`) requires reference material that doesn't fit elsewhere:
- Bundle IDs, domain names, social handles (operational reference for team)
- Usage guidelines across channels (app stores, marketing, social media)
- This is inherently "WHAT" but essential for consistent brand execution
- **Rationale:** Brand identity is atomic - can't be derived from code or split into separate files
- **Guideline:** Keep concise but complete; team needs single source of truth for brand assets

---

## Size Targets

### Domain Budgets

| Domain | Target Range |
|--------|--------------|
| Backend | 3,000-5,500 lines |
| Frontend | 2,000-3,500 lines |
| API | 1,500-2,500 lines |
| Shared | 1,000-1,500 lines |
| **TOTAL** | **7,500-13,000 lines** |

**Rationale:** Dual-stack project (Python backend + Flutter frontend) with API layer requires more context than single-stack. Backend is most complex (domain logic, LLM integration, evaluation). API is thin transport layer (FastAPI patterns, auth, deployment). Frontend is UI-focused (widgets, screens, state). Shared is product strategy and domain concepts.

### Per-File Limits

| Threshold | Action |
|-----------|--------|
| < 350 lines | Good |
| 350-400 lines | Monitor for growth |
| 400-450 lines | Consider trimming |
| > 450 lines | **MUST trim or split** |

**Hard rule:** No file should exceed 450 lines. If file grows past 450, it must be trimmed or split before merging.

### Context-to-Code Ratios

| Domain | Target Ratio |
|--------|--------------|
| Backend | 20-30% |
| Frontend | 20-30% |

**Definition:** Context-to-Code Ratio = (context lines / code LOC) × 100

**Why it matters:** Ratios >35% indicate over-documentation (reference/tutorial content instead of strategic decisions).

### Code Block Ratios

| Ratio | Assessment |
|-------|------------|
| 0-25% | Good (strategic content) |
| 25-40% | Mixed (some reference creeping in) |
| > 40% | Too much (reference/tutorial pattern) |

**High code block ratios** indicate file has become a reference manual or tutorial instead of strategic documentation.

---

## Maintaining the Context System

### Before Adding/Modifying Documentation

**1. Determine ownership:**
- Backend-only concern → `backend/`
- API-only concern → `api/`
- Frontend-only concern → `frontend/`
- Product strategy/domain → `shared/`

**2. Check for duplicates:**
- Each piece of information should exist in exactly ONE place
- Backend and frontend docs should reference `shared/` docs, not duplicate them

**3. Keep it high-level:**
- Strategic context belongs here
- Implementation details belong in `specs/` or code

**4. Follow size standards:**
- Keep files under 450 lines
- Document WHY/WHERE, not WHAT/HOW
- Point to actual files for implementation details

### Examples of Correct Placement

**✅ Good examples:**
- "Papers are identified by board/qualification/level/subject/code" → `shared/DESIGN.md`
- "Mark schemes are stored in the `mark_types` table" → `backend/DATABASE.md`
- "API endpoints use from_domain() pattern" → `api/README.md`
- "Mark scheme badges use primary color for M marks" → `frontend/STYLING.md`

**❌ Bad examples:**
- Duplicating JSON format spec in backend, API, and frontend docs
- Complete endpoint implementations in context (see `specs/m6/` instead)
- Complete DDL field listings in context (see `schema.sql` instead)

---

## Maintenance Schedule

**Monthly health checks:**
- Run context health assessment to track metrics and identify issues
- Review files approaching 450 line limit
- Check context-to-code ratios
- Identify duplication across domains

**On PR review:**
- Reject files >450 lines without explicit justification and trimming plan
- Verify ownership (correct domain folder)
- Check for duplicates across context system

**On milestone completion:**
- Prune historical details
- Remove implementation tutorials
- Trim examples to principles
- Update navigation in README.md
