# FINAL CHECK — Editorial Precision Visual System v2

**Status:** USER-DIRECTION APPROVED / SPEC REVIEW REQUIRED  
**Date:** 2026-09-13  
**Branch baseline:** `ui-redesign@a0f9f99c81674ff988d78093e7e6d048afaf781d` before this spec commit  
**Scope:** Visual system refinement only — color, typography, spacing, radius, borders, elevation, density, and cross-screen visual consistency  
**Product semantics:** unchanged  
**Design direction:** Editorial Minimal × Evidence-first Product UI

## 1. Goal

Refine FINAL CHECK from a conventional SaaS dashboard aesthetic into a quieter, more editorial product interface.

The target feeling is:

- almost monochrome at rest;
- typography and whitespace create hierarchy before color does;
- large, confident editorial headings on landing;
- restrained product UI inside the app;
- evidence is organized by alignment and rules, not by stacked colored cards;
- blue is scarce and therefore meaningful;
- status colors communicate BLOCKER / REVIEW / PASS / EXTERNAL without coloring whole surfaces;
- every visible typography, spacing, radius, and border value belongs to an approved integer-pixel token scale.

The visual reference supplied by the user is the primary mood reference: white canvas, strong black typography, generous whitespace, minimal chrome, precise alignment, very limited decorative color.

## 2. External reference principles

Use references for principles, not visual cloning.

### Linear

Borrow:

- quiet surfaces;
- strong information hierarchy;
- de-emphasized secondary UI;
- low visual noise;
- restrained saturation.

Do not borrow:

- issue-tracker-specific chrome;
- purple/blue saturation as a default screen atmosphere.

### Vercel Geist

Borrow:

- role-based color architecture;
- background / component / border / text hierarchy;
- monochrome-first product styling;
- disciplined grid and typography.

Do not borrow:

- black developer-tool branding as a product identity.

### GitHub Primer

Borrow:

- evidence/review information density;
- source-context traceability;
- border and divider use for dense review interfaces;
- responsive product-interface discipline.

### Stripe

Borrow:

- status color restraint;
- accessible semantic colors;
- role-based tokens rather than arbitrary decorative colors.

### Atlassian Design System

Borrow:

- bounded spacing and typography scales;
- token-as-source-of-truth discipline;
- integer-pixel visual tokens;
- accessibility-aware type hierarchy.

## 3. Design principle: structure through type and whitespace

The previous redesign still relies too much on familiar SaaS card grammar: rounded cards, tinted surfaces, soft blue backgrounds, and multiple small labels.

Editorial Precision reverses the hierarchy:

1. typography;
2. whitespace;
3. alignment/grid;
4. hairline borders;
5. color;
6. elevation.

Color and shadow are the last tools, not the first.

## 4. Color system

### 4.1 Neutral foundation

```css
--page: #FFFFFF;
--surface: #FFFFFF;
--surface-subtle: #FAFAF9;

--text-primary: #0A0A0A;
--text-secondary: #525252;
--text-muted: #737373;
--text-faint: #A3A3A3;

--border-subtle: #E5E5E5;
--border-strong: #D4D4D4;
```

Rules:

- `--page` is the default page background.
- `--surface-subtle` is optional and must be used sparingly for hover, selected background, or secondary utility areas.
- `--text-faint` is decorative/inactive only; do not use it for critical body copy.
- avoid blue-gray page backgrounds.
- avoid full-width tinted section backgrounds unless needed for a specific interaction state.

### 4.2 Brand/action accent

```css
--accent: #3157FF;
--accent-hover: #2447E6;
--accent-soft: #F4F6FF;
```

Blue may appear only in:

- primary CTA;
- active workflow step;
- focus ring;
- selected evidence relationship;
- source/evidence trace;
- selected control/tab when stronger indication is needed;
- brand scan-check mark.

Blue must not be used as general decoration or page atmosphere.

### 4.3 Semantic status colors

```css
--status-blocker: #C62828;
--status-blocker-soft: #FFF6F5;

--status-review: #A15C00;
--status-review-soft: #FFF9EB;

--status-pass: #17824B;
--status-pass-soft: #F0FBF5;

--status-external: #737373;
--status-external-soft: #F5F5F5;
```

Rules:

- status text/chip/marker may use semantic color;
- do not fill entire result cards with semantic backgrounds;
- status soft colors are limited to compact chips, micro-highlights, or exceptional warning regions;
- Electric/brand blue never means PASS.

## 5. Typography system

