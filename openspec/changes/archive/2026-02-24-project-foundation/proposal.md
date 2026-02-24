# Proposal: project-foundation

## Problem / Motivation

Before any syncing, analysis, or MCP integration can happen, the project needs a working Python package structure, a SQLite database with the right schema, and the basic tooling wired up. This is the skeleton everything else builds on.

## Goals

- Initialize the Python project with `uv` and `pyproject.toml`
- Define the SQLite schema (institutions, accounts, balances, transactions, sync_state)
- Implement a `db.py` module with connection management and schema initialization
- Create the package directory structure with empty module stubs
- Add `.env.example` documenting required environment variables
- Ensure `uv run python -c "from finance.db import init_db; init_db()"` works end-to-end

## Non-goals

- No actual data ingestion (SimpleFIN or CSV) — that's `simplefin-sync`
- No analysis functions — those come in `mcp-server`
- No CLI commands beyond a basic `finance --help` stub
- No MCP server — that's `mcp-server`

## Approach

1. `pyproject.toml` — defines package, entry points (`finance` CLI, `finance-mcp` server), and dependencies (`mcp`, `httpx`, `click`, `python-dotenv`)
2. `finance/db.py` — `init_db()` creates all tables if not exist; `get_connection()` returns a configured sqlite3 connection (WAL mode, row_factory)
3. `finance/db.sql` (or inline SQL in db.py) — canonical schema definition
4. Module stubs: `ingestion/__init__.py`, `analysis/__init__.py`, `ai/__init__.py`, `server.py`, `cli.py`
5. `data/` directory with `.gitkeep` placeholder (the actual DB lives here, gitignored)
6. `.env.example` with `SIMPLEFIN_TOKEN=`, `DATABASE_PATH=data/finance.db`, `ANTHROPIC_API_KEY=`

## Schema

```sql
CREATE TABLE institutions (
    id    TEXT PRIMARY KEY,
    name  TEXT NOT NULL,
    url   TEXT,
    source TEXT NOT NULL  -- 'simplefin' | 'csv'
);

CREATE TABLE accounts (
    id             TEXT PRIMARY KEY,
    institution_id TEXT REFERENCES institutions(id),
    name           TEXT NOT NULL,
    type           TEXT,  -- 'checking' | 'savings' | 'credit' | 'investment' | 'loan'
    currency       TEXT DEFAULT 'USD',
    mask           TEXT,
    active         INTEGER DEFAULT 1
);

CREATE TABLE balances (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT REFERENCES accounts(id),
    timestamp  INTEGER NOT NULL,  -- unix ms
    balance    REAL,
    available  REAL
);

CREATE TABLE transactions (
    id            TEXT PRIMARY KEY,
    account_id    TEXT REFERENCES accounts(id),
    date          TEXT NOT NULL,   -- YYYY-MM-DD
    amount        REAL NOT NULL,   -- negative = debit
    description   TEXT,
    merchant_name TEXT,
    category      TEXT,
    pending       INTEGER DEFAULT 0,
    source        TEXT,            -- 'simplefin' | 'csv'
    raw           TEXT             -- original JSON/row
);

CREATE TABLE sync_state (
    account_id     TEXT PRIMARY KEY REFERENCES accounts(id),
    last_synced_at INTEGER
);
```

## Open Questions

- Store schema as a separate `finance/db.sql` file or inline in `db.py`? Inline is simpler for a small schema.
- WAL mode on by default — any reason not to? (No, WAL is strictly better for this use case.)
