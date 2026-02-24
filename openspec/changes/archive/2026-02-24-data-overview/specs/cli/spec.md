## ADDED Requirements

### Requirement: finance data command prints data coverage summary
The `finance data` CLI command SHALL print a global summary line followed by a per-account coverage table.

#### Scenario: data command with transaction data
- **WHEN** `finance data` is run against a database with accounts and transactions
- **THEN** stdout contains a global summary line "X transactions across Y accounts, covering Z months" and a table with columns: Account, Institution, Transactions, Earliest, Latest, Last Synced

#### Scenario: data command with an account that has no transactions
- **WHEN** an active account has zero transactions
- **THEN** that account row shows 0 for Transactions, blank or "—" for Earliest and Latest, and the last sync timestamp (or "Never") for Last Synced

#### Scenario: data command with empty database
- **WHEN** `finance data` is run against a database with no active accounts
- **THEN** stdout contains "No accounts found." or equivalent message

#### Scenario: data command --json flag
- **WHEN** `finance data --json` is run
- **THEN** stdout contains valid JSON matching the structure returned by `get_data_overview(conn)` (with `global` and `per_account` keys), suitable for piping to `jq`