### 5.1 Font family

Primary:

```css
font-family: "Pretendard", "Noto Sans KR", "Malgun Gothic", sans-serif;
```

Technical metadata only:

```css
font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
```

Monospace is restricted to IDs, hashes, locators, measured facts, and technical provenance.

### 5.2 Approved type tokens

Every visible product text size must use one of these integer-pixel tokens:

| Token | Font size | Line height | Primary use |
| --- | ---: | ---: | --- |
| `display-lg` | 56px | 64px | landing hero on wide desktop |
| `display-md` | 48px | 56px | landing hero on smaller desktop/tablet |
| `heading-1` | 40px | 48px | major marketing/page headline |
| `heading-2` | 32px | 40px | page/section title |
| `heading-3` | 24px | 32px | major component heading |
| `heading-4` | 20px | 28px | compact panel heading |
| `body-lg` | 16px | 24px | important descriptive text |
| `body` | 14px | 20px | default application text |
| `small` | 12px | 16px | secondary metadata |
| `micro` | 11px | 16px | IDs/technical tertiary labels only |

Prohibited production sizes include arbitrary values such as `13px`, `15px`, `17px`, `22px`, `23px`, `27px`, and similar one-off values unless this spec is formally amended.

### 5.3 Font weights

Approved weights:

- 400 regular;
- 500 medium;
- 600 semibold;
- 700 bold.

Do not use 650, 800, 900, or arbitrary intermediate weights.

### 5.4 Letter spacing

Approved visible letter-spacing tokens:

- `0px` default;
- `-1px` large display headings only;
- `1px` micro uppercase/technical label only.

Do not use fractional letter spacing such as `.3px`, `.4px`, `.6px`, `1.2px`, or `1.5px`.

## 6. Spacing system

Every visible `margin`, `padding`, `gap`, `inset`, `scroll-margin`, and fixed layout spacing must use one of:

```text
4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 80 / 96 / 120 px
```

Exceptions:

- `0px` is always allowed;
- layout calculations may use `%`, `fr`, `vw`, `vh`, `min()`, `max()`, `clamp()`, and `calc()` when not representing a visual spacing token;
- positioning needed for icon geometry may use integers outside the spacing scale only when isolated inside the icon itself and documented.

Avoid `5px`, `6px`, `9px`, `10px`, `13px`, `18px`, `20px`, `22px`, `25px`, `28px`, `33px`, `34px`, `35px`, `52px`, etc. in normal visual spacing.

## 7. Radius and border system

### Radius

Approved:

```text
0 / 4 / 8 / 12 px
```

Guidance:

- rows, tables, large editorial frames: `0px` or `4px`;
- buttons/inputs/chips: `4px`;
- compact inspector/panel: `8px`;
- exceptional large overlay shell: `12px` max.

Avoid the previous pattern of 14–16px rounding across most surfaces.

### Borders

Approved:

```text
1 / 2 / 3 px
```

Default surface separation is `1px`.

Use `2px` for focus/active emphasis where needed.

Use `3px` only for semantic leading markers or clearly intentional evidence markers.

## 8. Elevation

Default product surfaces have no shadow.

Allowed shadows:

- Evidence Inspector drawer;
- modal/overlay if one exists;
- exceptional floating control only.

Do not use card shadows simply to separate ordinary content.

Prefer whitespace and `1px` borders.

## 9. Landing page

### 9.1 Header

Use an editorial header:

- left: FINAL CHECK mark + wordmark;
- center: small navigation;
- right: one compact CTA;
- white background;
- no filled header container;
- no decorative pills.

Navigation uses `14/20` or `12/16` tokens.

### 9.2 Hero

The hero should resemble an editorial cover more than a SaaS dashboard.

- large black headline;
- large empty space around it;
- supporting copy is gray and narrow;
- primary action appears after sufficient whitespace;
- blue is limited to CTA/focus/brand mark;
- no gradient;
- no blue background glow;
- no rotated frames;
- no decorative dashboard badges surrounding the hero.

Wide desktop:

- `display-lg` 56/64;
- hero vertical padding 80–120px from the approved spacing scale;
- body copy `body-lg` 16/24.

### 9.3 Product proof

The product proof is a clean evidence preview, not a card collage.

Use:

- white surface;
- 1px border where necessary;
- 0–8px radius;
- no generic shadow;
- status expressed as small text/chip;
- RULE / EVIDENCE / VERDICT aligned as a precise grid.

## 10. App shell

