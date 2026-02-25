## Why

SimpleFIN Bridge only provides ~90 days of transaction history, but banks can export years of data via CSV. When doing a one-time historical backfill for a SimpleFIN-linked account, the overlap window (the last 90 days that SimpleFIN already covers) would create duplicate transaction rows because SimpleFIN uses bank-assigned IDs while CSV uses content-hash IDs — they never collide, so `INSERT OR IGNORE` alone cannot prevent duplicates.

## What Changes

- `finance import csv` gains a `--before DATE` option that restricts import to transactions strictly before the given date
- When `--before` is omitted and the target account has existing SimpleFIN transactions, the cutoff is auto-detected as `MIN(date)` of those transactions
- When no SimpleFIN transactions exist for the account, all rows are imported (pure historical / CSV-only account)
- The import summary gains a `rows_before_cutoff` field showing how many rows were skipped due to the date cutoff

## Capabilities

### New Capabilities

_(none — this extends an existing capability)_

### Modified Capabilities

- `csv-ingestion`: Adding `--before DATE` option to the import command and auto-detect logic to prevent duplicate transactions during historical backfill

## Impact

- `finance/ingestion/csv_import.py`: `import_csv()` gains a `before_date: str | None` parameter; rows with `date >= before_date` are skipped
- `finance/cli.py`: `import csv` subcommand gains `--before` option; auto-detection queries `transactions` table when flag is omitted
- No schema changes required
- No breaking changes to existing behavior (no `--before` = auto-detect, falling back to import-all for CSV-only accounts)
