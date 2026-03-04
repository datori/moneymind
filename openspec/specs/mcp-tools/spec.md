## ADDED Requirements

### Requirement: MCP server runs and is discoverable
The MCP server SHALL start and be usable by any Claude session when run via `uv run finance-mcp`.

#### Scenario: Server starts
- **WHEN** `uv run finance-mcp` is executed
- **THEN** the server starts without error and registers all tools

---

### Requirement: get_accounts tool
The MCP tool `get_accounts` SHALL return all active accounts with their most recent balance.

Return shape per account:
```
{ id, name, type, institution, balance, available, currency, mask, last_updated }
```

#### Scenario: Returns all active accounts
- **WHEN** `get_accounts()` is called
- **THEN** one entry per active account is returned with its most recent balance snapshot

#### Scenario: No accounts
- **WHEN** `get_accounts()` is called with an empty database
- **THEN** an empty list is returned

---

### Requirement: get_transactions tool
The MCP tool `get_transactions` SHALL return transactions matching the given filters.

Parameters (all optional): `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD), `account_id`, `category`, `min_amount`, `max_amount`, `limit` (default 100).

Return shape per transaction:
```
{ id, date, amount, description, merchant_name, merchant_normalized,
  category, account_id, account_name, pending,
  is_recurring, needs_review, review_reason }
```

#### Scenario: Default returns last 30 days
- **WHEN** `get_transactions()` is called with no arguments
- **THEN** transactions from the past 30 days are returned, up to 100

#### Scenario: Date filter applied
- **WHEN** `get_transactions(start_date="2025-01-01", end_date="2025-01-31")` is called
- **THEN** only transactions with date in January 2025 are returned

#### Scenario: Limit respected
- **WHEN** `get_transactions(limit=10)` is called
- **THEN** at most 10 transactions are returned

---

### Requirement: get_net_worth tool
The MCP tool `get_net_worth` SHALL return net worth broken down by account type using the most recent balance per account.

Return shape:
```
{ total, assets, liabilities, by_type: { checking, savings, investment, credit, loan }, as_of }
```

#### Scenario: Net worth calculated from latest balances
- **WHEN** `get_net_worth()` is called
- **THEN** total = assets - liabilities, using the most recent balance snapshot per account

#### Scenario: as_of_date parameter
- **WHEN** `get_net_worth(as_of_date="2025-06-01")` is called
- **THEN** the most recent balance snapshot on or before that date is used per account

---

### Requirement: get_spending_summary tool
The MCP tool `get_spending_summary` SHALL aggregate debit transaction amounts by the requested dimension.

Parameters: `start_date` (required), `end_date` (required), `group_by` ("category" | "merchant" | "account", default "category").

Return shape per group:
```
{ label, total, count }
```
Where `total` is the absolute value of the sum of negative-amount transactions.

#### Scenario: Category summary
- **WHEN** `get_spending_summary(start_date="2025-01-01", end_date="2025-01-31", group_by="category")` is called
- **THEN** one entry per category is returned, sorted by total descending

#### Scenario: Only debits included
- **WHEN** `get_spending_summary(...)` is called for a period containing both debits and credits
- **THEN** only negative-amount (debit) transactions are included in totals

---

### Requirement: get_credit_utilization tool
The MCP tool `get_credit_utilization` SHALL return per-card and aggregate credit utilization using the most recent balance and configured credit limits.

Return shape:
```
{
  aggregate_pct,    -- null if no cards have configured limits
  total_balance,
  total_limit,      -- null if no limits configured
  cards: [{ account_id, name, balance, limit, utilization_pct }]
}
```

#### Scenario: Card with configured limit
- **WHEN** `get_credit_utilization()` is called for a card with a row in `credit_limits`
- **THEN** `utilization_pct` = `abs(balance) / credit_limit * 100`

#### Scenario: Card without configured limit
- **WHEN** `get_credit_utilization()` is called for a card with no row in `credit_limits`
- **THEN** that card's `limit` and `utilization_pct` are null

---

### Requirement: sync tool
The MCP tool `sync` SHALL trigger a SimpleFIN sync and return a summary.

Return shape:
```
{ accounts_updated, new_transactions, synced_at }
```

#### Scenario: Successful sync via MCP
- **WHEN** `sync()` is called via MCP
- **THEN** SimpleFIN is queried, data is upserted, and a summary is returned
