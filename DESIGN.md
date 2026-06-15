---
name: Dashboard Operasional Rumah Pandega
description: Internal operational dashboard for a multi-role boarding house management team.
colors:
  command-depth: "#0F172A"
  slate-surface: "#1E293B"
  ghost-surface: "#F1F5F9"
  card-white: "#FFFFFF"
  card-border: "#E8EDF3"
  input-surface: "#F8FAFC"
  ink-secondary: "#64748B"
  ink-tertiary: "#94A3B8"
  ink-sidebar: "#E2E8F0"
  role-executive: "#4F46E5"
  role-sales: "#059669"
  role-admin: "#2563EB"
  role-marketing: "#7C3AED"
  role-ops: "#EA580C"
  signal-success: "#16A34A"
  signal-danger: "#DC2626"
  signal-warning: "#D97706"
  signal-caution: "#F59E0B"
typography:
  display:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.5px"
  headline:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.2
  title:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.5
  label:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.3
  micro:
    fontFamily: "system-ui, -apple-system, sans-serif"
    fontSize: "10px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.1em"
rounded:
  xs: "4px"
  sm: "8px"
  md: "10px"
  lg: "12px"
  xl: "16px"
  full: "99px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  2xl: "24px"
  3xl: "40px"
components:
  kpi-card:
    backgroundColor: "{colors.card-white}"
    rounded: "{rounded.xl}"
    padding: "0 0 12px"
  button-primary:
    backgroundColor: "{colors.role-executive}"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "#4338CA"
    textColor: "#FFFFFF"
    rounded: "{rounded.sm}"
  input-text:
    backgroundColor: "{colors.input-surface}"
    textColor: "{colors.command-depth}"
    rounded: "{rounded.sm}"
  sidebar-nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.ink-tertiary}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  sidebar-nav-active:
    backgroundColor: "{colors.slate-surface}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  period-badge:
    backgroundColor: "{colors.ghost-surface}"
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.full}"
    padding: "2px 10px"
  empty-state:
    backgroundColor: "{colors.card-white}"
    rounded: "{rounded.xl}"
    padding: "40px 20px"
---

# Design System: Dashboard Operasional Rumah Pandega

## 1. Overview

**Creative North Star: "The Control Room"**

This is a dual-register system. The left panel is the cockpit: pitch dark, authoritative, role-aware. The right surface is the working floor: cool, clean, every number given space to breathe. You know where you are in the hierarchy the instant the page loads — the contrast between sidebar and content is not a styling choice, it's a structural signal.

Five roles operate this dashboard. Each has its own accent channel — indigo for Executive, emerald for Sales, blue for Admin, violet for Marketing, orange for Operasional — and that channel fires only as a signal: the top strip of a KPI card, the color of a chart line, the active state of a nav item. Everywhere else, the palette holds discipline. Rarity is what makes the signal meaningful.

The system rejects the two failure modes it was explicitly built against: the korporat kaku aesthetic of legacy BI tools (heavy chrome, gray gradients, zero personality, every control a form field) and the generic SaaS template (off-the-shelf card grid, tracked eyebrow above every section, indistinguishable from any other SaaS dashboard). This dashboard was built for one team, for one business. It should feel exactly that way.

**Key Characteristics:**
- Dark command sidebar (Slate Cockpit `#0F172A`) anchors every screen
- Cool neutral working surface (Ghost Surface `#F1F5F9`) with white card elevation
- Five role-specific accent channels; cross-contamination prohibited
- Flat depth model: background tonal steps replace shadows entirely
- KPI value (24px/700) is the loudest typographic element on any screen
- System font only; no decorative type choices

## 2. Colors: The Control Room Palette

Two structural colors and five signal channels. Everything else is infrastructure.

### Primary

