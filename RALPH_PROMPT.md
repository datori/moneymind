# Exploration: Mobile Friendliness and Responsive Design

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard.

### Current State of Focus Area

**base.html** — Shell layout: viewport meta tag is set, nav has a working
hamburger menu (md:hidden / hidden md:flex pattern). Desktop nav links and
Sync Now button hidden on mobile. Mobile panel toggles correctly. No padding
issues in the shell itself.

**index.html** — Dashboard: Net worth summary uses `grid grid-cols-1
sm:grid-cols-3` (good). Spending section uses `flex gap-6 flex-wrap` with
`min-w-64` table and `w-full md:w-80` chart — the chart doesn't stack cleanly
below the table on xs. Recent pipeline runs table is wide (4 columns) with
`overflow-x-auto` wrapper.

**transactions.html** — Filter form uses `flex flex-wrap gap-4 items-end`
which wraps, but the search input has `w-48` and limit `w-24` (fixed widths).
Transaction table (6 columns) has `overflow-x-auto`. Dense but acceptable with
scroll; could hide less critical columns on mobile.

**spending.html** — Summary strip uses `flex items-center gap-6` — on narrow
screens the 4 stats (Total, Transactions, Groups, Avg/day) don't wrap and get
squeezed. Chart/table side-by-side uses `flex gap-6 flex-wrap` with `min-w-80`
chart and `min-w-64` table, causing content to overflow on phones.

**recurring.html** — Top header uses `flex items-center justify-between` with
3 filter chip links — these can't wrap and collide on small screens. Summary
strip is `grid grid-cols-3` with no mobile breakpoint (stays 3-col always).
The recurring table has 8 columns and will need horizontal scroll. Cancel cell
has inline flex-wrap forms. The "Track Cancel" form expands inline in a table
cell, which is very cramped on mobile.

**accounts.html** — Global summary bar uses `flex flex-wrap gap-4` (OK).
Accounts table has 8 columns (Name, Institution, Type, Balance, Txns,
Date Range, Last Synced, Actions) — very wide; horizontal scroll is in place
but no columns are hidden on mobile.

**net_worth.html** — Single chart card, `p-6` padding. Responsive by nature.
Mostly fine.

**review.html** — Table with 7 columns (Date, Amount, Description, Merchant,
Category, Reason, Action). Has `overflow-x-auto`. The category select and
Approve button are in the same row, which gets cramped. Container padding `p-8`
isn't reduced on mobile.

**pipeline.html** — Stats grid is `grid grid-cols-2 sm:grid-cols-4` (good). Run
history table has 9 columns with `overflow-x-auto`. Dense but scrollable. The
streaming progress panel looks fine on mobile.

**reports.html** — Report cards use `grid gap-4 sm:grid-cols-2 lg:grid-cols-3`.
Nicely responsive.

**report_detail.html** — Narrative container has `p-8` padding (too much on
mobile). The narrative table styles don't set overflow/scroll so wide tables in
generated markdown may overflow the viewport.

**_macros.html** — Defines `category_badge(cat)` macro used throughout. No
layout concerns.

## Objective

Improve mobile friendliness and responsive design throughout the app. The base
nav is already mobile-aware, but many pages have dense tables, side-by-side
layouts, fixed-width inputs, and large paddings that break or look poor on
small screens.

Focus on practical, high-impact improvements: stacking layouts properly on
mobile, making the spending summary strip wrap gracefully, reducing padding on
mobile for content-heavy cards, ensuring wide tables scroll rather than
overflow, and improving touch target sizes where feasible.

This is intentionally open-ended. Use your judgment about what "better" means.
Focus on quality, clarity, correctness, and user experience — not quantity of changes.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- finance/web/templates/`
2. Read the file most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore(mobile-responsive): <what changed and why in one line>`

## Tool Reliability Note

Deferred tools (Read, Edit, Grep) require a ToolSearch call to load before first
use each iteration. If a ToolSearch call appears to hang (no response after ~20
seconds), fall back to Bash equivalents: `cat` to read files, `python3 -c` or
`sed` for edits. The Bash tool is always available without loading. Prefer the
dedicated tools when they load normally — they are safer and more precise.

## In Scope

finance/web/templates/base.html
finance/web/templates/index.html
finance/web/templates/transactions.html
finance/web/templates/spending.html
finance/web/templates/recurring.html
finance/web/templates/accounts.html
finance/web/templates/net_worth.html
finance/web/templates/review.html
finance/web/templates/pipeline.html
finance/web/templates/reports.html
finance/web/templates/report_detail.html
finance/web/templates/_macros.html

## Do Not Touch

finance/pipeline/
finance/web/app.py
finance/db/
openspec/ (specs are written during archive, not during exploration)
.claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
