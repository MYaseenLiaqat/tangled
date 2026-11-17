# Tangled design system (v1)

Status: **adopted 2026-11-17.** Implemented in `frontend/src/styles.css` (tokens at the top) and `frontend/src/ui/`
(`Icon.tsx`, `kit.tsx`, `Brand.tsx`). Decisions: scholar teal accent, Inter Variable self-hosted via
`@fontsource-variable/inter`, and unflagged topics shown as "Being watched" on the Overview.

Tangled has two audiences with different jobs:
- **Instructors** scan evidence and decide what to re-teach. They need calm, dense-but-quiet surfaces and trustworthy numbers.
- **Students** ask, read and think. They need a distraction-free reading column and tactile, rewarding feedback.

Principles: one brand accent, hairline structure instead of shadows, numbers that never jitter, every state
designed (empty, loading, error, closed), and nothing that moves without a reason.

---

## 1. Color tokens

All colors are CSS custom properties on `:root`. Dark mode follows the OS (`prefers-color-scheme`) as today.

### Surfaces and ink

| Token | Light | Dark | Use |
|---|---|---|---|
| `--canvas` | `#FAFAF9` | `#0F1115` | Page background (warm alabaster / slate-charcoal) |
| `--surface` | `#FFFFFF` | `#181B20` | Cards, panels, inputs on canvas |
| `--surface-sunken` | `#F4F4F2` | `#13161A` | Inputs, code, citation blocks, table headers |
| `--surface-hover` | `#F6F6F4` | `#1E2228` | Row and nav hover |
| `--line` | `#E7E5E0` | `#262A31` | 1px hairlines (default border) |
| `--line-strong` | `#D6D3CD` | `#353A42` | Hovered or interactive borders, button bottom edge |
| `--ink` | `#1C1917` | `#ECEDEE` | Primary text |
| `--ink-2` | `#44403C` | `#C4C7CB` | Body text in long-form answers |
| `--mute` | `#6B6560` | `#9BA1A6` | Secondary text (≥ 4.5:1 on canvas and surface) |
| `--faint` | `#A8A29E` | `#5F656D` | Placeholders, disabled |

### Brand (one accent)

**Recommendation: keep Tangled's teal, deepened to "scholar teal".** It's already the logo color, it reads calm
and academic, and it avoids the generic indigo that most AI products use. (The alternative, cobalt `#2563EB`, is
noted in section 9.)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--brand` | `#0F766E` | `#2DD4BF` | Primary buttons, links, active nav, progress fill |
| `--brand-hover` | `#115E59` | `#5EEAD4` | Hover and pressed |
| `--brand-soft` | `#E7F3F1` | `rgba(45,212,191,.12)` | Selected rows, soft chips, focus halo |
| `--on-brand` | `#FFFFFF` | `#04211E` | Text on brand fills (contrast 5.5:1 / 9:1) |
| `--focus` | `rgba(15,118,110,.35)` | `rgba(45,212,191,.45)` | 3px focus ring |

### Learning-state semantics

| State | Token (fg / bg) light | Dark | Meaning in Tangled |
|---|---|---|---|
| Mastery / done | `--ok #047857` / `#ECFDF5` | `#34D399` / `rgba(16,185,129,.14)` | Topic addressed, file indexed, answer marked clear, quiz ≥ 75% |
| Attention / in progress | `--warn #B45309` / `#FFFBEB` | `#FBBF24` / `rgba(245,158,11,.14)` | **Topic needs attention**, file processing, evidence highlight, quiz 60–74% |
| Gentle correction | `--bad #BE123C` / `#FFF1F2` | `#FB7185` / `rgba(244,63,94,.14)` | Errors, failed upload, quiz < 60% (the QUIZ_LOW threshold), destructive actions |
| Neutral info | `--info #1D4ED8` / `#EFF6FF` | `#60A5FA` / `rgba(59,130,246,.14)` | Monitoring tier, tips, "not counted" evidence |

A flagged topic changes from red ("Review") to **amber**, which means *worth your attention*, not alarm. Red is
reserved for real errors and low scores.

---

## 2. Typography

**Family:** *Inter Variable*, self-hosted (the server's security policy blocks font CDNs, and today
**no font loads at all**: `Manrope` and `DM Sans` fall back to Times New Roman in the brand mark and stat numbers).
Fallback: `ui-sans-serif, system-ui, "Segoe UI", sans-serif`. Optional mono for join codes: `ui-monospace, "Cascadia Mono", Consolas`.

Global features: `font-feature-settings: "cv11", "ss01"`. Turn on `font-variant-numeric: tabular-nums` for **every**
number: stats, percentages, counts, join codes, quiz rates, file sizes.

