## ADDED Requirements

### Requirement: Database initialization
The system SHALL initialize the SQLite database by calling `init_db()`, which creates all tables using `CREATE TABLE IF NOT EXISTS`. The database file path SHALL be read from the `DATABASE_PATH` environment variable, defaulting to `data/finance.db`.

#### Scenario: First-time initialization
- **WHEN** `init_db()` is called and no database file exists
- **THEN** the database file is created at the configured path and all tables are created

#### Scenario: Idempotent initialization
- **WHEN** `init_db()` is called and the database already exists with all tables
- **THEN** no error is raised and no data is modified

#### Scenario: WAL mode enabled
- **WHEN** any connection is opened via `get_connection()`
- **THEN** the connection operates in WAL (Write-Ahead Logging) mode

---

### Requirement: institutions table
The system SHALL maintain an `institutions` table storing financial institution metadata.

Schema:
```sql
CREATE TABLE institutions (
    id     TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    url    TEXT,
    source TEXT NOT NULL  -- 'simplefin' | 'csv'
);
```

#### Scenario: Institution record created
- **WHEN** a new institution is encountered during sync or import
- **THEN** a row is inserted with id, name, url (nullable), and source

---

### Requirement: accounts table
The system SHALL maintain an `accounts` table storing all financial accounts.

Schema:
```sql
CREATE TABLE accounts (
    id             TEXT PRIMARY KEY,
    institution_id TEXT REFERENCES institutions(id),
    name           TEXT NOT NULL,
    type           TEXT,     -- 'checking' | 'savings' | 'credit' | 'investment' | 'loan'
    currency       TEXT DEFAULT 'USD',
    mask           TEXT,
    active         INTEGER DEFAULT 1
);
```

#### Scenario: Account record created
- **WHEN** a new account is encountered
- **THEN** a row is inserted with all available fields

---

### Requirement: balances table
The system SHALL maintain a `balances` table as a time-series of balance snapshots, deduplicated on `(account_id, timestamp)`. A `UNIQUE INDEX` on those two columns ensures that if SimpleFIN returns the same `balance-date` on multiple syncs, only one row is stored.

Schema:
```sql
CREATE TABLE balances (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT REFERENCES accounts(id),
    timestamp  INTEGER NOT NULL,  -- unix ms
    balance    REAL,
    available  REAL
);
CREATE UNIQUE INDEX uq_balances_account_ts ON balances(account_id, timestamp);
```

#### Scenario: Balance snapshot inserted (first time for this timestamp)
- **WHEN** a sync runs and SimpleFIN returns a `balance-date` not yet stored for that account
- **THEN** a new balance row is inserted

#### Scenario: Balance snapshot skipped (duplicate timestamp)
- **WHEN** a sync runs and SimpleFIN returns the same `balance-date` as a previously stored snapshot for that account
- **THEN** the insert is silently skipped (`INSERT OR IGNORE`); no duplicate row is created

---

### Requirement: transactions table
The system SHALL maintain a `transactions` table with deduplication on `id`.

Schema:
```sql
CREATE TABLE transactions (
    id             TEXT PRIMARY KEY,
    account_id     TEXT REFERENCES accounts(id),
    date           TEXT NOT NULL,       -- YYYY-MM-DD
    amount         REAL NOT NULL,       -- negative = debit, positive = credit
    description    TEXT,
    merchant_name  TEXT,
    category       TEXT,
    categorized_at INTEGER,             -- unix ms, NULL if not yet categorized
    pending        INTEGER DEFAULT 0,
    source         TEXT,                -- 'simplefin' | 'csv'
    raw            TEXT                 -- original JSON or CSV row
);
```

#### Scenario: Transaction deduplication
- **WHEN** a transaction with an existing `id` is ingested
- **THEN** the existing row is preserved unchanged (INSERT OR IGNORE)

#### Scenario: Amount sign convention
- **WHEN** a debit/purchase transaction is stored
- **THEN** the `amount` value is negative

#### Scenario: Amount sign convention (credit)
- **WHEN** a credit/refund/deposit transaction is stored
- **THEN** the `amount` value is positive

---

### Requirement: sync_state table
The system SHALL maintain a `sync_state` table tracking the last successful sync time per account.

Schema:
```sql
CREATE TABLE sync_state (
    account_id     TEXT PRIMARY KEY REFERENCES accounts(id),
    last_synced_at INTEGER  -- unix ms
);
```

#### Scenario: Sync state updated after sync
- **WHEN** a sync completes successfully for an account
- **THEN** `last_synced_at` is updated to the current time in unix ms

---

### Requirement: credit_limits table
The system SHALL maintain a `credit_limits` table for manually-configured credit card limits.

Schema:
```sql
CREATE TABLE credit_limits (
    account_id   TEXT PRIMARY KEY REFERENCES accounts(id),
    credit_limit REAL NOT NULL,
    updated_at   INTEGER NOT NULL  -- unix ms
);
```

#### Scenario: Credit limit stored
- **WHEN** a user configures a credit limit for an account via CLI
- **THEN** the limit is stored in this table and returned by `get_credit_utilization()`

#### Scenario: Missing credit limit
- **WHEN** `get_credit_utilization()` is called for an account with no configured limit
- **THEN** that card's `utilization_pct` is returned as null
