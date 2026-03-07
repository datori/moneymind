# Exploration: Filter Bar UX — Transactions Page

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard.

### Current State of Focus Area

**`finance/web/templates/transactions.html`** — the full transactions page
template. The filter bar (lines 9–59) is the primary focus area. It contains:

- A "Month" navigation group: prev (‹) and next (›) buttons around a JS-driven
  month label, which auto-submits to set start/end to the full calendar month.
- Start date and End date inputs (type="date"), individually labeled.
- A Search text input (placeholder: "merchant or description"), fixed width w-48.
- A Category dropdown (All Categories + dynamic list from route context).
- A Limit number input (min 1, max 1000), fixed width w-24.
- Two hidden inputs preserving sort_by and sort_dir across filter submissions.
- A Filter submit button (indigo, right-aligned in the flex row).

The filter bar uses `flex flex-wrap gap-4 items-end` — controls wrap at
narrow viewports but there is no responsive grouping or priority ordering.
All controls share equal visual weight; the Limit field (a rarely-changed
power-user option) sits at the same level as Search and Category.

The count line at the bottom reads: "Showing N transaction(s)." using the
awkward `(s)` pattern.

The JS at the bottom (lines 123–170) drives the month navigation: it reads
start/end date inputs, updates the month label text, and auto-submits the
form when prev/next is clicked.

No "Clear" or "Reset" button exists — resetting filters requires manually
clearing each field.

## Objective

Improve the transactions filter bar layout, label clarity, and mobile
usability. The bar uses a flat flex-wrap layout that can crowd or misalign
on narrow viewports. Possible improvements include:

- Grouping related controls (e.g., date range as a unit)
- Responsive layout adjustments for narrow viewports
- Visual de-emphasis of low-priority fields (Limit)
- A clear/reset affordance
- Fixing the awkward "transaction(s)" count phrasing
- Any other UX refinements that reduce noise or improve clarity

This is intentionally open-ended. Use your judgment about what "better" means.
Focus on quality, clarity, correctness, and user experience — not quantity of changes.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- finance/web/templates/transactions.html`
2. Read the file most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore(filter-bar-ux): <what changed and why in one line>`

## Tool Reliability Note

Deferred tools (Read, Edit, Grep) require a ToolSearch call to load before first
use each iteration. If a ToolSearch call appears to hang (no response after ~20
seconds), fall back to Bash equivalents: `cat` to read files, `python3 -c` or
`sed` for edits. The Bash tool is always available without loading. Prefer the
dedicated tools when they load normally — they are safer and more precise.

## In Scope

finance/web/templates/transactions.html

## Do Not Touch

finance/web/app.py
finance/web/templates/base.html
finance/web/templates/_macros.html
finance/analysis/
openspec/ (specs are written during archive, not during exploration)
.claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
