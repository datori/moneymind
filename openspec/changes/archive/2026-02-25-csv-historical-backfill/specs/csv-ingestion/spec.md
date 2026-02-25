## MODIFIED Requirements

### Requirement: CSV import command
The system SHALL provide a `finance import <file>` CLI command that imports transactions from a CSV file into the database.

The command SHALL accept an optional `--before DATE` flag (ISO format `YYYY-MM-DD`) to restrict imported rows to transactions strictly before that date. When `--before` is not provided and the target account has existing SimpleFIN transactions, the system SHALL auto-detect the cutoff as the earliest SimpleFIN transaction date for that account.

#### Scenario: Basic import with institution flag
- **WHEN** `finance import chase_jan2025.csv --institution chase --account <id>` is run
- **THEN** transactions from the file are parsed and upserted into the `transactions` table

#### Scenario: Import summary printed
- **WHEN** `finance import ...` completes
- **THEN** stdout shows: rows read, rows imported, rows skipped (duplicates or filtered by cutoff)

#### Scenario: Unknown institution
- **WHEN** `finance import file.csv --institution unknown-bank` is run
- **THEN** an error is printed listing valid institution names and the command exits non-zero

---

## ADDED Requirements

### Requirement: Historical backfill date cutoff
The system SHALL support a `--before DATE` option on `finance import` to prevent importing transactions that overlap with existing SimpleFIN coverage, avoiding cross-source duplicate rows.

#### Scenario: Explicit --before flag filters rows
- **WHEN** `finance import history.csv --institution chase --account <id> --before 2024-11-01` is run
- **THEN** only rows with a transaction date strictly before `2024-11-01` are imported
- **AND** rows on or after `2024-11-01` are counted as skipped in the summary

#### Scenario: Auto-detect cutoff from SimpleFIN transactions
- **WHEN** `finance import history.csv --institution chase --account <id>` is run with no `--before` flag
- **AND** the account has at least one transaction with `source = 'simplefin'`
- **THEN** the cutoff is automatically set to `MIN(date)` of the account's SimpleFIN transactions
- **AND** the detected cutoff date is printed to stdout before import begins

#### Scenario: No cutoff when account is CSV-only
- **WHEN** `finance import history.csv --institution chase --account <id>` is run with no `--before` flag
- **AND** the account has no transactions with `source = 'simplefin'`
- **THEN** all rows are imported with no date filtering applied

#### Scenario: --before overrides auto-detection
- **WHEN** `finance import history.csv --institution chase --account <id> --before 2023-01-01` is run
- **AND** the account has SimpleFIN transactions with an earlier MIN date
- **THEN** the explicitly provided `2023-01-01` cutoff is used, not the auto-detected one

#### Scenario: Invalid --before date format
- **WHEN** `finance import history.csv --institution chase --account <id> --before not-a-date` is run
- **THEN** an error is printed indicating the expected format (`YYYY-MM-DD`) and the command exits non-zero
