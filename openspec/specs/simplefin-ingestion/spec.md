## ADDED Requirements

### Requirement: SimpleFIN setup token claim
The system SHALL support claiming a SimpleFIN Setup Token to obtain an Access URL.

SimpleFIN setup tokens are base64-encoded claim URLs. The system SHALL base64-decode the token to obtain the claim URL before POSTing to it.

#### Scenario: Successful token claim
- **WHEN** `finance sync setup <setup-token>` is run with a valid base64-encoded setup token
- **THEN** the token is base64-decoded to a claim URL, a POST is made to that URL, and the returned Access URL is printed to stdout with instructions to add it to `.env` as `SIMPLEFIN_ACCESS_URL`

#### Scenario: Invalid token URL
- **WHEN** `finance sync setup <token>` is run with an invalid or already-claimed token
- **THEN** an error message is printed and the command exits with a non-zero code

---

### Requirement: SimpleFIN account sync
The system SHALL fetch account data from the SimpleFIN `/accounts` endpoint and upsert it into the local database.

#### Scenario: Successful sync
- **WHEN** `finance sync` is run with `SIMPLEFIN_ACCESS_URL` configured
- **THEN** all accounts returned by SimpleFIN are upserted into `accounts` and `institutions` tables
- **AND** a balance snapshot is appended to `balances` for each account
- **AND** new transactions are inserted into `transactions` (existing IDs skipped)
- **AND** `sync_state.last_synced_at` is updated for each account

#### Scenario: Missing access URL
- **WHEN** `finance sync` is run without `SIMPLEFIN_ACCESS_URL` in environment
- **THEN** an error message is printed explaining how to run `finance sync setup`

#### Scenario: Network failure
- **WHEN** the SimpleFIN API returns a non-200 response or is unreachable
- **THEN** an error message including the status code is printed and no DB changes are made

---

### Requirement: Sync transaction window
The system SHALL use a time-bounded window for fetching transactions to avoid redundant re-fetching.

#### Scenario: First sync (no prior state)
- **WHEN** `finance sync` runs for an account with no entry in `sync_state`
- **THEN** transactions are fetched from 90 days ago to now

#### Scenario: Subsequent sync
- **WHEN** `finance sync` runs for an account with a `last_synced_at` timestamp
- **THEN** transactions are fetched from `last_synced_at` to now

---

### Requirement: Sync summary output
The system SHALL print a human-readable summary after each sync.

#### Scenario: Sync completes
- **WHEN** `finance sync` completes
- **THEN** stdout shows the number of accounts synced, new transactions added, and balance snapshots recorded

---

### Requirement: Transaction amount sign normalization
All transactions ingested via SimpleFIN SHALL follow the negative=debit convention.

#### Scenario: Purchase transaction stored
- **WHEN** SimpleFIN returns a transaction with a negative amount (e.g. `-45.00`)
- **THEN** the stored `amount` is negative

#### Scenario: Deposit or refund stored
- **WHEN** SimpleFIN returns a transaction with a positive amount
- **THEN** the stored `amount` is positive
