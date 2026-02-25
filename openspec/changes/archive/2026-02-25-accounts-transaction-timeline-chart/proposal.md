## Why

The accounts page shows a static snapshot — total transaction counts and date ranges — but gives no sense of transaction activity over time. There's no way to see which accounts are most active, how usage has shifted, or what the distribution of transactions looks like across accounts historically.

## What Changes

- Add `get_transaction_timeline()` analysis function returning monthly transaction counts grouped by account
- Add a stacked bar chart to the accounts page showing monthly transaction volume per account (color-coded per account)
- Default view spans the past 13 months (at least a year of history)
- Add an account selector so the user can filter the chart to a single account
- The `/accounts` route gains an optional `account_id` query parameter to persist the selection

## Capabilities

### New Capabilities
- `accounts-transaction-timeline`: Analysis function that returns monthly transaction counts per account, supporting optional single-account filtering

### Modified Capabilities
- `web-dashboard`: The accounts page gains a transaction timeline chart section with an account selector

## Impact

- `finance/analysis/accounts.py` — new `get_transaction_timeline()` function
- `finance/web/app.py` — `/accounts` route calls new function, passes chart data JSON
- `finance/web/templates/accounts.html` — new chart + account selector UI, Chart.js (already a dependency)
