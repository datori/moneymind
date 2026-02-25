import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/finance.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS institutions (
    id     TEXT PRIMARY KEY,
    name   TEXT NOT NULL,
    url    TEXT,
    source TEXT NOT NULL  -- 'simplefin' | 'csv'
);

CREATE TABLE IF NOT EXISTS accounts (
    id             TEXT PRIMARY KEY,
    institution_id TEXT REFERENCES institutions(id),
    name           TEXT NOT NULL,
    type           TEXT,  -- 'checking' | 'savings' | 'credit' | 'investment' | 'loan'
    currency       TEXT DEFAULT 'USD',
    mask           TEXT,
    active         INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS balances (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT REFERENCES accounts(id),
    timestamp  INTEGER NOT NULL,  -- unix ms
    balance    REAL,
    available  REAL
);

CREATE TABLE IF NOT EXISTS transactions (
    id             TEXT PRIMARY KEY,
    account_id     TEXT REFERENCES accounts(id),
    date           TEXT NOT NULL,    -- YYYY-MM-DD
    amount         REAL NOT NULL,    -- negative = debit
    description    TEXT,
    merchant_name  TEXT,
    category       TEXT,
    pending        INTEGER DEFAULT 0,
    source         TEXT,             -- 'simplefin' | 'csv'
    raw            TEXT,             -- original JSON/row
    categorized_at INTEGER           -- unix ms; NULL = not yet categorized
);

CREATE TABLE IF NOT EXISTS sync_state (
    account_id     TEXT PRIMARY KEY REFERENCES accounts(id),
    last_synced_at INTEGER
);

CREATE TABLE IF NOT EXISTS credit_limits (
    account_id   TEXT PRIMARY KEY REFERENCES accounts(id),
    credit_limit REAL NOT NULL,
    updated_at   INTEGER NOT NULL  -- unix ms
);

CREATE TABLE IF NOT EXISTS run_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type    TEXT NOT NULL,
    started_at  INTEGER NOT NULL,
    finished_at INTEGER,
    status      TEXT NOT NULL DEFAULT 'running',
    error_msg   TEXT,
    summary     TEXT
);

CREATE TABLE IF NOT EXISTS run_steps (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           INTEGER NOT NULL REFERENCES run_log(id),
    step_type        TEXT NOT NULL,
    batch_index      INTEGER,
    batch_total      INTEGER,
    started_at       INTEGER NOT NULL,
    finished_at      INTEGER,
    request_summary  TEXT,
    response_summary TEXT,
    tokens_in        INTEGER,
    tokens_out       INTEGER,
    error_msg        TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    """Open the SQLite database, configure row_factory, and enable WAL mode."""
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables if they do not already exist."""
    conn.executescript(_SCHEMA)
    conn.commit()

    # Schema migrations: add new columns to transactions.
    # Each ALTER TABLE is idempotent — OperationalError is suppressed when the
    # column already exists (SQLite does not support IF NOT EXISTS for columns).
    _migrations = [
        "ALTER TABLE transactions ADD COLUMN needs_review INTEGER DEFAULT 0",
        "ALTER TABLE transactions ADD COLUMN review_reason TEXT",
        "ALTER TABLE transactions ADD COLUMN is_recurring INTEGER DEFAULT 0",
        "ALTER TABLE transactions ADD COLUMN merchant_normalized TEXT",
        "ALTER TABLE run_log ADD COLUMN summary TEXT",
    ]
    for stmt in _migrations:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # column already exists
    conn.commit()

    # Balance snapshot deduplication: remove exact (account_id, timestamp) duplicates
    # keeping the earliest row (MIN id), then enforce uniqueness going forward.
    conn.execute(
        """
        DELETE FROM balances
        WHERE id NOT IN (
            SELECT MIN(id) FROM balances GROUP BY account_id, timestamp
        )
        """
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_balances_account_ts ON balances(account_id, timestamp)"
    )
    conn.commit()