Keep the five-step information architecture unchanged:

`공고 → 요구사항 검토 → 제출파일 → 결과 → 재검사`

Visual treatment:

- thin text stepper;
- active step indicated with blue text + minimal underline;
- completed steps use black/gray plus optional check;
- future steps use muted gray;
- no filled segment backgrounds by default;
- no round step bubbles unless reduced to a purely typographic marker.

## 11. Announcement Extraction

The Split Extraction Workspace remains.

Refinement:

- left and right regions should feel like editorial columns rather than rounded cards;
- use a vertical divider or independent whitespace before using boxes;
- selected source evidence uses subtle `accent-soft` or a thin blue rule;
- provisional status remains text-first;
- `AI EXTRACTED` must not become a prominent blue badge dominating the rule.

## 12. Human Review

Keep the existing list + inspector architecture.

Refinement:

- compact list rows separated by 1px rules;
- selected row uses a minimal blue edge/underline, not a large tinted card;
- inspector is mostly white with typographic grouping;
- form controls use 1px borders and 4px radius;
- approval button may use blue;
- edit/secondary actions remain monochrome;
- delete remains semantic danger text.

The hierarchy must continue to communicate:

`AI EXTRACTED → SOURCE EVIDENCE → HUMAN CONFIRMED`

without implying submission compliance.

## 13. Submission Package

The package workspace should resemble a well-composed file review sheet.

- file rows separated by rules;
- no pre-run status color cards;
- actual known metadata only;
- the right-side `이번 검사` scope is a typographic checklist, not a colored dashboard;
- semantic acknowledgement remains visually explicit but not oversized.

## 14. Results

This is the strongest expression of Editorial Precision.

### 14.1 Summary

Remove colored metric cards.

Preferred structure:

```text
Preflight Result
제출 전 점검이 완료되었습니다.

01 BLOCKER · 01 REVIEW · 03 PASS · 00 EXTERNAL
```

Counts are compact text with semantic status text color only.

### 14.2 Evidence rows

Dominant grammar:

```text
RULE                         EVIDENCE                         VERDICT

영상은 60초 이내여야 합니다     61.0s                            BLOCKER
--------------------------------------------------------------------
기대효과를 포함해야 합니다      proposal.pdf · p.2               REVIEW
                              “참여자의 접근성을 높이고…”
--------------------------------------------------------------------
```

Desktop columns remain the approved three-column evidence chain.

Mobile remains vertical:

`RULE ↓ EVIDENCE ↓ VERDICT`

### 14.3 Status chips

Prefer text + subtle chip only where scan speed improves.

Do not create large red/amber/green blocks.

## 15. Evidence Inspector

Keep right-side drawer behavior and accessibility unchanged.

Visual refinement:

- white background;
- 1px left border;
- minimal shadow only because it is an overlay;
- no tinted full drawer background;
- source locator is small monospace;
- quote uses black text with one restrained highlight treatment;
- technical details remain collapsed.

## 16. Buttons and controls

### Primary button

- accent blue background;
- white text;
- 4px radius;
- 14/20 text, 600 weight;
- integer spacing tokens only.

### Secondary button

- white background;
- black text;
- 1px strong/subtle border depending hierarchy;
- 4px radius.

### Text action

Use text only where hierarchy allows.

Avoid pill-heavy controls.

## 17. Responsive behavior

The current breakpoint architecture may remain if functionally correct, but visible spacing/type values must use approved tokens.

Rules:

- landing becomes single column on mobile;
- large display reduces from 56/64 to 40/48 or 32/40 as needed;
- evidence remains visible;
- no horizontal overflow;
- stepper remains usable without decorative density;
- source/evidence locators may wrap with `overflow-wrap:anywhere`.

## 18. Motion

Existing subtle-motion principle remains.

Motion values may be expressed in `ms`; the integer-pixel rule does not apply to time.

Allowed:

- 120–200ms state transitions;
- drawer slide/fade;
- subtle hover/focus transitions.

No parallax, bounce, infinite animation, decorative scaling, or floating.

Honor `prefers-reduced-motion`.

## 19. Integer Token Rule — normative

The user selected the following rule:

> Visible typography, spacing, radius, and border values must use approved integer-pixel tokens. Layout calculations such as `fr`, `%`, opacity, transform ratios, and responsive calculations are exempt.

This applies to production UI CSS and inline style values.

### Included properties

Audit at minimum:

- `font-size`;
- fixed `line-height` for product typography;
- `margin*`;
- `padding*`;
- `gap`, `row-gap`, `column-gap`;
- `top/right/bottom/left/inset` when used as visible spacing;
- `border-radius`;
- `border-width` and explicit border side widths;
- `outline-width` and `outline-offset`;
- fixed width/height values used for ordinary UI controls/icons when they form the visual system.

### Exempt

- `fr`;
- `%`;
- `vw`, `vh` used for responsive layout;
- opacity;
- transform ratios;
- `calc()`, `min()`, `max()`, `clamp()` when used for responsive layout rather than arbitrary type/spacing values;
- animation duration;
- z-index;
- line-clamp counts;
- grid column counts;
- data-dependent values.

### Typography exception rule

Responsive typography may use `clamp()` only if all min/max endpoints correspond to approved integer type tokens and the resulting design has explicit review approval. Prefer breakpoint token switching over continuously interpolated font sizes.

## 20. Visual Token Audit Gate

Add a deterministic audit for production UI styles.

It must fail when it finds:

- an unapproved font-size;
- an unapproved fixed line-height;
- an unapproved spacing value in a visible spacing property;
- an unapproved border radius;
- an unapproved border width;
- fractional pixel values in included properties;
- arbitrary font weights outside 400/500/600/700;
- arbitrary letter-spacing outside 0/-1/1px;
- raw production colors outside the approved palette unless explicitly allowlisted for browser/system behavior.

The audit must scan at least:

- `frontend/app/globals.css`;
- `frontend/components/profile.module.css`;
- all new production `.css` / `.module.css` files added by this refinement.

Do not scan generated build output or screenshot artifacts.

## 21. Visual QA matrix

Every major state must be reviewed at desktop and mobile.

Required states:

1. landing;
2. custom extraction — provisional AI-extracted state;
3. Human Review — selected item inspector;
4. upload/package — confirmed generic profile, plan READY;
5. upload/package — confirmed generic profile, planner REVIEW_REQUIRED;
6. deterministic BLOCKER result;
7. deterministic READY result;
8. semantic RELATED_EVIDENCE_FOUND REVIEW;
9. semantic NO_CLEAR_EVIDENCE REVIEW;
10. Evidence Inspector open;
11. actionable failure/recovery;
12. recheck comparison.

For each state review:

- color hierarchy;
- type hierarchy;
- spacing rhythm;
- alignment;
- status restraint;
- evidence legibility;
- contrast;
- focus visibility;
- overflow;
- responsive integrity.

## 22. Accessibility

Visual refinement must not lower accessibility.

Requirements:

- body/interactive text must meet WCAG contrast expectations;
- color is never the sole status indicator;
- focus remains clearly visible;
- minimum small text remains 11/16 and is restricted to tertiary/technical labels;
- meaningful body copy defaults to 14/20 or 16/24;
- drawer keyboard behavior remains unchanged;
- reduced-motion behavior remains unchanged.

## 23. Scope protection

This refinement must not alter:

- TASK02–TASK10 backend semantics;
- verification authority;
- Human confirmation;
- AI REVIEW-only authority;
- Plan DSL;
- upload readiness contract;
- semantic acknowledgement;
- polling/stale-session protection;
- recheck fingerprint comparison;
- frozen hashes;
- public runtime architecture.

PR #15 must not be merged until this visual refinement is implemented, audited, reviewed, and fresh CI is green.

## 24. Success criteria

The refinement is complete only when:

- the interface reads as predominantly black/white/neutral at first glance;
- blue is visibly scarce and meaningful;
- landing feels editorial rather than dashboard-like;
- app screens rely on type/spacing/dividers more than colored cards;
- result rows clearly read RULE → EVIDENCE → VERDICT;
- no arbitrary production type/spacing/radius/border values remain;
- deterministic visual token audit passes;
- full frontend regression passes;
- ACTUAL TASK08/TASK10 authority behavior remains unchanged;
- visual QA matrix is reviewed with zero unresolved HIGH/MEDIUM issues;
- final reviewer reports no blocking design-system regression.

## 25. Implementation strategy

Prefer targeted refactoring of the current UI over another information-architecture rewrite.

Expected primary implementation surfaces:

- `frontend/app/globals.css`;
- `frontend/components/profile.module.css`;
- small markup adjustments only where necessary to remove card-heavy wrappers or improve editorial grouping;
- a deterministic visual-token audit script/test;
- Playwright visual-contract assertions and screenshot matrix updates.

Do not reopen settled route architecture or backend contracts.