| Token | Size / line-height | Weight | Tracking | Use |
|---|---|---|---|---|
| `--t-display` | 36 / 1.1 | 650 | -0.025em | Big stats (share %, summary counters) |
| `--t-h1` | 28 / 1.2 | 650 | -0.02em | Page titles |
| `--t-h2` | 20 / 1.3 | 600 | -0.015em | Section titles |
| `--t-h3` | 16 / 1.4 | 600 | -0.01em | Card titles |
| `--t-body` | 14 / 1.55 | 400 | 0 | UI text |
| `--t-read` | 15.5 / 1.65 | 400 | 0 | Tutor answers, consent text: **max 68ch** |
| `--t-small` | 13 / 1.5 | 400 | 0 | Notes, meta |
| `--t-micro` | 11.5 / 1.3 | 600 | 0.06em, uppercase | Eyebrows, table headers |

Long titles (course names, file names, topic names) get `text-overflow: ellipsis` in cards with a `title` tooltip,
and wrap to 2 lines (`line-clamp: 2`) in headings.

---

## 3. Space, radius, layout

- **Spacing:** 4px grid. Tokens `--s-1`…`--s-10` = 4, 8, 12, 16, 20, 24, 32, 40, 48, 64.
- **Radius:** `--r-sm 6px` (chips, code) · `--r-md 10px` (buttons, inputs) · `--r-lg 14px` (cards) · `--r-xl 20px` (auth and join cards).
- **Page widths:** instructor content max **1120px**; student reading column max **720px** (answers capped at 68ch).
- **Instructor shell:** light 248px sidebar on the canvas with a hairline divider (no dark teal slab). Nav items are 36px
  high with icon and label; the active item has a `--brand-soft` background and `--brand` text. The header becomes a quiet
  **course bar**: the course name, the join code as a copyable chip, and the account menu.
- **Mobile (< 820px):** the sidebar collapses to a top bar with a horizontal scrollable tab row. Cards stack. Students get a
  composer pinned to the bottom.

---

## 4. Borders and elevation

Hairlines do the structure; shadows are rare and soft.

| Level | Recipe | Use |
|---|---|---|
| e0 | `1px solid var(--line)` | Panels, tables, inputs |
| e1 | e0 + `0 1px 2px rgba(28,25,23,.04)` | Cards on canvas |
| e1-hover | border `--line-strong`, `translateY(-1px)`, `0 4px 12px rgba(28,25,23,.06)` | Clickable cards (course, topic, file) |
| tactile | `box-shadow: inset 0 -2px 0 rgba(0,0,0,.14)` on primary buttons, `inset 0 -1px 0 var(--line-strong)` on secondary | Physical bottom edge |
| overlay | `0 12px 32px rgba(28,25,23,.12)` | Menus, toasts, confirm dialogs only |

In dark mode all shadows → none; hairlines and surface steps carry the depth.

---

## 5. Motion

- Standard: `160ms cubic-bezier(.2,.8,.2,1)` on color, border, shadow, transform.
- Press: `:active { transform: scale(.98) }` on buttons, chips and clickable cards.
- Entering content (new answer, toast): 200ms fade plus 4px rise. Skeletons shimmer at 1.4s.
- `prefers-reduced-motion`: no transforms or shimmer, color changes only (this exists today and is kept).

---

## 6. Components