- **Command Depth** (`#0F172A`): The anchor of the visual hierarchy. Used as sidebar background AND as primary text ink on the white surface. This deliberate dual role means the darkest and most authoritative color appears at both extremes — commanding the navigation and grounding the data.
- **Slate Surface** (`#1E293B`): The elevated layer within the sidebar. Active nav items, user profile cards, period selector — any sidebar element that needs to lift above the base floor.

### Secondary — Role Signal Channels

Five channels; each reserved exclusively for one division.

- **Executive Indigo** (`#4F46E5`): The default system accent. Appears on Executive pages and on all shared UI elements that predate the role split (login button, focus rings).
- **Sales Emerald** (`#059669`): Active only on Sales pages.
- **Admin Blue** (`#2563EB`): Active only on Admin pages.
- **Marketing Violet** (`#7C3AED`): Active only on Marketing pages.
- **Ops Orange** (`#EA580C`): Active only on Operasional pages.

### Tertiary — Semantic States

Four fixed roles; meaning is non-negotiable.

- **Signal Success** (`#16A34A`): Positive delta, "Aman" status, good performance indicators.
- **Signal Danger** (`#DC2626`): Negative delta, overdue items, SLA breach, cancellation.
- **Signal Warning** (`#D97706`): Caution states — kontrak berakhir ≤30 hari, items needing action.
- **Signal Caution** (`#F59E0B`): Softer alert — booking status, intermediate flags.

### Neutral

- **Ghost Surface** (`#F1F5F9`): Main content background. Cool, not warm. The contrast with Command Depth sidebar is the first visual hierarchy the eye reads.
- **Card White** (`#FFFFFF`): All KPI cards, chart containers, form surfaces. One step above Ghost Surface.
- **Card Border** (`#E8EDF3`): 1px borders on all cards and chart containers. Sufficient for separation; no shadow needed.
- **Input Surface** (`#F8FAFC`): Input field backgrounds; slightly lighter than Ghost Surface.
- **Ink Secondary** (`#64748B`): Sub-labels, subtitles, period text, sidebar section headers. Never primary copy.
- **Ink Tertiary** (`#94A3B8`): Empty state text, idle sidebar nav items, chart axis tick labels.
- **Ink Sidebar** (`#E2E8F0`): Base text color within the sidebar when placed on Command Depth.

**The Signal Rule.** Role accent colors appear in exactly three contexts: (1) the 4px top strip of KPI cards on that role's page, (2) chart line/bar/fill colors on that role's page, (3) the left-border active indicator in sidebar navigation. They never appear as card backgrounds, section backgrounds, button colors on non-login contexts, or decorative highlights. A role color on the wrong page is always an error.

**The Five-Channel Rule.** Cross-contamination between role channels is prohibited. Executive Indigo does not appear on Sales pages. Ops Orange does not appear on Admin charts. The accent the eye sees tells the user which context they're in — mixing channels destroys that signal.

## 3. Typography

**Body/UI Font:** system-ui, -apple-system, sans-serif (Streamlit default system stack)

No custom type is declared. The system relies on the OS default sans-serif at precisely calibrated weights and sizes. This is a deliberate choice: the dashboard is a working tool, not an editorial surface. The data is the voice; the type is infrastructure.

**Character:** One family across all weights. The scale creates hierarchy through size and weight alone, with no decorative variation. Discipline, not personality.

### Hierarchy

- **Display** (700, 24px, -0.5px tracking, lh 1.1): KPI metric values. This is the typographic peak of the page — the number the user came to read. Nothing competes.
- **Headline** (700, 22px, lh 1.2): Page section headers (e.g. "Ringkasan Eksekutif"). Used once per page.
- **Title** (600, 14px, lh 1.4): Chart and section headers. Paired with a subtitle line in Ink Tertiary.
- **Body** (500, 13px, lh 1.5): Sidebar navigation labels, subtitles, table cell content, general prose.
- **Label** (500, 12px, lh 1.3): KPI card sub-labels (e.g. "Tingkat Hunian"), tag text.
- **Micro** (700, 10px, 0.1em tracking, uppercase): Sidebar section dividers only ("PERIODE", "NAVIGASI"). Used sparingly in navigation structure; never as eyebrow headers above content sections.

