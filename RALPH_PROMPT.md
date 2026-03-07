# Exploration: Improve the Accounts Page

## Project Context

This is a personal finance application — Python/FastAPI/SQLite. It syncs
transactions from SimpleFin and CSV imports, AI-categorizes them, tracks
recurring charges, and provides a web dashboard.

### Current State of Focus Area

**finance/web/templates/accounts.html** — The main accounts page template. Shows:
- A global summary bar with total account count, transaction count, and date range
- A Transaction Volume bar chart (last 13 months, filterable by account) using Chart.js
- A table of accounts with: name/mask, institution, type, balance, txn count, date range,
  last synced, and a delete action with confirmation UI
- JS at the bottom for chart rendering, date range formatting, and relative time display

**finance/web/app.py** (accounts_page route, ~lines 130-204) — Assembles data:
- Calls `get_accounts()`, `get_data_overview()`, `get_transaction_timeline()`
- Builds `merged_accounts` enriching each account with txn_count, earliest/latest txn
  dates, last_synced_at, and balance_count
- Builds Chart.js dataset from timeline data with an indigo/amber/green palette
- Passes: accounts, overview, msg, chart_data_json, has_chart_data, selected_account_id

**finance/analysis/accounts.py** — Analysis functions:
- `get_accounts()`: returns active accounts with latest balance snapshot; fields include
  id, name, type, institution, balance, available, currency, mask, last_updated
- `get_account_by_id()`: same for single account
- `get_transaction_timeline()`: monthly transaction counts per active account, 13 months
- `get_credit_utilization()`: per-card and aggregate credit utilization; joins
  credit_limits table; returns aggregate_pct, total_balance, total_limit, and cards list
  with utilization_pct per card

**finance/web/templates/_macros.html** — Shared macros:
- `category_badge(cat)`: renders a colored pill badge for a transaction category

## Objective

Improve the accounts page — better information density, UX polish, visual clarity,
and any missing useful data (e.g. credit utilization, available balance display, net
balance summary, type-based visual cues).

This is intentionally open-ended. Use your judgment about what "better" means.
Focus on quality, clarity, correctness, and user experience — not quantity of changes.

## Per-Iteration Protocol

Before making any change:
1. Run: `git log --oneline -8 -- finance/web/templates/accounts.html finance/web/app.py finance/analysis/accounts.py finance/web/templates/_macros.html`
2. Read the files most relevant to the next improvement
3. Identify ONE specific, concrete improvement that has not already been made
4. If you genuinely cannot identify a meaningful improvement, output the stop signal

Making the change:
- Implement cleanly — one focused change per iteration
- Do not touch files outside the scope listed below
- Do not re-implement or undo something a previous iteration already did

After the change:
- Commit with: `explore(accounts-page): <what changed and why in one line>`

## Tool Reliability Note

Deferred tools (Read, Edit, Grep) require a ToolSearch call to load before first
use each iteration. If a ToolSearch call appears to hang (no response after ~20
seconds), fall back to Bash equivalents: `cat` to read files, `python3 -c` or
`sed` for edits. The Bash tool is always available without loading. Prefer the
dedicated tools when they load normally — they are safer and more precise.

## In Scope

finance/web/templates/accounts.html
finance/web/app.py
finance/web/templates/_macros.html
finance/analysis/accounts.py

## Do Not Touch

finance/db/
finance/pipeline/
finance/analysis/net_worth.py
finance/analysis/spending.py
finance/analysis/overview.py
finance/analysis/review.py
openspec/ (specs are written during archive, not during exploration)
.claude/ (skill and config files)

## Stop When

You cannot identify a further meaningful, non-trivial improvement within the
scope that hasn't already been made in a previous iteration.

Output exactly:
<promise>EXPLORATION COMPLETE</promise>
