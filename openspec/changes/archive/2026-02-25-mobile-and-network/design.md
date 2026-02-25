## Context

The dashboard is a Jinja2/Tailwind app served by uvicorn/FastAPI. It was built desktop-first: the nav bar has 8 links + an action button in a single `flex` row that overflows on narrow viewports; wide data tables have no horizontal scroll container; the spending doughnut chart uses a fixed inline `width:320px` and `responsive: false`. The server defaults to `127.0.0.1`, preventing LAN access from phones or tablets.

All styling uses Tailwind CDN (utility classes only — no build step, no custom CSS file).

## Goals / Non-Goals

**Goals:**
- Server reachable on LAN by default (no flag required)
- Nav usable on 390px-wide screens without information loss
- All tables accessible on narrow screens (horizontal scroll, not content removal)
- Chart scales with its container on any viewport width
- Zero information density loss — every existing data field stays visible

**Non-Goals:**
- Authentication or access control (personal tool, trusted LAN)
- Native mobile app or PWA
- Redesigning page layouts or changing data presented
- Responsive card layout for table rows (over-engineering; scroll is sufficient)

## Decisions

### 1. Default host → `0.0.0.0`

Change `argparse` default from `127.0.0.1` to `0.0.0.0`. The `--host` flag remains for explicit override. No environment variable needed — this is a personal tool.

**Alternative considered:** Document passing `--host 0.0.0.0` at launch. Rejected: requires remembering a flag every time; the desired default _is_ network-accessible.

**Security trade-off:** Any device on the LAN can access the dashboard with no auth. Acceptable for a home network / personal tool; noted in spec.

### 2. Nav: hamburger toggle (pure Tailwind, no JS framework)

On screens narrower than `md` (768px), hide the link list and show a hamburger button. Clicking it toggles a vertical dropdown panel using a small inline `<script>` toggle (one function, no dependencies). On `md:` and wider, the standard horizontal bar is shown — no behaviour change for desktop.

**Alternative considered:** Wrapping nav links to a second row (`flex-wrap`). Rejected: 8 links wrap unpredictably and still look cramped; active-state highlighting becomes confusing.

**Alternative considered:** Icon-only nav on mobile. Rejected: icons for "Recurring" and "Pipeline" are not universally recognisable; text labels are clearer.

### 3. Tables: `overflow-x-auto` wrapper

Wrap every `<table>` in a `<div class="overflow-x-auto">`. The table itself stays `w-full`; on narrow viewports the user scrolls horizontally within the card. No columns are hidden or reordered.

**Alternative considered:** Column priority / hide less important columns with `hidden sm:table-cell`. Rejected: the user explicitly wants no information loss; deciding which columns are "less important" is subjective and fragile.

### 4. Chart: `responsive: true`, remove inline width

Remove `style="width:320px"` from the chart container div. Set `responsive: true` and `maintainAspectRatio: true` in Chart.js options. The container uses Tailwind's `w-full` so the chart fills available space.

**Alternative considered:** Keep fixed size, add `overflow-x-auto`. Rejected: a chart that requires horizontal scroll is a poor experience; true responsiveness is straightforward here.

## Risks / Trade-offs

- **LAN exposure** → Acceptable for personal home network use; document in spec that binding to `0.0.0.0` has no auth.
- **Hamburger adds a tap** → One extra tap to reach nav items on mobile. Acceptable given the alternative (broken overflow).
- **Inline script for nav toggle** → Keeps the template self-contained (no separate JS file). The toggle is ~4 lines; complexity is negligible.
- **Horizontal table scroll UX** → Some users find horizontal scroll on mobile surprising. Mitigated by the fact that this is a personal tool and the user prefers information availability over simplified layout.
