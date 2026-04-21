You are conducting a **UI Technical Standards Check** for the Flutter codebase.

Think hard about sizing standards, design system consistency, brand alignment, and accessibility - this requires technical analysis of UI implementation against best practices and brand guidelines.

## Objective

Analyze UI implementation for sizing standards, touch target accessibility, design system consistency, brand guideline compliance, color contrast, typography hierarchy, and responsive design patterns.

This is a **code-based technical analysis only**. Do not look at screenshots. Analyze measurements, calculations, and standards from code.

## Scope

**All Flutter/Dart files:** `lib/**/*.dart` (excluding generated files)
**Report location:** `.quality/ui/code-{TIMESTAMP}.md`

## What to Read

**Required:**
- `CLAUDE.md` - Flutter principles
- `context/shared/BRANDING.md` - Brand guidelines (source of truth)
- `context/frontend/DESIGN_SYSTEM.md` - Design philosophy and technical specs
- All Dart files in `lib/` (especially `theme/`, `screens/`, `widgets/`)

**DO NOT read:**
- Screenshots (this is code analysis only)
- Backend context files (not relevant)
- `context/shared/MISSION.md` (not needed for technical standards)
- `context/shared/ROADMAP.md` (not relevant)

## Quality Standards to Check

### 1. Touch Target Sizes (Accessibility)

**Standards:**
- Minimum: 48dp × 48dp (Material Design guideline)
- Recommended: 48-56dp for primary actions
- Icons: 24dp standard, 48dp touch area
- Small targets (< 44dp) are accessibility violations

**Check:**
- Button heights
- IconButton sizes and padding
- ListItem/Card tap areas
- Custom tappable widgets

**Look for violations:**
- Buttons < 48dp tall
- IconButton without sufficient padding
- Tappable areas too small
- Custom GestureDetector targets < 44dp

### 2. Typography Standards

**Check:**
- Font sizes follow hierarchy (h1 > h2 > h3 > body > caption)
- Body text ≥ 14sp (12sp absolute minimum)
- Line heights appropriate (1.2-1.8x font size)
- Letter spacing used correctly
- Font weight hierarchy logical

**Standards:**
- Body text: 14-16sp
- Small text: minimum 12sp
- Headers: Progressive scale (e.g., 12, 14, 16, 20, 24, 32)
- Line height: 1.4-1.5 for body, 1.2-1.3 for headers

### 3. Color Contrast Ratios (WCAG)

**Standards (WCAG 2.1):**
- AA (minimum): 4.5:1 for normal text, 3:1 for large text (≥18pt)
- AAA (enhanced): 7:1 for normal text, 4.5:1 for large text
- UI components: 3:1 minimum

**Check:**
- Text on backgrounds (primary, secondary, disabled)
- Button text on button background
- Icon colors on backgrounds
- Border colors for visibility

**Calculate contrast ratios** for key combinations from hex values in AppColors.

### 4. Spacing System Consistency

**Check:**
- Spacing follows consistent scale (e.g., 4, 8, 12, 16, 24, 32, 40, 48)
- No arbitrary values (e.g., 13px, 17px, 23px)
- Padding/margin use theme constants
- Vertical rhythm maintained

**Reference:** AppSpacing constants - verify they follow proper scale.

### 5. Design System Adherence

**Check:**
- All colors from AppColors (no Color(0xFF...) in widgets)
- All typography from AppTypography
- All spacing from AppSpacing
- Consistent component usage

**Violations:**
- Hardcoded colors in widgets
- Inline TextStyle instead of theme
- Hardcoded padding/margin values
- Duplicated component logic

### 6. Brand Alignment

**Read context files and check:**
- Color palette matches brand (from BRANDING.md)
- Typography matches brand voice (from DESIGN_SYSTEM.md)
- Spacing density matches brand personality
- Component style matches brand aesthetic
- Design philosophy reflected in code

**DO NOT invent brand guidelines** - only reference what exists in context files.

### 7. Responsive Design

**Check:**
- No fixed widths without maxWidth constraints
- Use of MediaQuery where needed
- Flexible layouts (Flexible, Expanded, LayoutBuilder)
- SafeArea for notched devices

### 8. Icon Sizing Standards

**Check:**
- Icon sizes consistent (16, 20, 24, 32, 40, 48)
- IconButton touch area ≥ 48dp
- Icon visual weight matches context

### 9. Cross-Screen Consistency (Code Level)

