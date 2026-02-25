## Why

The current dashboard has redundant pages (`/accounts` and `/data` cover ~70% of the same ground), no way to delete accounts from the browser, and a transactions page with no category filtering. Adding a category exclusion toggle to the spending view closes the gap where Financial/Income/Investment activity inflates apparent spending figures. These four focused changes tighten the UI surface and make daily use faster without touching the data model or core analysis layer.

## What Changes

- `/accounts` and `/data` pages merge into a single unified `/accounts` page with a global summary bar and a rich per-account table; `/data` redirects 301 to `/accounts` and its nav link is removed.
- Each account row on `/accounts` gains a [Delete] button with an inline confirmation that shows the transaction and balance counts before committing a cascading `POST /accounts/{id}/delete`.
- The `/transactions` filter bar gains a category dropdown (all 15 canonical categories + "All Categories") backed by the already-present `category` parameter on `get_transactions()`.
- The `/spending` page gains an "Include Financial Activity" toggle; when off (default), `get_spending_summary()` excludes Financial, Income, and Investment transactions.

## Capabilities

### New Capabilities

- `account-web-delete`: Delete an account and all its dependent rows from the web UI, with inline confirmation showing impact counts, via `POST /accounts/{id}/delete`.
- `transaction-filter`: Category dropdown on the `/transactions` filter bar, backed by the `?category=` URL param and the existing `category` argument on `get_transactions()`.

### Modified Capabilities

- `web-dashboard`: `/accounts` becomes the unified accounts + data coverage page; `/data` redirects to `/accounts`; nav "Data" link removed; `/spending` gains the `?include_financial=1` URL param and "Include Financial Activity" toggle.
- `data-overview`: `get_data_overview()` is unchanged; it is now called by `/accounts` instead of `/data`; the `/data` route is deprecated (redirect).

## Impact

- **Routes**: `finance/web/app.py` — `/accounts` route expanded, `/data` route converted to redirect, new `POST /accounts/{id}/delete` route, `/transactions` route gains `category` param, `/spending` route gains `include_financial` param.
- **Analysis**: `finance/analysis/spending.py` — `get_spending_summary()` gains `exclude_categories` parameter (defaults to `['Financial', 'Income', 'Investment']` when spending filter is active).
- **Templates**: `finance/web/templates/accounts.html` — rewritten to unified page with global summary bar, merged per-account table with balance + txn columns, and inline delete confirmation UI.
- **Templates**: `finance/web/templates/transactions.html` — category dropdown added to filter form.
- **Templates**: `finance/web/templates/spending.html` — "Include Financial Activity" checkbox toggle added to filter form.
- **Nav**: `finance/web/templates/base.html` — "Data" nav link removed.
- **Database**: No schema changes. Cascade delete touches `credit_limits`, `sync_state`, `transactions`, `balances`, `accounts` for the deleted account.
- **Dependencies**: No new packages.
