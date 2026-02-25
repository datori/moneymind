## Context

The dashboard is a server-side rendered FastAPI + Jinja2 application. All state lives in URL query parameters; there is no client-side state management or AJAX. Filter forms use `method="get"`, making browser back/forward and bookmarking work naturally.

Current gaps: spending and transactions pages require manual date-field editing to browse months, no path from a spending category to its constituent transactions, transactions are only sortable by date, no text search exists, and the recurring page shows only merchant/count/typical-amount with no temporal intelligence.

## Goals / Non-Goals

**Goals:**
- Month prev/next navigation on spending and transactions pages (pure JS, zero backend cost)
- Spending → transactions drill-down via linked category rows
- Sort by amount (or date) on transactions, controlled via URL params
- Text search on transactions (description + merchant_name + merchant_normalized LIKE)
- Enriched recurring: interval detection, next-due date, status (upcoming/due soon/past due), lifetime total — all derived from existing transaction data, no schema changes

**Non-Goals:**
- Persistent user preferences (cookies, server-side sessions)
- Month-over-month comparison columns
- Budget targets or spending alerts
- CSV export
- Inline category editing from transactions table

## Decisions

### 1. Month navigation as pure JS (no round-trip)

The prev/next buttons compute the first and last day of the adjacent month in JS, update the `start` and `end` hidden inputs, and submit the form. No new backend route or parameter is needed. The form already accepts arbitrary `start`/`end` values.

Alternative considered: server-side redirect via dedicated `/spending/prev-month` route. Rejected — adds backend complexity for zero gain when JS is sufficient.

### 2. Sort controls via URL query params (`sort_by`, `sort_dir`)

`get_transactions()` gains two optional params: `sort_by: str` (values: `"date"` | `"amount"`, default `"date"`) and `sort_dir: str` (values: `"asc"` | `"desc"`, default `"desc"`). The SQL `ORDER BY` clause is constructed from a safe allowlist lookup — no raw string interpolation of user input.

Column headers in the template render as `<a>` links that toggle sort direction. Active sort column shows an arrow indicator.

Alternative considered: client-side JS sort on the rendered table. Rejected — doesn't work well with the `limit` parameter (only sorts visible rows, not the full dataset).

### 3. Text search as LIKE filter (three columns)

`get_transactions()` gains `search: str | None`. When present, appends:
```sql
AND (t.description LIKE ? OR t.merchant_name LIKE ? OR t.merchant_normalized LIKE ?)
```
with `%search%` as the bound value for all three. Case-insensitive by default (SQLite LIKE is case-insensitive for ASCII).

Alternative considered: FTS5 full-text search index. Rejected — overkill for a personal tool with < 100k transactions; LIKE is fast enough at this scale on SQLite.

### 4. Spending drill-down as plain `<a>` links (no HTMX, no modal)

Each row `<tr>` in the spending table becomes a clickable `<a>` wrapping the label cell. The link is:
```
/transactions?start={start}&end={end}&category={label}&sort_by=amount&sort_dir=desc
```
Navigation is full-page, consistent with the app's server-rendered model. The transactions page receives `category` pre-selected and amount-sorted, showing that category's breakdown for the same period.

When `group_by=merchant`, the link passes `search={label}` instead of `category={label}` (since merchant is not a structured filter field). When `group_by=account`, no drill-down link is added (account is already a separate filter, less useful for drill-down).

### 5. Recurring enrichment: Python-side interval inference

`get_recurring()` is rewritten. The SQL query is extended to also return `date` for each transaction. Python post-processes per merchant:

1. Sort dates ascending.
2. Compute gaps (days) between consecutive charges.
3. Median gap → `interval_days`.
4. Classify into label: Weekly (5–9d), Bi-weekly (13–17d), Monthly (25–35d), Quarterly (85–95d), Semi-annual (175–190d), Annual (355–375d), else `"Every ~{n}d"`.
5. `next_due_date = last_date + timedelta(days=interval_days)`.
6. `days_until_next = (next_due_date - date.today()).days`.
7. Tolerance = `interval_days * 0.35` (rounds to int, min 3).
8. Status:
   - `days_until_next > 7` → `"upcoming"`
   - `1 <= days_until_next <= 7` → `"due_soon"`
   - `-tolerance <= days_until_next <= 0` → `"due_any_day"` (processing lag)
   - `days_until_next < -tolerance` → `"past_due"`
9. `total_spent = sum(abs(amount) for all charges)`.

If only one charge exists (`len(dates) < 2`), interval/next-due/status are `None`; the template shows `—`.

The page sorts: past_due first, then due_soon, then due_any_day, then upcoming (by days_until_next ascending), then unknown (no interval).

### 6. No schema changes

All new fields are derived at query/analysis time. The `is_recurring` flag on transactions is the sole source of truth for recurring detection, consistent with existing pipeline behavior.

## Risks / Trade-offs

- **Interval inference is heuristic**: Charges with irregular timing (e.g., quarterly billing on a variable day) may compute a noisy median gap and show inaccurate next-due dates. Mitigation: display the computed interval label so the user can sanity-check it.
- **LIKE search is case-insensitive for ASCII only**: Non-ASCII characters in merchant names use SQLite's default case-sensitive LIKE. Acceptable for a personal tool; all practical merchant names are ASCII.
- **Drill-down by merchant uses search, not exact match**: When `group_by=merchant`, the drill-down link uses `search={label}` which is a LIKE match. Results may include near-matches. Acceptable given the exploratory nature of the drill-down.
- **Sort direction toggle state in HTML**: Column headers need to know the current sort to toggle direction. Passed from the route handler as template context variables (`current_sort_by`, `current_sort_dir`).

## Migration Plan

No data migration required. Changes are additive:
1. Update `get_transactions()` — backward-compatible (new params are optional with defaults).
2. Update `get_recurring()` — return dict gains new keys; template updated simultaneously.
3. Deploy is a simple restart of the dev server.
