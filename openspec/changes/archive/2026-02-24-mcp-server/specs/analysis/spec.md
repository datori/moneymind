## ADDED Requirements

### Requirement: Analysis functions accept a Connection parameter
All analysis functions in `finance/analysis/` SHALL take a `sqlite3.Connection` as their first positional argument and return plain dicts or lists of dicts.

#### Scenario: Analysis function called with test connection
- **WHEN** an analysis function is called with a test database connection
- **THEN** it queries only that connection (no global state accessed)

---

### Requirement: get_accounts returns latest balance per account
`get_accounts(conn)` SHALL return all accounts with `active=1`, each joined to their most recent balance snapshot.

#### Scenario: Account with no balance snapshot
- **WHEN** `get_accounts(conn)` is called for an account with no rows in `balances`
- **THEN** that account is still returned with `balance=null`

---

### Requirement: get_transactions supports filtering
`get_transactions(conn, *, start_date, end_date, account_id, category, min_amount, max_amount, limit)` SHALL apply all provided filters as SQL WHERE clauses.

#### Scenario: All filters combined
- **WHEN** multiple filters are provided simultaneously
- **THEN** all filters are applied (AND logic)

---

### Requirement: get_net_worth sums latest balances
`get_net_worth(conn, as_of_date=None)` SHALL compute net worth by summing the most recent balance per account.

Classification (by `type` field):
- Assets: accounts with `type` in ('checking', 'savings', 'investment')
- Liabilities: accounts with `type` in ('credit', 'loan') — balances for these are negative or zero
- Unknown/NULL type (e.g. SimpleFIN does not populate `type`): use balance sign as fallback — positive balance → asset, negative balance → liability

#### Scenario: Investment account contribution
- **WHEN** an investment account has a positive balance
- **THEN** it increases both `assets` and `total`

#### Scenario: Credit card contribution
- **WHEN** a credit account has a negative balance (balance owed)
- **THEN** `abs(balance)` increases `liabilities` and decreases `total`

#### Scenario: Account with unknown type
- **WHEN** an account has `type = NULL` (as is the case for all SimpleFIN-sourced accounts)
- **THEN** a positive balance increases `assets`, a negative balance increases `liabilities`

---

### Requirement: get_spending_summary aggregates debits
`get_spending_summary(conn, start_date, end_date, group_by="category")` SHALL sum absolute amounts of transactions with `amount < 0` in the date range.

#### Scenario: Results sorted by total descending
- **WHEN** `get_spending_summary(...)` returns multiple groups
- **THEN** groups are ordered by total (highest spend first)
