## ADDED Requirements

### Requirement: get_data_overview returns global and per-account coverage stats
`get_data_overview(conn)` in `finance/analysis/overview.py` SHALL return a dict with two keys:
- `global`: a dict with `total_accounts` (int), `total_transactions` (int), `total_balances` (int), `earliest_transaction` (str YYYY-MM-DD or null), `latest_transaction` (str YYYY-MM-DD or null)
- `per_account`: a list of dicts, one per active account, each with `account_id` (str), `name` (str), `institution` (str or null), `txn_count` (int), `earliest_txn` (str YYYY-MM-DD or null), `latest_txn` (str YYYY-MM-DD or null), `last_balance` (float or null), `last_synced_at` (int unix-ms or null)

The function SHALL follow the existing `finance/analysis/` conventions: pure function, takes `sqlite3.Connection` as first positional argument, returns plain dicts (no ORM objects).

#### Scenario: Database with multiple accounts and transactions
- **WHEN** `get_data_overview(conn)` is called with a database containing 3 accounts and 150 transactions spanning 2023-01-01 to 2025-12-31
- **THEN** `result["global"]["total_accounts"]` is 3, `result["global"]["total_transactions"]` is 150, `result["global"]["earliest_transaction"]` is "2023-01-01", `result["global"]["latest_transaction"]` is "2025-12-31"

#### Scenario: Account with no transactions
- **WHEN** `get_data_overview(conn)` is called and one active account has zero transactions
- **THEN** that account appears in `per_account` with `txn_count` of 0, `earliest_txn` of null, and `latest_txn` of null

#### Scenario: Account with no sync_state row
- **WHEN** an account has never been synced via SimpleFIN (e.g. CSV-only account with no row in sync_state)
- **THEN** that account appears in `per_account` with `last_synced_at` of null

#### Scenario: Empty database
- **WHEN** `get_data_overview(conn)` is called on a database with no accounts or transactions
- **THEN** `result["global"]["total_accounts"]` is 0, `result["global"]["total_transactions"]` is 0, `result["global"]["earliest_transaction"]` is null, `result["global"]["latest_transaction"]` is null, and `result["per_account"]` is an empty list

#### Scenario: Global stats reflect all active accounts only
- **WHEN** an account has `active = 0`
- **THEN** it does not appear in `per_account` and does not contribute to `total_accounts` or transaction counts
