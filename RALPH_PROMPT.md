# Exploration: Increase Information Display Richness and Density

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard.

### Current State of Focus Area

**finance/web/templates/base.html**
Shared layout shell. Tailwind CSS via CDN, Chart.js via CDN. Navigation bar
with links to all pages. Mobile hamburger menu. Flash message display. Content
area is a `max-w-7xl mx-auto px-4 py-6` main element. No data-carrying logic.

**finance/web/templates/index.html**
Dashboard home. Shows: Net Worth summary cards (total, assets, liabilities),
Spending This Month table + doughnut chart by category, Credit Utilization
table per card with utilization %, and Recent Pipeline Runs table (status,
type, started, duration). Pipeline run timestamps are raw epoch ms integers,
not human-readable. Spending table has no category color badges. Utilization
has no progress bar visualization. Layout feels spacious with limited data
density.

**finance/web/templates/transactions.html**
Full transaction list with filter form (date range, month navigation, search,
category, limit). Table: Date, Description (hidden sm:), Merchant (hidden md:),
Category (badge), Account (hidden md:), Amount. Pending indicator is a small
dot. Showing count at bottom is plain text. No running total or summary strip.
No inline amount formatting with thousands separator. Category column always
shows a badge but table has no visual grouping or totals.

**finance/web/templates/accounts.html**
Lists all accounts with a transaction volume timeline chart (bar, 13 months).
Table: Account Name+mask, Institution (hidden sm:), Type (hidden sm:), Balance,
Txns count (hidden sm:), Date Range (hidden lg:), Last Synced (relative time,
hidden lg:), Actions. Global summary bar shows total accounts, transactions,
date range. Balances don't use thousands separator on larger amounts (uses
{:,.2f} but only when balance >= 0, negative branch lacks comma formatting).

**finance/web/templates/spending.html**
Spending breakdown page with date range filter, group-by (category/merchant/
account), and financial activity toggle. Summary strip shows total spent,
transaction count, group count, avg/day. Bar chart + table side by side.
Table has % of total with a progress bar per row. Category rows link to
filtered transaction view. Merchant rows link to search view.

**finance/web/templates/recurring.html**
Recurring charges page. Summary strip (monthly total, annual total, due-soon
count). Spend timeline chart (13 months actual + 3 projected). Three sections:
Needs Attention (past due / due any day / zombies), Active Subscriptions
(grouped by cadence: monthly/annual/etc), Likely Cancelled (collapsed). Each
row: Merchant (linked), Interval, Typical amount, Times Seen, Total Spent,
Next Due, Status badge, Cancel tracking cell. Status badges are color-coded
(red=past_due, blue=due_any_day, amber=due_soon, etc). Cancel tracking allows
logging attempt date + notes.

**finance/web/templates/review.html**
Review queue for flagged transactions. Simple table: Date, Amount, Description
(hidden md:), Merchant (hidden md:), Category (inline select), Review Reason
(hidden sm:), Approve button. Shows count at top and bottom. No grouping by
reason or category. No visual priority indicators.

**finance/web/templates/net_worth.html**
Just a Chart.js line chart of net worth over time. No summary stats, no
annotations, no delta indicators, no current value callout outside the chart.

**finance/web/templates/pipeline.html**
Shows current pipeline state (total txns, uncategorized count, recurring
count, needs review count) plus category breakdown table. Run Pipeline button
with streaming log output panel. Recent run history table. No cost information
displayed on recent runs, no trend indicators on the state cards.

**finance/web/templates/_macros.html**
`category_badge(cat)` macro — renders colored pill badges for each known
category (Food & Dining, Groceries, Transportation, Shopping, Entertainment,
Travel, Health & Fitness, Home & Utilities, Subscriptions & Software, Personal
Care, Education, Financial, Income, Investment, Other). Falls back to gray.

**finance/web/app.py**
FastAPI routes serving all pages. Provides template context data. Route
handlers compute net worth, credit utilization, spending summaries, account
overviews, recurring charges, pipeline runs, etc.

## Objective

Increase information display richness and density across the finance dashboard.
Make every view show more useful context at a glance — better use of space,
richer data in table rows, smarter summary lines, subtle inline indicators
where data exists, and tighter visual layout without sacrificing readability.

This is intentionally open-ended. Use your judgment about what "better" means.
Focus on quality, clarity, correctness, and user experience — not quantity of changes.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- finance/web/templates/ finance/web/app.py`
2. Read the files most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore(info-density): <what changed and why in one line>`

## Tool Reliability Note

Deferred tools (Read, Edit, Grep) require a ToolSearch call to load before first
use each iteration. If a ToolSearch call appears to hang (no response after ~20
seconds), fall back to Bash equivalents: `cat` to read files, `python3 -c` or
`sed` for edits. The Bash tool is always available without loading. Prefer the
dedicated tools when they load normally — they are safer and more precise.

## In Scope

finance/web/templates/index.html
finance/web/templates/transactions.html
finance/web/templates/accounts.html
finance/web/templates/recurring.html
finance/web/templates/spending.html
finance/web/templates/review.html
finance/web/templates/net_worth.html
finance/web/templates/pipeline.html
finance/web/templates/_macros.html
finance/web/templates/base.html
finance/web/app.py

## Do Not Touch

finance/pipeline/
finance/db/
finance/models.py
openspec/ (specs are written during archive, not during exploration)
.claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
