## MODIFIED Requirements

### Requirement: SimpleFIN account sync
The system SHALL fetch account data from the SimpleFIN `/accounts` endpoint and upsert it into the local database. The sync operation SHALL NOT trigger any LLM categorization or enrichment calls.

#### Scenario: Successful sync
- **WHEN** `finance sync` is run with `SIMPLEFIN_ACCESS_URL` configured
- **THEN** all accounts returned by SimpleFIN are upserted into `accounts` and `institutions` tables
- **AND** a balance snapshot is inserted into `balances` for each account (skipped if a snapshot with the same `account_id` and `balance-date` timestamp already exists)
- **AND** new transactions are inserted into `transactions` (existing IDs skipped)
- **AND** `sync_state.last_synced_at` is updated for each account
- **AND** no LLM API calls are made

#### Scenario: Missing access URL
- **WHEN** `finance sync` is run without `SIMPLEFIN_ACCESS_URL` in environment
- **THEN** an error message is printed explaining how to run `finance sync setup`

#### Scenario: Network failure
- **WHEN** the SimpleFIN API returns a non-200 response or is unreachable
- **THEN** an error message including the status code is printed and no DB changes are made
