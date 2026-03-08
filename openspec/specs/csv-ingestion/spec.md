## ADDED Requirements

### Requirement: CSV import does not trigger LLM calls
The `import_csv()` function SHALL import transactions from a CSV file into the database without triggering any LLM categorization or enrichment calls. Auto-categorization is removed from the import path.

#### Scenario: CSV import with ANTHROPIC_API_KEY set
- **WHEN** `finance import` is run with `ANTHROPIC_API_KEY` set in environment
- **THEN** transactions are imported from the CSV file
- **AND** no LLM API calls are made
- **AND** imported transactions have `category = NULL` and `categorized_at = NULL`

#### Scenario: CSV import without ANTHROPIC_API_KEY
- **WHEN** `finance import` is run without `ANTHROPIC_API_KEY` set
- **THEN** transactions are imported normally (same behavior as with key set)

---

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

### Requirement: Institution listing command
The system SHALL provide a `finance institutions` command listing all supported CSV institution names.

#### Scenario: Lists all normalizers
- **WHEN** `finance institutions` is run
- **THEN** each supported institution name is printed (one per line)

---

### Requirement: Transaction deduplication via hash ID
CSV-imported transactions SHALL use a deterministic hash-based ID for deduplication.

ID formula: `sha256("{account_id}|{date}|{amount}|{description}".encode()).hexdigest()[:16]`

#### Scenario: Re-importing same file
- **WHEN** the same CSV file is imported twice
- **THEN** the second import inserts 0 new transactions (all skipped as duplicates)

---

### Requirement: Supported institution normalizers
The system SHALL support the following institutions with correct column mapping and amount sign normalization.

| Institution | Key | Amount sign rule |
|-------------|-----|-----------------|
| Chase | `chase` | Amount column; negative = debit |
| Discover (credit) | `discover` | Amount column; negative = debit |
| Discover (debit) | `discover-debit` | Amount column; negative = debit |
| Citi | `citi` | Separate Debit/Credit cols; debit = negative |
| Capital One | `capital-one` | Separate Debit/Credit cols (`Transaction Date` column); debit = negative |
| Amex | `amex` | Amount column; positive = charge → negate to debit; negative = payment → negate to positive |
| Robinhood | `robinhood` | Amount column; buys = negative |
| M1 | `m1` | Amount column; buys = negative |
| Apple Card | `apple` | `Amount (USD)` column; positive = charge → negate to debit; skip Type=="Payment" rows |

#### Scenario: Citi Debit/Credit column merge
- **WHEN** a Citi CSV row has a value in the `Debit` column
- **THEN** the stored amount is `-(abs(debit_value))`

#### Scenario: Citi credit row
- **WHEN** a Citi CSV row has a value in the `Credit` column
- **THEN** the stored amount is `+abs(credit_value)`

#### Scenario: Apple Card purchase row
- **WHEN** an Apple Card CSV row has `Type` other than `"Payment"` and `Amount (USD)` of `"45.99"`
- **THEN** the stored amount is `-45.99` and `merchant_name` is populated from the `Merchant` column

#### Scenario: Apple Card payment row skipped
- **WHEN** an Apple Card CSV row has `Type == "Payment"`
- **THEN** the row is skipped and not inserted into the database

---

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

---

### Requirement: Account auto-creation
The system SHALL auto-create an account record if `--account` is not provided and no matching account exists.

#### Scenario: New account auto-created
- **WHEN** `finance import file.csv --institution chase` is run with no `--account` flag
- **THEN** a new account is created with `source='csv'` and the user is prompted to confirm the name

#### Scenario: Existing account used
- **WHEN** `finance import file.csv --institution chase --account <existing-id>` is run
- **THEN** transactions are associated with the existing account

#### Scenario: Non-existent account ID provided
- **WHEN** `finance import file.csv --institution chase --account nonexistent` is run
- **THEN** an error is printed and no rows are imported
