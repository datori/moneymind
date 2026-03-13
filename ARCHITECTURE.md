# Finance — Architecture

## Goal

Build a local, self-hosted personal finance intelligence system that:
- Imports transaction and balance data via **SimpleFIN Bridge** (primary) + CSV fallback
- Stores everything in a local database — no cloud dependency after initial sync
- Runs AI analysis on spending, net worth trends, credit utilization, investment allocation
- Exposes data as an MCP server so any Claude session can query financial data directly
- Built from scratch — full control over architecture, models, and analysis logic

## Design Philosophy

This is a power-user tool built for a single user. The goal is not to replicate
what Copilot or Monarch do — it's to have a programmable financial data layer that
any AI agent or custom script can query. Prefer simple, composable pieces over
monolithic frameworks.

**What this is NOT:**
- A budgeting app with categories and goals UI
- A multi-user application
- A Plaid integration (approval friction, overkill for personal use)
- A Firefly III wrapper (complex, opinionated, not worth the overhead)

---

## Data Ingestion Strategy

### Primary: SimpleFIN Bridge
- Low-cost annual subscription, no approval process, built for personal use
- Token-based access (Setup Token → Access Token → `/accounts` endpoint)
- Returns: balances, transactions per account
- Rate limit: ~1 request per 24 hours (daily sync is the intended use case)
- Python client or raw HTTP (simple enough to call directly)

### Fallback: CSV Import
- Every account supports CSV export from their web UI
- CSV importer normalizes across institution-specific formats (Chase, Citi, Amex, Discover, Apple Card, etc.)
- Used as a historical backfill before SimpleFIN sync starts or for accounts SimpleFIN can't reach

### Out of scope (for now)
- OFX Direct Connect
- Plaid
- Screen scraping

---

## Data Architecture

### Storage: SQLite
- Single local file, zero ops, easy backup
- Strong enough for analytics at this scale (one person's data)
- Can run DuckDB queries against it for heavy analysis if needed

### Schema

```sql
-- Institutions / connection metadata
CREATE TABLE institutions (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    url         TEXT,
    source      TEXT NOT NULL  -- 'simplefin' | 'csv'
);

-- Accounts
CREATE TABLE accounts (
    id              TEXT PRIMARY KEY,  -- SimpleFIN org:id or generated
    institution_id  TEXT REFERENCES institutions(id),
    name            TEXT NOT NULL,
    type            TEXT,              -- 'checking' | 'savings' | 'credit' | 'investment' | 'loan'
    currency        TEXT DEFAULT 'USD',
    mask            TEXT,              -- last 4 digits
    active          BOOLEAN DEFAULT 1
);

-- Balance snapshots (append-only history)
CREATE TABLE balances (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id  TEXT REFERENCES accounts(id),
    timestamp   INTEGER NOT NULL,  -- unix ms
    balance     REAL,
    available   REAL
);

-- Transactions (deduplicated by transaction_id)
CREATE TABLE transactions (
    id              TEXT PRIMARY KEY,  -- SimpleFIN id or hash(csv row)
    account_id      TEXT REFERENCES accounts(id),
    date            TEXT NOT NULL,     -- YYYY-MM-DD
    amount          REAL NOT NULL,     -- negative = debit
    description     TEXT,
    merchant_name   TEXT,
    category        TEXT,              -- AI-assigned
    pending         BOOLEAN DEFAULT 0,
    source          TEXT,              -- 'simplefin' | 'csv'
    raw             TEXT               -- original JSON/row for reprocessing
);

-- Sync state
CREATE TABLE sync_state (
    account_id      TEXT PRIMARY KEY REFERENCES accounts(id),
    last_synced_at  INTEGER,          -- unix ms
    last_cursor     TEXT              -- for future cursor-based APIs
);
```

---

## Application Architecture

```
finance/
├── finance/
│   ├── ai/
│   │   ├── categorize.py     # LLM-based transaction categorization (Anthropic)
│   │   ├── enrich.py         # Merchant normalization, recurring detection
│   │   └── pipeline.py       # Orchestrates categorization + enrichment
│   ├── analysis/
│   │   ├── spending.py       # Category breakdowns, trends, date-range filtering
│   │   ├── net_worth.py      # Balance history, net worth over time
│   │   ├── accounts.py       # Per-account summaries
│   │   ├── overview.py       # Dashboard aggregate stats
│   │   └── review.py         # Recurring transaction detection
│   ├── ingestion/
│   │   ├── simplefin.py      # SimpleFIN API client + sync
│   │   ├── csv_import.py     # CSV normalizer per institution
│   │   ├── store.py          # DB write helpers
│   │   └── sync.py           # End-to-end sync orchestration
│   ├── web/
│   │   ├── app.py            # FastAPI routes + Jinja2 templates
│   │   └── templates/        # HTML dashboard (Tailwind CSS, Chart.js)
│   ├── db.py                 # SQLite connection + schema bootstrap
│   ├── config.py             # Settings (env vars)
│   ├── cli.py                # Click CLI (sync, import, categorize)
│   └── server.py             # MCP server (exposes financial data to Claude)
├── openspec/                 # Development specs and change history
├── data/                     # gitignored — DB files, exports
├── import/                   # gitignored — CSV exports from institutions
└── .env                      # gitignored — SimpleFIN token, API keys
```

---

## OpenClaw / MCP Integration

Expose financial data via an MCP server so any Claude session can access financial data directly:

1. Accepts natural language queries
2. Runs predefined analysis functions or translates to SQL
3. Returns structured results Claude can reason about

Example queries:
- "How much did I spend on food last month?"
- "What's my current net worth vs 3 months ago?"
- "Which credit card has the highest utilization right now?"
- "Show me all transactions over $200 in February"
- "What are my biggest spending categories this year?"

---

## AI Pipeline

Transactions pass through an LLM pipeline (Claude via Anthropic API) for:
1. **Categorization** — assigns a category from a fixed taxonomy
2. **Merchant normalization** — standardizes raw description strings to clean merchant names
3. **Recurring detection** — flags subscriptions and regular charges

All LLM calls use structured output (tool_use) for guaranteed JSON responses. The pipeline runs incrementally — only processes uncategorized transactions.

---

## Privacy
- All data stays local — SQLite file on this machine
- SimpleFIN token in `.env` (gitignored)
- Transaction database (`data/`) gitignored entirely
- CSV exports (`import/`) gitignored entirely
- No telemetry, no cloud sync
- ANTHROPIC_API_KEY sent only to Anthropic for LLM calls; no transaction data is stored by the provider beyond the API call
