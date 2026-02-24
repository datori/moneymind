## Why

The dashboard is functional but visually flat — categories are plain text, Apple Card users cannot import CSV exports, and there is no way to remove stale accounts from the database. These three targeted improvements add visual clarity, broaden institution coverage, and close a data-management gap without touching core architecture.

## What Changes

- Category labels on the transactions and spending pages gain color-coded pill/badge styling using Tailwind CSS utility classes, making it faster to visually scan spending at a glance.
- A new `apple` normalizer is added to the CSV ingestion registry so Apple Card CSV exports can be imported with correct column mapping, merchant extraction, and debit-sign convention, while skipping card-payment rows.
- A new `finance accounts delete <account-id>` CLI command is added that cascades deletion of an account and all its associated rows (balances, transactions, sync_state, credit_limits), guarded by a confirmation step.

## Capabilities

### New Capabilities

- `category-color-badges`: Color-coded pill/badge display for all 15 transaction categories in the web dashboard (transactions view and spending view).
- `apple-card-csv`: Apple Card CSV normalizer registered under institution key `apple`, with correct column mapping, payment-row filtering, and amount-sign negation.
- `accounts-delete`: CLI command `finance accounts delete <account-id>` that deletes an account and all dependent rows, with confirmation guard.

### Modified Capabilities

- `web-dashboard`: Transactions page and spending page gain category badge rendering (visual enhancement, no new routes or data requirements).
- `csv-ingestion`: `apple` is added to the supported institutions table.
- `cli`: `finance accounts delete` subcommand added to the accounts group.

## Impact

- **Templates**: `finance/web/templates/transactions.html`, `finance/web/templates/spending.html` — add inline badge spans with Tailwind color classes.
- **Ingestion**: `finance/ingestion/csv_import.py` — add `apple` entry to `NORMALIZERS` dict.
- **CLI**: `finance/cli.py` — add `delete` subcommand under the `accounts` group.
- **Database**: Cascading deletes touch `balances`, `transactions`, `sync_state`, `credit_limits` for the target account; no schema changes required.
- **Dependencies**: No new packages; uses existing Click, SQLite, Jinja2, and Tailwind CDN.
