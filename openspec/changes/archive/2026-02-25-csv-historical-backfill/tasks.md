## 0. Normalizer Fixes

- [x] 0.1 Fix `normalize_amex()` in `finance/ingestion/csv_import.py` to negate the amount (Amex exports positive = charge; must store as negative to match canonical convention)
- [x] 0.2 Add `normalize_capital_one()` normalizer: uses `Transaction Date` (YYYY-MM-DD) + separate `Debit`/`Credit` columns, same sign logic as Citi
- [x] 0.3 Register `"capital-one"` in the `NORMALIZERS` dict

## 1. Core Import Logic

- [x] 1.1 Add `before_date: str | None` parameter to `import_csv()` in `finance/ingestion/csv_import.py`
- [x] 1.2 Skip rows where the normalised transaction date `>= before_date` when `before_date` is set; increment a `rows_cutoff` counter for skipped rows
- [x] 1.3 Add `rows_cutoff` key to the dict returned by `import_csv()`

## 2. CLI Integration

- [x] 2.1 Add `--before` option (type `str`, optional) to the `import csv` subcommand in `finance/cli.py`
- [x] 2.2 When `--before` is not provided and an `account_id` is resolved, query `MIN(date) FROM transactions WHERE account_id = ? AND source = 'simplefin'` to auto-detect the cutoff
- [x] 2.3 Print the detected cutoff to stdout before import begins (e.g. `"Auto-detected cutoff: 2024-11-01 (earliest SimpleFIN transaction)"`)
- [x] 2.4 Validate `--before` value is a valid `YYYY-MM-DD` date; print a clear error and exit non-zero if not
- [x] 2.5 Update the import summary output to include `rows_cutoff` (label: `"rows before cutoff"` or similar)