| Component | Spec |
|---|---|
| **Button** | Height 36 (sm 30, lg 42). **Primary**: brand fill and tactile edge. **Secondary**: surface, e0 and tactile edge. **Ghost**: no border, hover `--surface-hover`. **Danger**: rose text, rose-soft hover, solid rose only inside the confirm dialog. Loading state keeps the width (text swaps, no jump) |
| **Input / textarea / select** | 40px high, `--surface-sunken` fill, e0. Focus: border `--brand` plus 3px `--focus` ring. Always a visible label (no placeholder-only fields, unlike Topic setup today). Error text below in `--bad` |
| **Checkbox** | Custom 18px box with r-sm; checked = brand fill and a white check. Same for the consent box and "Allow new students to join" (as a **switch**) |
| **Card** | Surface, e1, r-lg, 20–24px padding (fixes today's zero-padding topic cards in Topic setup) |
| **Status pill** | Dot and label, 22px high, r-full, semantic soft background: `● Needs attention` (warn), `✓ Addressed` (ok), `◐ Monitoring` (info), `○ Not enough data` (neutral) |
| **Confidence meter** | 3 small bars plus a label ("High" = 3 filled, "Medium" = 2), instead of a colored pill. Reads as strength, not alarm |
| **Progress / share bar** | 6px track `--surface-sunken`, r-full, fill `--brand` (quiz bars use semantic colors by threshold); 400ms width transition |
| **Stat** | Micro label above, display number (tabular), optional delta or caption below. Separated by hairlines, not boxes |
| **Table → list rows** | Quiz and Materials become row lists: 56px rows, hairline separators, hover `--surface-hover`, key column bold with meta below, actions right-aligned and revealed on hover (always visible on touch) |
| **Empty state** | Line-art icon in a 44px soft circle, one encouraging sentence, one primary action. E.g. *"No questions yet. Share the join code and you'll see where your class gets stuck."* |
| **Skeleton** | Same dimensions as the real thing: summary strip (3 × 64px), topic cards (2 × 196px), message thread (2 bubbles). Replaces every "Loading…" text |
| **Toast** | Bottom-center (mobile) / bottom-right, overlay elevation, auto-dismiss 3s. Used for "Topic added", "Copied join link", "Settings saved" |
| **Confirm dialog** | Replaces `window.confirm` / `window.prompt` for deleting a course. It still asks for the course name; the API call is unchanged |
| **Icons** | ~14 hand-authored inline SVGs (1.75px stroke, 20px box) in `src/ui/Icon.tsx`, with no icon library: overview, quiz, files, settings, back, search, upload, copy, check, alert, doc types (pdf, slides, doc, notebook, text), send. They replace today's Unicode glyphs (◈ ▤ □ ⚙ ∿ ⌕ ↑), which render differently on every OS |

---

## 7. Learning-state patterns per screen

| Screen | Pattern |
|---|---|
| **Overview** | Stat strip (questions · students asked "12 / 30" · topics needing attention). Flagged topic cards: status pill, name with module, big tabular share %, share bar, confidence meter, "Review evidence →". Below, a quiet **"Being watched"** list of unflagged topics (the API already returns them; today they're hidden). Encouraging empty state |
| **Topic detail** | Header with status pill and a sticky action bar (**Mark as addressed** primary, **Not a real problem** ghost). "Why it's flagged" as a checklist of signals with ✓ in ok-soft circles. Confusion groups as cards: title, count chip, quotes in reading font with the amber evidence highlight (`--warn` soft background, 2px underline) |
| **Quiz** | "Hardest question" callout. Rows: item and topic, correct-rate bar colored ok/warn/bad by threshold, top wrong option chip. Import button with drop affordance |
| **Materials** | Dropzone (dashed `--line-strong`, brand-soft on drag), file rows with a type icon, size, sections, and a status dot: processing = amber pulsing dot plus an indeterminate bar; failed = rose with the reason inline and a retry hint |
| **Topic setup** | Two columns on desktop: **Topics** (list and add/edit form with labels, 0/10 counter as a slim progress bar) · **Course settings** (name, class size, join switch, **Share card** with a big monospace join code, Copy link and Copy code buttons, Regenerate) · **Danger zone** (outlined rose section) |
| **Student** | Reading column. Course name and a materials row (compact doc chips with type icons). A **conversation thread**: the student's question right-aligned in a brand-soft bubble; the answer as a card with formatted text at 68ch, citation chips `[1]` linked to the Sources list, and **feedback toggles** ("✓ Got it" / "Still unclear") that show a selected state (ok / warn soft). The composer is pinned at the bottom with an auto-growing textarea and a send button, and a "Thinking…" skeleton bubble while waiting. Empty state: *"Ready when you are. Ask about anything in your course materials."* |
| **Join / consent / login** | Centered r-xl card on canvas with a faint teal radial wash (already introduced). Monospace join-code field, custom checkbox, consent text at the reading measure |

---

## 8. Accessibility guardrails

- Text contrast ≥ 4.5:1 (body) and ≥ 3:1 (large or UI glyphs) in both themes; status is never shown by color alone (dot or icon plus label).
- Visible 3px focus ring on every interactive element; hit targets ≥ 40px on touch.
- Keep all current accessible names and roles (tests depend on them: "Join course", "Course code", "Your question", "Return to join", "Search topics", etc.).
- Custom scrollbar: 10px, thumb `--line-strong`, track transparent; native on touch.

## 9. Open decisions

1. **Accent:** scholar teal `#0F766E` (recommended, keeps brand continuity) **or** focused cobalt `#2563EB`.
2. **Font delivery:** add `@fontsource-variable/inter` (one small font-files package, no build change, served from `self` so the CSP is happy) **or** use the system font stack only (zero deps; Segoe UI on Windows, SF on Mac).
3. **Show unflagged topics** on Overview as a quiet "Being watched" list (the data is already in the API response; presentation only).
