# Exploration: Improve the Spending View

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard.

### Current State of Focus Area

**finance/web/templates/spending.html** — The main spending breakdown page.
Contains a filter form (date range, month nav buttons, group_by select,
include_financial checkbox), a Chart.js bar chart, and a summary table.
Chart flips to horizontal axis when >8 items. Table rows link to filtered
transactions for category and merchant views. Month navigation submits the
form automatically via JS.

**finance/analysis/spending.py** — Two analysis functions:
- `get_transactions()`: Returns filtered transactions with date, amount,
  description, merchant, category, account fields. Supports search, sort,
  and limit.
- `get_spending_summary()`: Aggregates debit transactions (amount < 0) by
  category, merchant, or account. Returns list of {label, total, count}
  sorted by total descending.

**finance/web/app.py** — FastAPI routes. The /spending route (lines 326-368)
calls get_spending_summary() with the chosen filters, builds chart_data_json
(labels + values arrays), and passes spending rows + filter state to the
template. Also contains _current_month_range() helper at lines 75-79.

**finance/web/templates/_macros.html** — Defines the category_badge(cat)
macro used throughout the app to render colored pill badges for categories
(indigo primary accent color, Tailwind CSS).

## Objective

Improve the /spending page — the breakdown chart and table showing expenses
grouped by category, merchant, or account. Focus on UX clarity, data density,
and visual quality. Make it more useful and informative without over-engineering.

This is intentionally open-ended. Use your judgment about what "better" means.
Focus on quality, clarity, correctness, and user experience — not quantity of changes.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- finance/web/templates/spending.html finance/analysis/spending.py finance/web/app.py finance/web/templates/_macros.html`
2. Read the files most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore(spending-view): <what changed and why in one line>`

## Tool Reliability Note

Deferred tools (Read, Edit, Grep) require a ToolSearch call to load before first
use each iteration. If a ToolSearch call appears to hang (no response after ~20
seconds), fall back to Bash equivalents: `cat` to read files, `python3 -c` or
`sed` for edits. The Bash tool is always available without loading. Prefer the
dedicated tools when they load normally — they are safer and more precise.

## In Scope

finance/web/templates/spending.html
finance/web/templates/_macros.html
finance/analysis/spending.py
finance/web/app.py

## Do Not Touch

finance/pipeline/
finance/ingestion/
finance/db/
finance/web/templates/base.html
finance/web/templates/transactions.html
finance/web/templates/recurring.html
openspec/ (specs are written during archive, not during exploration)
.claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