**The Number-First Rule.** The KPI Display value (24px/700) is the loudest element on any data screen. No heading, icon, chart label, or badge may visually compete with it. If it is not immediately legible at a glance, something around it is wrong.

**The Micro-Only Rule.** Uppercase tracked type (Micro style) is permitted only as sidebar navigation section dividers. It is prohibited as eyebrow/kicker text above any content section on the main surface. That pattern is the saturated AI grammar this system explicitly rejects.

## 4. Elevation

This system is completely flat. There are no box-shadows. Depth is expressed through exactly three tonal steps, read left-to-right and back-to-front:

1. **Command Depth** (`#0F172A`) — the sidebar; the deepest layer
2. **Ghost Surface** (`#F1F5F9`) — the main content background; the working floor
3. **Card White** (`#FFFFFF`) — cards and chart containers; the foreground surface

The border (`#E8EDF3`, 1px solid) defines card edges. The contrast between Ghost Surface and Card White (ΔL ≈ 5%) is sufficient for clear separation without shadow.

**The Flat-By-Default Rule.** Shadows are prohibited at all states. If a new component requires depth differentiation, add a tonal background step (e.g. `#F8FAFC`) or increase border contrast. Never reach for `box-shadow` as a first response.

## 5. Components

### KPI Cards

The signature component. Four per page, arranged in a 4-column grid, each owned by one metric.

- **Structure:** 16px rounded card, 1px `#E8EDF3` border, white background. A 4px color strip at the top (role accent color) signals context without text. Below: 14–20px body padding containing label → value → sub → delta → optional sparkline.
- **Label:** 12px/500, `#64748B`. One line; describes the metric.
- **Value (Display):** 24px/700, `#0F172A`, -0.5px tracking. The answer to the user's question.
- **Sub:** 11px, color-coded (`#16A34A` positive, `#DC2626` negative, `#D97706` warning, `#64748B` neutral).
- **Delta badge:** 10px/600, `▲`/`▼` prefix, same color logic as sub. "vs sblm" suffix.
- **Sparkline:** Optional SVG area chart, role accent color at 12% opacity fill. Shown only when ≥2 data points exist.

### Chart Containers

Two-part structure: a rounded header element paired with the chart body.

- **Chart header:** White background, 1px `#E8EDF3` border, 16px top radius, no bottom radius, no bottom border. Contains title (14px/600, `#0F172A`) and subtitle (11px, `#94A3B8`). Top border uses role accent — **use `border-top: 3px solid [role-accent]` (not `border-left`)**.
- **Chart body:** White background, left + right + bottom 1px `#E8EDF3` borders, 0 top radius, 16px bottom radius, 8px side padding. `margin-bottom: 16px`.
- **Chart palette:** Transparent paper and plot backgrounds. Grid lines `#E2E8F0`. Axis tick labels 10px `#374151`. Legend 11px `#374151`.

**The No-Stripe Rule.** `border-left` or `border-right` greater than 1px as a colored accent is prohibited on any content container — including chart headers, callout cards, and data rows. The existing `.cht-hdr border-left: 3px` pattern violates this rule and must be replaced with `border-top` on the next polish pass. The sidebar nav active `border-left` is a deliberate navigation affordance and is the sole exception.

### Sidebar Navigation

- **Container:** `#0F172A` background, no border.
- **Nav items:** 13px/500, `#94A3B8` at rest. `#1E293B` background + `#FFFFFF` text + 600 weight on active. `border-left: 3px solid [role-accent]` on active — the only permitted content left-border in this system, because it is a navigation indicator, not a content decoration. `border-radius: 10px`. Emoji icon + label, displayed as flex row.
- **Section dividers:** Micro style (10px/700, uppercase, 0.1em tracking), `#475569`. "PERIODE" and "NAVIGASI" only.