**Check across all screens and widgets:**
- **Colors:** Same semantic colors used consistently (textPrimary, textSecondary, etc.)
- **Typography:** Same text styles for same purposes (h3 for titles, body for content, etc.)
- **Spacing:** Same spacing scale used everywhere (AppSpacing.md, lg, xl, etc.)
- **Component sizes:** Similar components have identical dimensions
- **Border radius:** Consistent corner rounding across cards, buttons, containers
- **Elevation/shadows:** Consistent depth hierarchy

**Look for violations:**
- Same element type using different colors (e.g., one screen uses textPrimary, another uses custom gray)
- Same element type using different font sizes (e.g., screen titles at h2 in one screen, h3 in another)
- Same element type using different spacing (e.g., section spacing 24px in one screen, 32px in another)
- Button heights varying across screens without justification
- Border radius inconsistent (8px in some places, 12px in others)
- Component patterns duplicated with slight variations instead of reused

**Analyze:**
- `lib/screens/` - Do all screens use theme consistently?
- `lib/widgets/` - Are reusable components actually reused?
- Compare implementations across files for consistency

### 10. Premium Polish Standards (Code)

**Check implementation details that signal quality:**

**Shadow & elevation system:**
- Multi-layer shadows (not single harsh shadow)?
- Elevation values follow consistent scale (2, 4, 8, 16)?
- Shadow colors use transparency (not pure black)?
- Elevation used purposefully (cards > background)?

**Border radius consistency:**
- All components use same radius scale (4, 8, 12, 16)?
- Radius appropriate for component size (larger components = larger radius)?
- No mixed radius values (some 8px, some 10px)?

**Animation standards (if present):**
- Duration follows standards (150-300ms UI, 200-400ms page)?
- Easing curves use Material curves (not linear)?
- Curves: cubic-bezier(0.4, 0.0, 0.2, 1) for standard, fastOutSlowIn for emphasis?
- No instant state changes (always transition)?

**State management (visible in code):**
- Loading states implemented (not just empty while loading)?
- Error states implemented (not just crash)?
- Empty states implemented (not just blank)?
- Disabled states have proper visual treatment?
- Pressed/active states defined?

**Interaction feedback:**
- InkWell/Material for tap ripple effects?
- Proper splash color defined (not default)?
- Touch feedback on all tappable elements?

**Typography refinement:**
- Letter spacing defined (not default 0)?
- Line height specified (not default)?
- Font weights span range (not just 400/700)?
- Optical sizing considerations?

**Color sophistication:**
- Using semantic color names (not color names)?
- Neutral grays have slight warmth (not pure gray)?
- Colors work in light/dark mode (if applicable)?
- Accent color used sparingly for emphasis?

**Component-level polish:**
- All components have proper constraints?
- ClipBehavior set appropriately (antiAlias for rounded)?
- Proper use of Material/Ink for layering?
- Shadow painters or elevation used (not borders for depth)?

**Look for code patterns that indicate premium quality:**
- Custom curves defined for brand motion
- Multi-layer Container widgets for depth
- Proper use of Theme.of(context) for consistency
- Custom ShapeBorder implementations for unique shapes
- Opacity widgets for layering (not just solid colors)

**Look for patterns that indicate rough implementation:**
- Hard-coded colors instead of theme
- No animation curves defined
- Single-layer shadows
- No state variants (loading, error, empty)
- No touch feedback on tappables
- Default Material Design without customization

### 11. Component Consistency

**Check:**
- Similar components have same sizes
- Button heights consistent
- Card/ListItem heights consistent
- Border radius consistent
- Elevation/shadow consistent

## Analysis Process

1. **Read context files** (BRANDING.md, DESIGN_SYSTEM.md)
2. **Read theme files** (AppColors, AppTypography, AppSpacing)
3. **Read all widget and screen files**
4. **Measure and calculate:**
   - Touch target sizes
   - Font size hierarchy
   - Color contrast ratios (from hex values)
   - Spacing scale consistency
   - Icon sizes
5. **Compare against standards** (Material Design, WCAG, brand from context)
6. **Identify violations** by severity
7. **Generate report** with specific measurements

## Output Format

Generate report at `.quality/ui/code-{TIMESTAMP}.md`

Use format: `YYYY-MM-DD-HHMMSS` for timestamp

### Report Structure

