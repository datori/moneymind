## ADDED Requirements

### Requirement: CSV import command
The system SHALL provide a `finance import <file>` CLI command that imports transactions from a CSV file into the database.

#### Scenario: Basic import with institution flag
- **WHEN** `finance import chase_jan2025.csv --institution chase --account <id>` is run
- **THEN** transactions from the file are parsed and upserted into the `transactions` table

#### Scenario: Import summary printed
- **WHEN** `finance import ...` completes
- **THEN** stdout shows: rows read, rows imported, rows skipped (duplicates)

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
| Amex | `amex` | Amount column; negative = debit |
| Robinhood | `robinhood` | Amount column; buys = negative |
| M1 | `m1` | Amount column; buys = negative |

#### Scenario: Citi Debit/Credit column merge
- **WHEN** a Citi CSV row has a value in the `Debit` column
- **THEN** the stored amount is `-(abs(debit_value))`

#### Scenario: Citi credit row
- **WHEN** a Citi CSV row has a value in the `Credit` column
- **THEN** the stored amount is `+abs(credit_value)`

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
