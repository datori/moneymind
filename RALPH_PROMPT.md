# Exploration: Enhance and Add Visualizations

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard.

### Current State of Focus Area

**finance/web/templates/index.html** — Dashboard home page. Shows three net worth
summary cards (total, assets, liabilities), a spending-this-month section with a
table and a doughnut Chart.js chart, a credit utilization section with a table and
inline progress bars, and a recent pipeline runs table. Chart uses hsl palette.

**finance/web/templates/spending.html** — Spending breakdown page with date range
picker (month nav + explicit dates), group_by selector (category/merchant/account),
and include_financial toggle. Shows a Chart.js bar chart (horizontal when >8 labels)
and a data table with % of total mini progress bars. Summary strip shows totals and
avg/day. Chart uses hsl color palette from chart_data_json passed by the server.

**finance/web/templates/net_worth.html** — Net worth history page. Single filled
line chart (Chart.js) showing daily net worth over time. Summary strip shows current
value, period-start value, and change with sign/color. Labels are YYYY-MM-DD, y-axis
formatted as compact dollars, tooltip shows full dollar value.

**finance/web/templates/recurring.html** — Recurring charges page. Stacked bar chart
with actual past spend per merchant, a "ghost" overlay for missed expected charges,
and projected future bars at 40% opacity. Today-index divider annotation. Summary
stats: monthly total, annual total, pending cancels, projected next month.

**finance/web/templates/accounts.html** — Accounts page. Has a credit utilization
panel with aggregate progress bar and per-card mini bars. Has a transaction timeline
stacked bar chart (Chart.js) showing transaction counts per account per month.
Account list table with type badges, balances, data coverage dates.

**finance/web/templates/transactions.html** — Transaction browser with date/category/
search/sort filters and a paginated table. No chart currently.

**finance/web/templates/_macros.html** — Jinja2 macros. Defines `category_badge(cat)`
which renders a colored pill badge for a category name.

**finance/web/app.py** — FastAPI routes. Key routes: `/` (index), `/spending`,
`/net-worth`, `/recurring`, `/accounts`, `/transactions`, `/pipeline`. Passes
chart_data_json (spending, net_worth) and spend_chart_json (recurring) to templates.
The spending route computes labels+values and avg_per_day. The net_worth route
aggregates daily balance history into chart_data_json with labels+values arrays.

**finance/analysis/spending.py** — get_spending_summary(conn, start_date, end_date,
group_by, exclude_categories) returns list of {label, total, count}. get_transactions()
returns filtered transaction rows.

**finance/analysis/net_worth.py** — get_balance_history(conn) returns raw balance
rows with account_id, timestamp (unix ms), balance. get_net_worth(conn) returns
{total, assets, liabilities, as_of}.

**finance/analysis/accounts.py** — get_accounts(conn) returns account rows.
get_credit_utilization(conn) returns utilization data. get_transaction_timeline(conn,
account_id) returns {months, accounts: [{name, counts}]} for stacked bar chart.

**finance/analysis/review.py** — get_recurring(conn) returns recurring charge records
with status, interval_days, typical_amount, cancel_attempt. get_recurring_spend_timeline()
returns {months, future_months, merchants: [{name, actual, ghost, projected}]}.

## Objective

Enhance existing charts and add new visualizations across the finance dashboard.
Current charts: doughnut (index), bar (spending), line (net_worth), stacked bar
(recurring), stacked bar (accounts). Opportunities include: adding chart annotations,
improving tooltip content, adding trend context, adding charts to pages that lack
them, improving color consistency, adding month-over-month comparison, or any other
meaningful visualization improvement that helps a user understand their finances better.

This is intentionally open-ended. Use your judgment about what "better" means.
Focus on quality, clarity, correctness, and user experience — not quantity of changes.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- finance/web/templates/ finance/web/app.py finance/analysis/`
2. Read the files most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore(viz-enhancements): <what changed and why in one line>`

## Tool Reliability Note

Deferred tools (Read, Edit, Grep) require a ToolSearch call to load before first
use each iteration. If a ToolSearch call appears to hang (no response after ~20
seconds), fall back to Bash equivalents: `cat` to read files, `python3 -c` or
`sed` for edits. The Bash tool is always available without loading. Prefer the
dedicated tools when they load normally — they are safer and more precise.

## In Scope

finance/web/templates/index.html
finance/web/templates/spending.html
finance/web/templates/net_worth.html
finance/web/templates/recurring.html
finance/web/templates/accounts.html
finance/web/templates/transactions.html
finance/web/templates/_macros.html
finance/web/app.py
finance/analysis/spending.py
finance/analysis/net_worth.py
finance/analysis/accounts.py
finance/analysis/review.py

## Do Not Touch

finance/pipeline/
finance/ingestion/
finance/db/
finance/ai/
- openspec/ (specs are written during archive, not during exploration)
- .claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
