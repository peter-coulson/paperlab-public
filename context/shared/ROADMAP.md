# Roadmap

> **Project status:** Archived. PaperLab reached professional beta (Milestone 7) before the commercial path was blocked by exam board content licensing. This document captures what was built and what had been planned.

---

## Strategic Vision (as of archive)

Become the primary past paper marking and exam training tool in the UK.

**Scope:** All GCSE and A-Level subjects across all exam boards.

**Value proposition:** Accurate automated marking with working analysis that identifies specific misconceptions (not just right/wrong).

---

## Project Scope

**Subject:** GCSE Maths (Pearson Edexcel only)

**Distribution:** Native mobile app (iOS/Android) via Flutter

**Architecture:** Backend-heavy design. All marking logic in Python backend. Clients are thin display layers.

**Design constraint:** Architecture supports rapid expansion to other subjects/levels without refactors — expansion happens through data and prompts, not code changes.

---

## Completed Milestones

| Milestone | What | Status |
|-----------|------|--------|
| **M1** | E2E single question marking (95%+ accuracy validated) | ✅ Complete |
| **M2** | Testing framework (reproducibility, ground truth, parallel execution) | ✅ Complete |
| **M3** | Cloud infrastructure (R2 storage, presigned URLs, security) | ✅ Complete |
| **M4** | Full paper marking (batch marking, grades, retry workflow) | ✅ Complete |
| **M5** | Flutter prototype (10 screens, mock data, design system) | ✅ Complete |
| **M6** | FastAPI backend + integration (E2E workflow working) | ✅ Complete |
| **M7** | Professional beta (TestFlight distribution, Railway deployment, beta testing infrastructure) | ✅ Complete |
| **M7.5** | Refinement & stabilization (beta feedback incorporated, UX polish, performance work) | ✅ Complete |

---

## Planned Milestones (not implemented)

The following milestones were scoped but never executed. Project was archived before this work began.

### Milestone 8: Accuracy Optimization

- Metrics calculation and analysis
- Model comparison (Claude vs GPT-4o vs Gemini)
- Iterative prompt refinement using expert feedback from M7
- Target: 95%+ accuracy across diverse test cases

### Milestone 9: Production Launch

- Payment integration
- Security hardening
- Scale testing
- R2 custom domain setup (migrate from r2.dev to custom domain for production-grade access, rate limit removal, and security controls)
- LLM response storage migration (SQL → R2 for cost savings at scale)
- Image optimization (HEIC handling, compression, detail-mode tuning, parallel uploads)
- Persistent cache (Hive-based disk cache, stale-while-revalidate, offline mode)
- Public App Store release

### Milestone 10: Insights Engine

- Pattern detection across questions
- Topic/concept breakdown
- "Why you got it wrong" analysis

---

## Planned Expansion (pre-archive)

Expansion was designed to happen through **data and prompts, not code changes**.

### Expansion Order

1. **Exam Board Expansion** — other boards (AQA, OCR) for GCSE Maths
2. **Subject Expansion (GCSE)** — sciences, English, humanities
3. **A-Level Expansion** — starting with A-Level Maths
4. **Platform Expansion** — web application, teacher dashboards
5. **Advanced Features** — recommendations, enterprise accounts, API access

---

## Key Technical Decisions

**Backend:** Python + FastAPI (all business logic server-side)

**Database:** SQLite until 10k+ students

**Deployment:** Railway (backend) + Cloudflare R2 (images) + App Store (mobile)

**See also:** `../backend/ARCHITECTURE.md` for detailed patterns.
