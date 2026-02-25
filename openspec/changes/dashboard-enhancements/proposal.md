## Why

Browsing spending history and transactions is friction-heavy: navigating between months requires manually editing date fields, clicking a spending category has no drill-down, and the recurring charges page is too sparse to act as a subscription health tracker. These enhancements make the daily-use loop faster and the recurring page genuinely actionable.

## What Changes

- **Month navigation**: Add prev/next month buttons to the spending and transactions filter bars so users can browse history without touching date inputs.
- **Spending → Transactions drill-down**: Each category row in the spending table becomes a link to `/transactions` pre-filtered by that category and date range, sorted by amount descending.
- **Transaction sorting**: Add `sort_by` parameter (date or amount) to the transactions page; column headers become sort toggles.
- **Transaction text search**: Add a search input on the transactions page that filters by description, merchant name, or normalized merchant name (LIKE match).
- **Richer recurring charges**: Extend `get_recurring()` to compute interval (from median gap between charges), next expected charge date, days until next, status (upcoming / due soon / past due), and total spent. The page sorts by urgency and color-codes status so users can immediately spot potentially-canceled subscriptions.

## Capabilities

### New Capabilities

- `month-navigation`: Prev/next month buttons (JS-only) on spending and transactions filter bars; no backend change.
- `transaction-sorting`: `sort_by` + `sort_dir` query params on `/transactions`; `get_transactions()` switches `ORDER BY` accordingly. Column headers render as sort-toggle links.
- `transaction-search`: `search` query param on `/transactions`; `get_transactions()` adds `LIKE` filter across description, merchant_name, merchant_normalized.

### Modified Capabilities

- `web-dashboard`: Spending table rows link to `/transactions` drill-down with category + date range pre-filled.
- `transaction-filter`: Transactions filter bar gains search input and sort controls alongside existing date/limit/category fields.
- `recurring-detection`: `get_recurring()` extended to return `last_date`, `interval_days`, `interval_label`, `next_due_date`, `days_until_next`, `status`, and `total_spent`. Page sorted by urgency (past due first), status color-coded.

## Impact

- `finance/analysis/spending.py`: `get_transactions()` gains `sort_by`, `sort_dir`, `search` params.
- `finance/analysis/review.py`: `get_recurring()` rewritten to return richer derived fields.
- `finance/web/app.py`: `/transactions` route passes new params; `/recurring` route passes enriched data.
- `finance/web/templates/transactions.html`: Search input, sort controls, column header links.
- `finance/web/templates/spending.html`: Month nav buttons (JS); category rows become links.
- `finance/web/templates/recurring.html`: Expanded table with interval, total, status columns.
- No schema changes; no new dependencies.
