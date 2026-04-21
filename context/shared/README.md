# Shared Context

Strategic context shared across backend and frontend systems.

## When to Use This

- **Understanding product mission and values** → `MISSION.md`
- **Understanding roadmap and strategy** → `ROADMAP.md`
- **Understanding domain concepts** → `DESIGN.md`
- **JSON format specification** → `JSON-FORMATS.md`
- **Brand identity and UX principles** → `BRANDING.md`

## What Lives Here

**Product Strategy**
- `MISSION.md` - Why we exist, core values, who we serve
- `ROADMAP.md` - Strategic goal, milestones (M1-M10), go-to-market strategy
- `BRANDING.md` - Brand identity, UX principles, visual direction

**Domain Model**
- `DESIGN.md` - Question-level marking, GCSE mark scheme structure, display mapping
- `JSON-FORMATS.md` - JSON input format specification, key patterns, design rationale

**Integration Points**
- API contracts are defined in `../api/PATTERNS.md` and `../api/WORKFLOWS.md`

## What Doesn't Live Here

**Backend-specific concerns** → `../backend/`
- Python architecture, CLI, database, repositories, validation layers

**Frontend-specific concerns** → `../frontend/`
- Flutter patterns, widgets, screens, navigation, state management

## Principles

- **Single source of truth** - If both backend and frontend need it, it lives here
- **No duplication** - Backend and frontend docs should reference shared docs, not duplicate them
- **Domain-focused** - Emphasize business concepts, not technical implementation
- **Platform-agnostic** - Describe what, not how (how lives in backend/ or frontend/)

## Maintaining This System

**Before adding documentation here:**
1. Ask: "Does this apply to both backend and frontend?"
   - Yes → Belongs in `shared/`
   - No → Belongs in `backend/` or `frontend/`

2. Ask: "Is this domain knowledge or implementation detail?"
   - Domain knowledge → Belongs in `shared/`
   - Implementation detail → Belongs in `backend/` or `frontend/`

**Examples:**
- ✅ "Mark schemes have types: M (method), A (accuracy), B (reasoning)" → `shared/DESIGN.md`
- ✅ "Papers are identified by board/qualification/level/subject/code" → `shared/DESIGN.md`
- ❌ "Mark schemes are stored in the `mark_types` table" → `backend/DATABASE.md`
- ❌ "Mark schemes are displayed as badges in the UI" → `frontend/COMPONENTS.md`
