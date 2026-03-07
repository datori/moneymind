# Exploration: Mobile UX — Transactions, Accounts, Review Queue

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard.

### Current State of Focus Area

**finance/web/templates/transactions.html** — Transaction list with a multi-input
filter form (month nav, start/end dates, search, category, limit) using `flex flex-wrap`.
The data table has 6 columns (Date, Description, Merchant, Category, Account, Amount)
wrapped in `overflow-x-auto`. On mobile this forces horizontal scrolling — key columns
like Merchant and Account could be hidden on small screens via `hidden sm:table-cell`.

**finance/web/templates/accounts.html** — Accounts list with a bar chart (Transaction
Volume, last 13 months) and an 8-column table: Account Name, Institution, Type, Balance,
Txns, Date Range, Last Synced, Actions. Has `overflow-x-auto` but 8 columns is far too
wide for mobile. Institution, Date Range, and Last Synced are good candidates to hide
on small screens.

**finance/web/templates/review.html** — Review queue table with 7 columns: Date, Amount,
Description, Merchant, Category (inline select dropdown), Reason, Action (Approve button).
The form spans multiple columns (Category + Action). On mobile this is nearly unusable.
Should be refactored to a stacked card layout on small screens.

**finance/web/templates/recurring.html** — Recurring charges page with summary stat
cards (3-col grid, already `grid-cols-1 sm:grid-cols-3`), a spend timeline chart, and
multiple 8-column tables (Merchant, Interval, Typical, Times Seen, Total Spent, Next Due,
Status, Cancel). The header has filter toggle pills that wrap via `flex flex-wrap`.
Cancel column contains complex inline forms. Times Seen and Total Spent could be hidden
on mobile.

**finance/web/templates/index.html** — Dashboard with net worth cards (already responsive,
`grid-cols-1 sm:grid-cols-3`), spending section (recently improved with `flex-col md:flex-row`
stacking), credit utilization table (4 columns: Card, Balance, Limit, Utilization — manageable
on mobile), and recent pipeline runs table (4 columns: Status, Type, Started, Duration —
manageable but Started timestamp formatting could be improved for mobile).

**finance/web/templates/base.html** — Navigation with hamburger menu for mobile (already
implemented). Main content uses `max-w-7xl mx-auto px-4 py-6`.

**finance/web/templates/_macros.html** — Jinja2 macros for `category_badge(cat)`.

## Objective

Continue improving mobile UX and responsive design across the finance app. A previous
exploration loop (explore/mobile-responsive-2026-03-06) already improved spending,
recurring summary, report detail, and dashboard spending sections.

This loop focuses on the remaining high-impact pages:
- **Transactions** — hide less-critical columns on mobile, improve filter form layout
- **Accounts** — hide secondary columns on mobile
- **Review queue** — near-unusable on mobile; needs card layout or column hiding
- **Recurring** — hide secondary columns on mobile if not already done

This is intentionally open-ended. Use your judgment about what "better" means.
Focus on quality, clarity, correctness, and user experience — not quantity of changes.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- finance/web/templates/`
2. Read the files most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore(mobile-ux): <what changed and why in one line>`

## Tool Reliability Note

Deferred tools (Read, Edit, Grep) require a ToolSearch call to load before first
use each iteration. If a ToolSearch call appears to hang (no response after ~20
seconds), fall back to Bash equivalents: `cat` to read files, `python3 -c` or
`sed` for edits. The Bash tool is always available without loading. Prefer the
dedicated tools when they load normally — they are safer and more precise.

## In Scope

finance/web/templates/transactions.html
finance/web/templates/accounts.html
finance/web/templates/review.html
finance/web/templates/recurring.html
finance/web/templates/index.html
finance/web/templates/base.html
finance/web/templates/_macros.html

## Do Not Touch

finance/pipeline/
finance/db/
finance/web/app.py
finance/web/templates/spending.html
finance/web/templates/report_detail.html
finance/web/templates/net_worth.html
finance/web/templates/pipeline.html
finance/web/templates/reports.html
openspec/ (specs are written during archive, not during exploration)
.claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