### Page Headers

- **Title:** 22px/700, `#0F172A`, flex row with role emoji icon and label.
- **Subtitle:** 13px, `#64748B`, includes period badge inline.
- **Accent bar:** 3px height, 48px width, `border-radius: 99px`, role accent color. Appears below subtitle. This is the only colored decorative element permitted in page headers.

### Buttons

- **Primary (Login / Submit):** `#4F46E5` background (Executive Indigo regardless of page context), white text, 600 weight, 8px radius. Hover: `#4338CA`. Focus: `outline: 2px solid #4F46E5; outline-offset: 2px`. Used only for form submission (login screen) and sidebar Refresh.
- **No secondary or ghost variants** exist in the current system. Do not introduce them without a defined design rationale.

### Input Fields

- **Default:** `#F8FAFC` background, `#0F172A` text, `#E2E8F0` border, 8px radius.
- **Focus:** `border-color: #4F46E5`, no box-shadow, no glow.
- **Label:** 13px/500, `#374151`, above the field.
- **Placeholder:** `#94A3B8` (must maintain ≥4.5:1 contrast; verify before changing).

### Period Badge

Inline pill appended to page subtitle. `#F1F5F9` background, `#475569` text, `#E2E8F0` border, `99px` radius, 11px. Prefixed with 📅 emoji. Never used as a standalone section marker.

### Empty States

Centered card: white background, 1px `#E8EDF3` border, 16px radius, 40px vertical padding. 32px emoji icon, 13px `#94A3B8` message text. Appears whenever a data section has no records for the selected period. Tone: matter-of-fact, not apologetic.

## 6. Do's and Don'ts

### Do:

- **Do** use role accent colors exclusively for KPI card top strips, chart lines/fills, and sidebar nav active indicators on that role's page. Nowhere else.
- **Do** maintain the three-layer depth hierarchy: Command Depth sidebar → Ghost Surface main → Card White cards. Never flatten or collapse these layers.
- **Do** make KPI display values (24px/700) the loudest element on every data screen. Test this: glance for 1 second — the number you needed should be what you saw.
- **Do** use `border-top: 3px solid [role-accent]` on chart headers if an accent indicator is needed. Never `border-left`.
- **Do** use the period badge consistently in every page subtitle — it is part of the data contract, not decoration.
- **Do** maintain WCAG AA contrast (4.5:1) for all body text, labels, and placeholder text. The palette's muted grays are already close to the floor; do not dilute further.
- **Do** use empty state components whenever a data section has zero records. Never hide the container or show a blank white box.

### Don't:

- **Don't** use `border-left` or `border-right` greater than 1px as a colored accent on any content card, chart header, callout, or data row. This is an absolute ban. Replace with `border-top`, a background tint, or nothing. The sidebar nav active state is the sole exception.
- **Don't** feel like SAP or Oracle — no heavy gray gradients, no multi-level chrome, no form-heavy layouts, no enterprise-gray color schemes.
- **Don't** feel like a generic SaaS template — no identical icon + heading + text card grid, no uppercase tracked eyebrow above content sections, no numbered section markers (01 / 02 / 03) used as scaffolding.
- **Don't** use role accent colors as full card backgrounds or section backgrounds in the main content area.
- **Don't** introduce box-shadows. Elevation is expressed through background contrast and borders only.
- **Don't** add gradient text (`background-clip: text`). Display values are solid `#0F172A`; accent values are solid role-color. No gradients.
- **Don't** mix role accent channels between pages. Executive Indigo on a Sales page, or Ops Orange on an Admin section, is always a bug.
- **Don't** use Micro style (uppercase tracked) as eyebrow/kicker text above any main-surface content section. It is permitted only as sidebar navigation section dividers.
- **Don't** add decorative elements that carry no data meaning: glassmorphism, hero-metric templates (big number + small label + gradient blob), identical card grids, decorative blur layers.
