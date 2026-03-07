# Design: Explore mobile-responsive

## Overview

The loop made five focused layout fixes across four template files. Every
change used Tailwind CSS responsive utility classes — no CSS was written, no
backend code was touched, and no JavaScript logic was altered. The overall
pattern was consistent: replace `flex`/`grid` containers that had no mobile
breakpoint with variants that stack on small screens and side-by-side on
larger ones, and hide visual separators that look wrong when items wrap.

The `report_detail.html` change was the most structurally interesting — it also
required a small JS addition to wrap dynamically-rendered markdown tables in
scrollable containers post-render.

## Iteration Progression

**Iteration 1 — spending.html summary strip**
The 4-stat summary strip (Total spent, Transactions, Groups, Avg/day) used
`flex items-center gap-6` with no wrapping, causing stats to crunch together on
narrow screens. Changed to `flex flex-wrap gap-x-6 gap-y-2` and hid the pipe
separator dividers on xs (`hidden sm:block`) since they look odd when content
wraps mid-row.

**Iteration 2 — recurring.html header + summary grid**
The recurring page header used `flex items-center justify-between` with three
filter chip links (Housing, Education, Health). These chips could not wrap and
would collide with the heading on narrow screens. Fixed by switching to
`flex flex-wrap items-center gap-3` and moving the chip container to
`ml-auto` within the same flex row. Separately, the 3-card summary strip
(`grid grid-cols-3`) had no responsive breakpoint — changed to
`grid grid-cols-1 sm:grid-cols-3` so the Monthly/Annual/Due Soon cards stack
on mobile.

**Iteration 3 — report_detail.html padding + table overflow**
The narrative card had `p-8` padding which is fine on desktop but wastes
significant horizontal space on phones. Changed to `p-4 sm:p-8`. Also,
narrative content is rendered from Markdown via marked.js — any tables in the
generated narrative had no overflow handling and could overflow the viewport.
Fixed by: (a) adding `.table-wrap { overflow-x: auto; }` CSS, and (b) adding
a post-render JS pass that wraps each `<table>` in a `.table-wrap` div.

**Iteration 4 — spending.html chart/table stacking**
The chart + table side-by-side layout used `flex gap-6 flex-wrap` with
`min-w-80` on the chart and `min-w-64` on the table. On phones these min-widths
prevent proper wrapping and cause horizontal overflow of the page. Replaced with
`flex flex-col lg:flex-row gap-6`, giving each panel `w-full` on mobile and
`lg:flex-1` on large screens.

**Iteration 5 — index.html dashboard spending section**
The same flex-wrap + min-w pattern existed on the dashboard home page for the
spending doughnut chart and category table. Applied the same fix: `flex
flex-col md:flex-row gap-6` (md rather than lg since the dashboard doughnut is
narrower). The chart retains its `w-full md:w-80` sizing since it's a circular
chart that doesn't need to expand to fill all available space.

## Design Decisions

**flex-col → flex-row at breakpoint vs. flex-wrap with min-w**
The original layouts used `flex flex-wrap` with minimum widths as an
approximation of responsive two-column layout. This is a common pattern but
fragile — on screens between the min-widths it creates partial wrapping that
looks broken. Replacing with explicit `flex-col {breakpoint}:flex-row` is
more predictable and intentional.

**lg vs. md breakpoint for spending page**
The spending page chart is a full-width bar chart that needs horizontal space
to be readable, so the side-by-side layout was deferred to `lg` (1024px).
The dashboard home chart is a doughnut (fixed `w-80 = 320px`) that reads fine
on smaller screens, so `md` (768px) was used there.

**Hiding pipe separators vs. removing them**
The spending summary strip uses `|` dividers between stats. Rather than
removing them (which would affect desktop layout), `hidden sm:block` hides
them only on xs. On sm+ they remain. This avoids the ugly mid-row pipe
that would appear if items wrapped.

**JS table wrapping vs. CSS only**
Narrative tables are inserted by marked.js at runtime, so a CSS-only approach
(e.g., wrapping the narrative container in overflow-x-auto) would cause the
entire narrative to scroll rather than just wide tables. The JS post-processing
approach wraps each table individually, preserving normal flow for other content.

## Coherence Assessment

The five iterations composed well — they addressed distinct problem areas
without contradicting each other. No iteration was redundant. The loop
correctly identified the spending/index chart+table layouts as the same
underlying problem and applied consistent fixes (iteration 4 and 5).

The loop correctly stopped at iteration 5 after addressing the most impactful
issues. It did not attempt to rewrite the transactions table, accounts table, or
review table — those all already had `overflow-x-auto` wrappers and are
acceptable with horizontal scroll.

One honest limitation: the loop noted but did not fix the transactions filter
form having fixed-width inputs (`w-48` for search, `w-24` for limit). These
could be improved with `w-full sm:w-48` style responsive sizing, but this was a
lower-priority improvement and the loop ran out of iterations.

## What Was Improved

- **Spending page summary strip**: 4 stats now wrap gracefully on mobile; pipe separators hidden on xs
- **Spending page layout**: chart and table stack full-width on mobile, side-by-side on large screens
- **Recurring page header**: filter chips can wrap below the heading on narrow screens
- **Recurring page summary**: Monthly/Annual/Due Soon cards stack vertically on mobile
- **Report detail page**: narrative card padding halved on mobile (p-4); generated markdown tables scroll horizontally instead of overflowing the viewport
- **Dashboard spending section**: spending category table and doughnut chart stack on mobile

## What Was Not Addressed

- `transactions.html` filter form: search input (`w-48`) and limit (`w-24`) have fixed widths that could use responsive sizing
- `accounts.html` table: 8 columns all visible on mobile; horizontal scroll is in place but some columns (e.g., Date Range, Last Synced) could be hidden on mobile to reduce scroll distance
- `review.html`: 7-column table, horizontal scroll works, but the inline category select + approve button layout in a single row is cramped on phones
- `pipeline.html` run history: 9-column table, horizontal scroll works
- No touch-specific improvements (tap target sizing, etc.) were made
