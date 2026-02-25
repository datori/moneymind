## ADDED Requirements

### Requirement: get_transaction_timeline function
`get_transaction_timeline(conn, account_id=None, months=13)` in `finance/analysis/accounts.py` SHALL return monthly transaction counts per active account for the past N complete calendar months (counting back from the current month inclusive).

The return value SHALL be a dict with:
- `months`: list of `YYYY-MM` strings, sorted ascending, exactly `months` entries
- `accounts`: list of dicts, one per active account, each with:
  - `id`: account id string
  - `name`: account display name string
  - `counts`: list of ints, length == len(months), zero-filled for months with no transactions

When `account_id` is provided and not `None`, `accounts` SHALL contain only the matching account (or an empty list if the account does not exist or is inactive).

#### Scenario: All accounts, default 13 months
- **WHEN** `get_transaction_timeline(conn)` is called with no arguments
- **THEN** the returned `months` list has exactly 13 entries spanning the past 13 calendar months
- **THEN** the `accounts` list contains one entry per active account

#### Scenario: Single account filter
- **WHEN** `get_transaction_timeline(conn, account_id="acct-123")` is called
- **THEN** `accounts` contains exactly one entry with `id == "acct-123"`
- **THEN** `months` still spans the full 13-month window

#### Scenario: Month with no transactions shows zero count
- **WHEN** an active account has no transactions in a given month within the window
- **THEN** the corresponding entry in that account's `counts` list is `0` (not absent)

#### Scenario: Custom months parameter
- **WHEN** `get_transaction_timeline(conn, months=6)` is called
- **THEN** `months` list has exactly 6 entries and `counts` lists have length 6

#### Scenario: No transactions at all
- **WHEN** the transactions table is empty
- **THEN** `months` still has 13 entries and all `counts` values are `0`
