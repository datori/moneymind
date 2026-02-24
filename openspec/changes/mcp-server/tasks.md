## 1. Analysis: Accounts

- [ ] 1.1 Create `finance/analysis/accounts.py`
- [ ] 1.2 Implement `get_accounts(conn) -> list[dict]` — query `accounts` joined to latest `balances` snapshot per account (LEFT JOIN with subquery for MAX timestamp), filter `active=1`
- [ ] 1.3 Implement `get_account_by_id(conn, account_id: str) -> dict | None`
- [ ] 1.4 Implement `get_credit_utilization(conn) -> dict` — join `accounts` (type='credit') with latest `balances` and `credit_limits`; compute `utilization_pct = abs(balance) / credit_limit * 100` where limit exists, else null

## 2. Analysis: Spending & Transactions

- [ ] 2.1 Create `finance/analysis/spending.py`
- [ ] 2.2 Implement `get_transactions(conn, *, start_date=None, end_date=None, account_id=None, category=None, min_amount=None, max_amount=None, limit=100) -> list[dict]` — build parameterized WHERE clause from provided filters; default start_date = 30 days ago
- [ ] 2.3 Implement `get_spending_summary(conn, start_date: str, end_date: str, group_by: str = "category") -> list[dict]` — sum `ABS(amount)` for `amount < 0` transactions grouped by `category`, `merchant_name`, or `account_id`; order by total DESC

## 3. Analysis: Net Worth

- [ ] 3.1 Create `finance/analysis/net_worth.py`
- [ ] 3.2 Implement `get_net_worth(conn, as_of_date: str | None = None) -> dict` — for each active account, find the most recent balance snapshot on or before `as_of_date` (default: latest); classify by account type into assets vs liabilities; return `{total, assets, liabilities, by_type, as_of}`
- [ ] 3.3 Implement `get_balance_history(conn, account_id: str | None = None) -> list[dict]` — return all balance snapshots optionally filtered by account, ordered by timestamp ASC

## 4. MCP Server

- [ ] 4.1 Replace `finance/server.py` stub with a working MCP server using the `mcp` Python SDK
- [ ] 4.2 Implement `get_accounts` MCP tool — calls `analysis.accounts.get_accounts(conn)`
- [ ] 4.3 Implement `get_transactions` MCP tool — calls `analysis.spending.get_transactions(conn, ...)` with all parameters forwarded
- [ ] 4.4 Implement `get_net_worth` MCP tool — calls `analysis.net_worth.get_net_worth(conn, ...)`
- [ ] 4.5 Implement `get_spending_summary` MCP tool — calls `analysis.spending.get_spending_summary(conn, ...)`
- [ ] 4.6 Implement `get_credit_utilization` MCP tool — calls `analysis.accounts.get_credit_utilization(conn)`
- [ ] 4.7 Implement `sync` MCP tool — calls `ingestion.simplefin.sync_all(conn)`, returns summary dict
- [ ] 4.8 Implement `main()` in `server.py` — creates DB connection, runs MCP server via `mcp.run()`

## 5. CLI Commands

- [ ] 5.1 Replace `finance/cli.py` stub with full Click group
- [ ] 5.2 Add `finance accounts` command — calls `get_accounts()`, prints formatted table (name, type, institution, balance); supports `--json`
- [ ] 5.3 Add `finance transactions` command — accepts `--start`, `--end`, `--account`, `--category`, `--limit`; supports `--json`
- [ ] 5.4 Add `finance net-worth` command — accepts `--as-of`; supports `--json`
- [ ] 5.5 Add `finance spending` command — accepts `--start`, `--end`, `--group-by`; supports `--json`
- [ ] 5.6 Add `finance utilization` command — supports `--json`
- [ ] 5.7 Add `finance set-limit <account-id> <amount>` command — upserts row in `credit_limits`
- [ ] 5.8 Add `finance limits` command — lists all configured credit limits with account names

## 6. Verification

- [ ] 6.1 Verify `uv run finance-mcp` starts without error
- [ ] 6.2 Verify `uv run finance accounts` prints account table (requires data from simplefin-sync)
- [ ] 6.3 Verify `uv run finance net-worth --json` outputs valid JSON
- [ ] 6.4 Verify `uv run finance spending --start 2025-01-01 --end 2025-12-31` runs without error
- [ ] 6.5 Verify `uv run finance set-limit <account-id> 5000` and then `uv run finance utilization` shows the configured limit
