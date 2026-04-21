# Frontend Context

Strategic context for Flutter mobile app architecture, widgets, screens, and UX patterns.

## When to Use This

- **Understanding Flutter architecture** → `ARCHITECTURE.md`
- **Working with navigation** → `NAVIGATION.md`
- **Building reusable widgets** → `WIDGETS.md`
- **Managing state** → `STATE-MANAGEMENT.md`
- **Optimizing performance** → `PERFORMANCE.md`
- **Styling and design** → `DESIGN_SYSTEM.md`
- **Calling backend APIs** → `API-INTEGRATION.md`
- **Parsing API responses** → `MODELS.md`

### Available Documentation

- **ARCHITECTURE.md** ✅ - Flutter structure, layered architecture, module responsibilities (utils/), input validation
- **NAVIGATION.md** ✅ - Screen flow, state-aware navigation, routing patterns
- **WIDGETS.md** ✅ - Widget composition, when to extract utilities, organization patterns
- **STATE-MANAGEMENT.md** ✅ - Riverpod patterns, async state, optimistic updates
- **PERFORMANCE.md** ✅ - Non-blocking async patterns, prefetch strategy, Timeline profiling
- **DESIGN_SYSTEM.md** ✅ - Colors, typography, spacing, timing/text constants
- **API-INTEGRATION.md** ✅ - ApiClient, repository pattern, error handling, OAuth2
- **MODELS.md** ✅ - fromJson factories, state derivation, immutability patterns

## Cross-Cutting Concerns

For shared information across backend and frontend:
- **API contracts** → `../shared/API-CONTRACTS.md` (to be created)
- **JSON format specification** → `../shared/JSON-FORMATS.md`
- **Domain concepts (mark schemes)** → `../shared/DESIGN.md`
- **Product vision and roadmap** → `../shared/VISION.md`

## Principles (CRITICAL - Must Follow)

- **DRY** - One source of truth per piece of information
- **Separation of concerns** - Each file has distinct purpose
- **Assume intelligence** - Self-documenting structure over verbose explanation
- **Minimum required context** - Provide orientation, not exhaustive detail
- **Mobile-first design** - Optimize for mobile UX, adapt for web

## Implementation Guidance

**Looking for detailed specs?** See `specs/` folder at project root, particularly:
- `specs/ui-workflows.md` - Screen specifications and user flows
- `specs/upload-workflow.md` - Photo upload and submission flow

**This folder is for strategic context only.** Implementation details live in:
- `specs/` - Pre-implementation guidance (delete after code exists)
- Frontend source code - Post-implementation (code is truth)

## Deployment

**Production builds (iOS):**
```bash
fvm flutter build ios --release --dart-define=ENVIRONMENT=production
```

**Development (default):**
```bash
fvm flutter run  # Uses localhost backend
```

**Environment selection:** `--dart-define=ENVIRONMENT=production` switches from local to Railway backend. See `lib/config.dart` for environment configuration.

---

## Current Status

See `CURRENT.md` at project root for active sprint tasks and current milestone.
