# Landing Page Context

Marketing website for PaperLab user acquisition.

---

## Purpose

The landing page is a standalone marketing site that:
- Communicates the product value proposition
- Drives TestFlight signups (iOS early access)
- Captures email for Android/Web waitlist
- Establishes brand credibility before app download

**Separate from the Flutter app** - This is a Next.js website, not part of the mobile app codebase.

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| **Next.js 16** | React framework with App Router |
| **TypeScript** | Type safety |
| **Tailwind CSS v4** | Utility-first styling with `@theme` syntax |
| **shadcn/ui** | Component primitives (Button, Input, Card) |

**Why Next.js?** Static site generation for fast loading, React ecosystem for component reuse, Tailwind integration matches Flutter app's utility-first approach.

---

## Design System Connection

The landing page shares visual DNA with the Flutter app but adapts for marketing context.

### Shared Elements

| Element | Flutter App | Landing Page |
|---------|-------------|--------------|
| **Primary font** | IBM Plex Serif (headings) | Same |
| **Body font** | IBM Plex Sans | Same |
| **Primary color** | Indigo `#667EEA` | Same |
| **Accent** | Indigo Deep `#4F46E5` | Same |
| **Success** | Emerald `#10B981` | Same |
| **Warning** | Amber `#F59E0B` | Same |
| **Spacing unit** | 4px base | Same |

### Landing-Specific Adaptations

The landing page uses **darker backgrounds** to make app screenshots pop:

- **Deep Slate** `#0F172A` - Hero, How It Works, Footer
- **Slate** `#1E293B` - Card backgrounds on dark sections
- **Warm White** `#FAFAF9` - Light section backgrounds

This "frame and product" approach creates visual contrast where the dark page acts as a stage for the clean white app UI.

---

## Architecture

```
landing/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # Root layout (fonts, metadata)
│   │   ├── page.tsx        # Main page (imports all sections)
│   │   └── globals.css     # Design tokens (@theme block)
│   └── components/
│       ├── ui/             # shadcn components
│       └── sections/       # Page sections
│           ├── Hero.tsx
│           ├── Problem.tsx
│           ├── Solution.tsx
│           ├── HowItWorks.tsx
│           ├── Differentiator.tsx
│           ├── Scope.tsx
│           ├── CTA.tsx
│           └── Footer.tsx
└── public/
    └── images/             # App screenshots
```

### Key Locations

| What | Where |
|------|-------|
| **Design tokens** | `src/app/globals.css` (Tailwind `@theme` block) |
| **Font setup** | `src/app/layout.tsx` (next/font/google) |
| **Page sections** | `src/components/sections/*.tsx` |
| **App screenshots** | `public/images/*.jpeg` |

---

## Source of Truth

| What | Location |
|------|----------|
| **Design tokens** | `landing/src/app/globals.css` |
| **Section content** | `landing/src/components/sections/*.tsx` |
| **Screenshots** | `landing/public/images/` |

Code is authoritative - content and design are implemented directly in components.

---

## Screenshots

Screenshots show the actual Flutter app to demonstrate product value:

| Screenshot | Section | Shows |
|------------|---------|-------|
| `question_plus_results.jpeg` | Hero | Question with LaTeX + results |
| `paper_upload.jpeg` | How It Works (1) | Paper selection |
| `question_upload.jpeg` | How It Works (2) | Photo capture |
| `paper_results.jpeg` | How It Works (3) | Grade summary |
| `mark_results.jpeg` | Solution, Differentiator | Detailed mark breakdown |

---

## Development

```bash
cd landing
npm run dev    # Start dev server (localhost:3000)
npm run build  # Production build
npm run lint   # ESLint check
```

---

## Relationship to Other Docs

- **Brand voice & UX principles** → `context/shared/BRANDING.md`
- **Product mission** → `context/shared/MISSION.md`
- **Flutter design system** → `context/frontend/DESIGN_SYSTEM.md`
