## Context

The accounts page currently shows a static table with per-account summary stats (transaction count, date range). There is no way to see how transaction activity is distributed over time or which accounts are driving activity in a given period.

Chart.js is already a dependency (used in net-worth and spending pages). The analysis layer uses pure query functions returning plain dicts. The `/accounts` route currently calls `get_data_overview()` and `get_accounts()`.

## Goals / Non-Goals

**Goals:**
- Add a stacked bar chart to the accounts page showing monthly transaction counts per account, color-coded
- Default view: all accounts, past 13 calendar months (guarantees at least a year of data visible)
- Account selector to filter chart to a single account
- No new JS dependencies; use existing Chart.js CDN already referenced in templates

**Non-Goals:**
- Custom date range selection for the chart (always 13 months back from today)
- Showing transaction amounts (dollars) — count only keeps it simple and useful
- Saving the selected account across sessions (URL param is sufficient)

## Decisions

### Monthly granularity
13 months of data at monthly resolution gives one bar per month — readable and shows seasonal patterns. Daily granularity would produce ~400 bars (too dense). Weekly produces ~57 bars (workable but noisier). Monthly is the right default for "at least a year at a time."

### Server-side aggregation in `get_transaction_timeline()`
The chart data is pre-aggregated in Python/SQLite rather than sending raw transaction rows to the client. Consistent with the existing pattern (analysis layer returns plain dicts). The query groups by `strftime('%Y-%m', date)` and `account_id`; Python fills zero-count months to guarantee all 13 months appear for every account.

Alternative considered: client-side aggregation from a `/api/transactions` endpoint. Rejected — introduces a new API pattern for one page, no benefit.

### Account filter via URL query param
`GET /accounts?account_id=<id>` persists the selection in the URL. The template renders a `<select>` form that POSTs to the same page via GET redirect. Simple, bookmarkable, no JS state management needed.

Alternative: JavaScript-only chart filter with no page reload. Rejected — adds client-side state management and requires the full multi-account dataset to be embedded in the page even when not needed.

### Color palette assignment
A fixed 10-color palette is assigned deterministically by account sort order (alphabetical by name). Accounts always get the same color on the same installation. Uses Tailwind-friendly hex values consistent with the dashboard color scheme.

Alternative: Random or hash-based colors. Rejected — unpredictable, may clash.

### Stacked bars (all-accounts view) vs grouped bars
Stacked bars show total volume and per-account contribution simultaneously. Grouped bars with many accounts become crowded. When a single account is selected, the chart switches to a single-dataset (non-stacked) bar for clarity.

## Risks / Trade-offs

- **Sparse data** → months with very few transactions produce tiny bar segments. Mitigation: chart tooltips show exact counts; the zero-fill ensures no month is skipped.
- **Many accounts** → legend becomes crowded with 8+ accounts. Mitigation: acceptable for a personal finance tool with typically 3-8 accounts; no action needed.
- **SQLite date storage** → transactions store dates as `YYYY-MM-DD` strings; `strftime('%Y-%m', date)` is reliable. No risk.
- **First-boot with no data** → chart renders as empty/blank. Mitigation: show a placeholder message when no timeline data is available.
