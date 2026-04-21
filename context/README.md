# Context System

Entry point for strategic context across backend, API, frontend, and shared systems.

---

## Quick Navigation

### Working on Backend?
→ **[`backend/README.md`](backend/README.md)** - Python architecture, CLI, database, domain logic

### Working on API?
→ **[`api/README.md`](api/README.md)** - FastAPI layer, endpoints, authentication, deployment

### Working on Frontend?
→ **[`frontend/README.md`](frontend/README.md)** - Flutter mobile app, widgets, screens, UX

### Need Shared Information?
→ **[`shared/README.md`](shared/README.md)** - Product vision, domain concepts, data formats

### Working on Landing Page?
→ **[`landing/README.md`](landing/README.md)** - Next.js marketing site, design system, sections

---

## When to Use This

**Understanding product strategy:**
- Product vision and roadmap → `shared/ROADMAP.md`
- Domain concepts (mark schemes) → `shared/DESIGN.md`

**Working on backend (Python):**
- Backend architecture → `backend/ARCHITECTURE.md`
- CLI structure → `backend/CLI.md`
- Database patterns → `backend/DATABASE.md`
- Data ingestion → `backend/DATA-LOADING.md`
- Marking pipeline → `backend/MARKING.md`
- Full paper workflow → `backend/PAPER-MARKING.md`
- Evaluation system → `backend/EVALUATION.md`
- [See full list →](backend/README.md)

**Working on API (FastAPI):**
- API patterns and design → `api/README.md` ✅
- Authentication (M7) → `api/AUTHENTICATION.md` (future)

**Working on frontend (Flutter):**
- Frontend architecture → `frontend/ARCHITECTURE.md` ✅
- Navigation patterns → `frontend/NAVIGATION.md` ✅
- Widget composition → `frontend/WIDGETS.md` ✅
- State management → `frontend/STATE-MANAGEMENT.md` ✅
- Design system → `frontend/DESIGN_SYSTEM.md` ✅
- [See full list →](frontend/README.md)

**Product strategy and domain:**
- JSON format specification → `shared/JSON-FORMATS.md`
- Product roadmap → `shared/ROADMAP.md`
- Domain concepts → `shared/DESIGN.md`

---

## Structure

```
context/
├── README.md              # This file (entry point and router)
├── GOVERNANCE.md          # Principles, size standards, maintenance
├── backend/               # Python backend context
│   ├── README.md         # Backend-specific index
│   ├── ARCHITECTURE.md   # Layered architecture, patterns
│   ├── CLI.md            # Command-line interface
│   ├── DATABASE.md       # SQLite, connection management
│   ├── MARKING.md        # Question marking pipeline
│   └── ...               # (17 docs total)
├── api/                   # FastAPI layer context
│   └── README.md         # API patterns, design, authentication
├── frontend/             # Flutter frontend context
│   ├── README.md         # Frontend-specific index
│   ├── ARCHITECTURE.md   # Flutter structure, layered architecture
│   ├── NAVIGATION.md     # Screen flow, navigation patterns
│   ├── WIDGETS.md        # Widget composition patterns
│   ├── STATE-MANAGEMENT.md # M6 Provider, M5 approach
│   └── DESIGN_SYSTEM.md  # Visual design (colors, typography)
├── shared/               # Cross-cutting context
│   ├── README.md         # Shared context index
│   ├── ROADMAP.md        # Product strategy, milestones
│   ├── MISSION.md        # Product identity, values
│   ├── BRANDING.md       # Communication style
│   ├── DESIGN.md         # Domain concepts
│   └── JSON-FORMATS.md   # Data format specification
└── landing/              # Marketing website context
    └── README.md         # Landing page architecture, design system
```

---

## Implementation Guidance

**Looking for detailed specs?** See `specs/` folder at project root.

**This folder is for strategic context only.** Implementation details (class structures, method signatures, validation rules) live in:
- `specs/` - Pre-implementation guidance (delete after code exists)
- `src/` - Post-implementation (code is truth)

---

## Contributing to Context

**Before adding/modifying context documentation:**

👉 **Read [`GOVERNANCE.md`](GOVERNANCE.md)** for complete governance, principles, size standards, and maintenance guidelines.

**Quick reference:**
- **Total target:** 7,500-13,000 lines
- **Per-file limit:** <450 lines (hard rule)
- **Content principle:** Document WHY/WHERE, not WHAT/HOW
- **Ownership:** Backend → `backend/`, API → `api/`, Frontend → `frontend/`, Product/domain → `shared/`
