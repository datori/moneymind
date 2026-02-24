## 1. SimpleFIN Client

- [ ] 1.1 Create `finance/ingestion/simplefin.py` with a `SimpleFINClient` class that takes `access_url: str` in `__init__`
- [ ] 1.2 Implement `SimpleFINClient.fetch_accounts(start_date: int | None = None) -> dict` — GET `{access_url}/accounts` with HTTP basic auth (user="", password=access_url), pass `start-date` query param if provided
- [ ] 1.3 Implement `claim_setup_token(setup_token_url: str) -> str` module-level function — POST to the setup token URL and return the access URL
- [ ] 1.4 Add `SIMPLEFIN_ACCESS_URL` loading from env in `simplefin.py`, raise clear `ValueError` if missing when client is instantiated

## 2. Data Upsert Logic

- [ ] 2.1 Implement `upsert_institution(conn, org: dict) -> str` — `INSERT OR REPLACE INTO institutions`, return institution id
- [ ] 2.2 Implement `upsert_account(conn, account: dict, institution_id: str) -> str` — `INSERT OR REPLACE INTO accounts`, return account id
- [ ] 2.3 Implement `insert_balance_snapshot(conn, account_id: str, balance: float, available: float | None, timestamp_s: int)` — convert unix seconds to ms, `INSERT INTO balances`
- [ ] 2.4 Implement `upsert_transactions(conn, account_id: str, transactions: list[dict]) -> int` — `INSERT OR IGNORE INTO transactions` for each, return count of new rows inserted
- [ ] 2.5 Implement `update_sync_state(conn, account_id: str)` — `INSERT OR REPLACE INTO sync_state` with current unix ms timestamp

## 3. Sync Orchestration

- [ ] 3.1 Implement `sync_all(conn) -> dict` — orchestrate full sync: fetch all accounts, upsert institutions/accounts, insert balances, upsert transactions, update sync_state; return `{accounts_updated, new_transactions, synced_at}`
- [ ] 3.2 Implement sync window logic: for each account, read `last_synced_at` from `sync_state`; if none, use 90 days ago as `start_date` for SimpleFIN request
- [ ] 3.3 Handle accounts that return empty `transactions` list (balance-only) without error

## 4. CLI Commands

- [ ] 4.1 Add `finance sync` command to `cli.py` — calls `sync_all(conn)`, prints summary: accounts synced, new transactions, timestamp
- [ ] 4.2 Add `finance sync setup <setup-token-url>` subcommand — calls `claim_setup_token()`, prints the access URL with instructions to add to `.env`
- [ ] 4.3 Add `finance accounts` command stub to `cli.py` (just prints "Run mcp-server change to implement" — will be replaced in that change)

## 5. Verification

- [ ] 5.1 Verify `finance sync setup` prints a clear error if the URL is invalid (not a real SimpleFIN URL)
- [ ] 5.2 Verify `finance sync` exits with a clear error message when `SIMPLEFIN_ACCESS_URL` is not set
- [ ] 5.3 (After configuring real SimpleFIN token) Run `finance sync` and verify rows appear in `accounts`, `balances`, `transactions`, and `sync_state` tables