```markdown
# UI Technical Standards Check
**Run:** {TIMESTAMP}
**Commit:** {git hash}
**Files Analyzed:** {count} Dart files
**Brand Guidelines:** {context files read}
**Status:** {✅ All Clear | ⚠️ Issues Found | ❌ Critical Issues}

## Summary
- Touch target compliance: {percentage}%
- Typography standards: {percentage}%
- Color contrast (WCAG AA): {percentage}%
- Design system adherence: {percentage}%
- Brand alignment: {percentage}%
- Responsive design: {percentage}%
- **Overall UI Technical Score: {percentage}%**

## 🔴 Critical Issues [MUST FIX]

{List critical issues with file:line, measurements, fixes}

## 🟡 Warnings [SHOULD FIX SOON]

{List warnings with measurements and fixes}

## 🔵 Info [CONSIDER]

{List suggestions}

## Detailed Analysis by Category

### ✅/⚠️/❌ Touch Target Sizes

**Metrics:**
- Components checked: {count}
- Minimum size found: {dp}
- Targets < 48dp: {count}
- Touch target compliance: {percentage}%

**Touch target inventory:**

| Component | Size | Location | Status |
|-----------|------|----------|--------|
| {component} | {height}dp | {file:line} | {✅/⚠️/❌} |

**Issues:** {list violations}

### ✅/⚠️/❌ Typography Standards

**Typography scale:**

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| {style} | {size}sp | {weight} | {height} | {usage} |

**Hierarchy validation:**
- ✅/⚠️ Progressive scale
- ✅/⚠️ Clear visual distinction
- ✅/⚠️ Readability (body ≥ 14sp)

**Issues:** {list violations}

### ✅/⚠️/❌ Color Contrast Ratios

**Contrast ratio measurements:**

| Foreground | Background | Ratio | WCAG AA | WCAG AAA |
|------------|------------|-------|---------|----------|
| {color} ({hex}) | {color} ({hex}) | {ratio}:1 | {✅/❌} | {✅/❌} |

**Issues:** {list WCAG failures}

### ✅/⚠️/❌ Spacing System

**Spacing scale:**

| Name | Value | Multiplier | Usage |
|------|-------|------------|-------|
| {name} | {px} | {x}× | {usage} |

**Scale validation:**
- Base unit: {4px/8px}
- ✅/⚠️ All values multiples of base
- ✅/⚠️ Progressive scale

**Issues:** {list arbitrary spacing}

### ✅/⚠️/❌ Design System Adherence

**Metrics:**
- Hardcoded colors: {count}
- Inline TextStyles: {count}
- Magic number spacing: {count}
- Design system usage: {percentage}%

**Issues:** {list violations}

### ✅/⚠️/❌ Brand Alignment

**Brand Guidelines (from context):**
{Summarize BRANDING.md and DESIGN_SYSTEM.md}

**Implementation vs Brand:**

| Guideline | Implementation | Match |
|-----------|----------------|-------|
| {guideline} | {implementation} | {✅/⚠️/❌} |

**Issues:** {list misalignments}

### ✅/⚠️/❌ Responsive Design

**Metrics:**
- Fixed widths without constraints: {count}
- SafeArea usage: {✅/⚠️}
- Flexible layouts: {percentage}%

**Issues:** {list violations}

### ✅/⚠️/❌ Icon Sizing

**Icon inventory:**

| Icon | Visual Size | Touch Area | Location | Status |
|------|-------------|------------|----------|--------|
| {icon} | {dp} | {dp} | {file:line} | {✅/⚠️/❌} |

**Issues:** {list non-standard sizes}

### ✅/⚠️/❌ Cross-Screen Consistency (Code)

**Metrics:**
- Screens analyzed: {count}
- Color usage consistency: {percentage}%
- Typography consistency: {percentage}%
- Spacing consistency: {percentage}%
- Component reuse: {percentage}%

**Assessment:** {Overall assessment}

**Consistency analysis:**

| Element Type | Screen 1 | Screen 2 | Screen 3 | Consistent? |
|--------------|----------|----------|----------|-------------|
| Page title | h2, textPrimary | h3, textPrimary | h2, textPrimary | ⚠️ Size varies |
| Section spacing | AppSpacing.lg | AppSpacing.xl | AppSpacing.lg | ⚠️ Mixed |
| Button height | 48dp | 48dp | 52dp | ⚠️ Inconsistent |
| Border radius | 8px | 8px | 8px | ✅ Consistent |

**Color usage across screens:**
- textPrimary: Used in {X} screens ✅
- textSecondary: Used in {Y} screens ✅
- Custom colors: Found in {Z} locations ⚠️

**Typography usage across screens:**
- h1: Used for {purpose} in {X} screens
- h2: Used for {purpose} in {Y} screens
- h3: Used for {purpose} in {Z} screens
- Inconsistencies: {list any}

**Spacing usage across screens:**
- Section spacing: {list values used and where}
- Card spacing: {list values used and where}
- Content padding: {list values used and where}
- Inconsistencies: {list any}

**Component reuse:**
- Reused components: {list components used across multiple screens}
- Duplicated patterns: {list similar code not extracted to components}
- Opportunities: {suggest where components could be extracted}

**Issues:** {list cross-screen inconsistencies}

### ✅/⚠️/❌ Premium Polish Standards (Code)

**Metrics:**
- Shadow/elevation system: {✅ Multi-layer | ⚠️ Single-layer | ❌ None}
- Animation standards: {✅ Defined | ⚠️ Basic | ❌ None}
- State coverage: {percentage}% (loading, error, empty, disabled)
- Interaction feedback: {percentage}% tappables have ripple
- Typography refinement: {✅ Custom spacing/height | ⚠️ Defaults}
- Premium polish score: {percentage}%

**Assessment:** {Overall assessment of implementation sophistication}

**Premium patterns found:**
- ✅/❌ Multi-layer shadows for depth
- ✅/❌ Custom animation curves
- ✅/❌ InkWell/Material for feedback
- ✅/❌ Loading/error/empty states
- ✅/❌ Letter spacing refinement
- ✅/❌ Semantic color system

**Rough implementation patterns:**
- {List any indicators of unpolished code}

**What would make this "OpenAI/Claude quality" (code level):**
1. {Specific code improvements}
2. {Animation/interaction additions}
3. {State management enhancements}

### ✅/⚠️/❌ Component Consistency

**Component inventory:**
- Buttons: {list types and sizes}
- Cards/Lists: {list types and sizes}

**Consistency check:**
- ✅/⚠️ Similar components same sizes
- ✅/⚠️ Border radius consistent
- ✅/⚠️ Elevation consistent

**Issues:** {list inconsistencies}

## Accessibility Summary

**WCAG Compliance:**
- Level AA: {pass/fail} ({percentage}%)
- Level AAA: {pass/fail} ({percentage}%)

**Critical accessibility issues:** {count}
- Touch targets < 48dp: {count}
- Color contrast failures: {count}
- Text size violations: {count}

## Brand Compliance Summary

**Brand guideline adherence:** {percentage}%

**Strengths:** {list what matches brand well}
**Gaps:** {list where brand could be stronger}

## Refactoring Recommendations

### High Priority (Accessibility/Brand Critical)
1. **{Issue}** - {file:line} - {fix} - {effort}

### Medium Priority (Best Practices)
1. **{Issue}** - {file:line} - {fix} - {effort}

### Low Priority (Polish)
1. **{Issue}** - {file:line} - {fix} - {effort}

## Next Steps

{If critical issues:}
⚠️ **Action Required:** Fix {X} accessibility violations and {Y} brand misalignments.

{If warnings only:}
✅ Technical standards are solid. Address {Y} warnings for better compliance.

{If all clear:}
✅ Excellent technical implementation! Meets accessibility and brand standards.

---
*This analyzed code-based technical standards only.*
*For visual design review (hierarchy, aesthetics, balance), run /ui-check-visual*
```

## Chat Output

```
{✅ | ⚠️ | ❌} UI Technical Standards Check Complete

📄 Report: .quality/ui/code-{TIMESTAMP}.md
Technical Score: {percentage}%

{If critical:}
🔴 Critical: {count}
- Accessibility violations: {count}
- Brand misalignments: {count}

{If warnings:}
🟡 Warnings: {count}

Scores:
- Touch targets: {percentage}%
- Typography: {percentage}%
- Color contrast: {percentage}%
- Design system: {percentage}%
- Brand alignment: {percentage}%

{Top recommendations}

---
📸 Next: Run /ui-check-visual for visual design review
(hierarchy, aesthetics, balance, user experience)
```

## Important Notes

- **Code analysis only** - Never look at screenshots
- **Context files are source of truth** - Don't invent brand guidelines
- **Calculate real metrics** - Contrast ratios, sizes, scales
- **Be specific** - Always file:line references
- **Material + WCAG standards** - 48dp touch, 4.5:1 contrast
- **After report** - Suggest /ui-check-visual for comprehensive review
