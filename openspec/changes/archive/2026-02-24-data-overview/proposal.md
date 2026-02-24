## Why

When mixing SimpleFIN (90-day rolling window) with CSV imports (potentially years of history), there is no way to see what transaction data is actually stored — how many transactions, which date range, or how fresh each account's data is. This makes it hard to trust the data or diagnose gaps.

## What Changes

- New `finance/analysis/overview.py` module with `get_data_overview(conn)` returning global and per-account coverage stats
- New `GET /data` web route that displays a "Data" page with a global summary header and per-account coverage table
- Enhanced `/accounts` page: existing balance table kept at top; new "Data Coverage" section added below showing per-account transaction count, date range, and last sync time
- New `finance data` CLI command printing global summary and per-account coverage table

## Capabilities

### New Capabilities

- `data-overview`: Analysis function and UI surfaces for inspecting stored transaction data coverage (global stats + per-account breakdown of transaction count, date range, and last sync time)

### Modified Capabilities

- `web-dashboard`: The `/accounts` route gains a "Data Coverage" section and a new `/data` route is added
- `cli`: A new `data` subcommand is added to the CLI

## Impact

- **New file**: `finance/analysis/overview.py`
- **Modified file**: `finance/web/templates/accounts.html` (add Data Coverage section)
- **New file**: `finance/web/templates/data.html` (new Data page)
- **Modified file**: `finance/cli.py` (add `data` command)
- **Modified file**: `finance/web/app.py` (add `/data` route; update `/accounts` route to pass overview data)
- No new dependencies, no schema changes, no breaking API changes
