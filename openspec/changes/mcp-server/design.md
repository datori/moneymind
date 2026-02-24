## Context

With data flowing into SQLite via `simplefin-sync`, we need a way to query it. This change builds the analysis layer (pure Python query functions) and exposes it through two interfaces: an MCP server (for Claude sessions) and a CLI (for testing and scripting). Both interfaces call the same underlying analysis functions.

This change builds on `project-foundation` (DB schema/connection) and `simplefin-sync` (data ingestion).

## Goals / Non-Goals

**Goals:**
- `finance/analysis/` — pure query functions over SQLite
- `finance/server.py` — MCP server exposing all tools via MCP Python SDK
- `finance/cli.py` — Click CLI with commands mirroring MCP tools
- MCP server runnable as `uv run finance-mcp`
- CLI runnable as `uv run finance <command>`

**Non-Goals:**
- AI categorization (that's `ai-categorize`)
- CSV import (that's `csv-import`)
- Web dashboard (that's `dashboard`)
- Writing/mutating data other than triggering sync

## Decisions

### D1: Analysis functions are pure — Connection as first argument

**Decision:** All analysis functions take a `sqlite3.Connection` as their first parameter. They return plain `dict` or `list[dict]` (no ORM objects, no dataclasses for now).

**Rationale:** Pure functions are easy to test (pass a test DB connection) and easy to call from any context (MCP handler, CLI command, future web server). No global state means no hidden coupling.

```python
def get_accounts(conn: Connection) -> list[dict]: ...
def get_transactions(conn: Connection, *, start_date: str | None = None, ...) -> list[dict]: ...
```

---

### D2: MCP tools are thin wrappers over analysis functions

**Decision:** Each MCP tool handler opens a DB connection, calls the relevant analysis function, and returns the result as a JSON-serializable dict. No business logic in the MCP layer.

**Rationale:** Keeps the MCP layer thin and testable independently from the MCP framework.

---

### D3: Credit limits — graceful null for unconfigured cards

**Decision:** `get_credit_utilization()` returns `utilization_pct: null` for credit accounts without a row in `credit_limits`. It does NOT raise an error.

**Rationale:** Users may not configure limits immediately. The tool should still return partial data rather than failing entirely.

---

### D4: `sync()` MCP tool delegates to ingestion module

**Decision:** The `sync()` MCP tool calls `finance.ingestion.simplefin.sync_all(conn)` directly (not via subprocess).

**Rationale:** In-process call is simpler and faster. The MCP server already has the DB connection and env vars loaded.

---

### D5: CLI uses Click, outputs as table (human) or JSON (--json flag)

**Decision:** All CLI commands support a `--json` flag for machine-readable output. Default output is a formatted table using Python's built-in `textwrap`/string formatting (no rich/tabulate dependency).

**Rationale:** `--json` makes the CLI composable with scripts. Avoiding `rich` or `tabulate` keeps dependencies minimal.

---

### D6: `get_net_worth` uses latest balance snapshot per account

**Decision:** Net worth is calculated as the sum of the most recent `balances` snapshot per account, grouped by account type (assets vs liabilities).

**Rationale:** Balance snapshots are append-only. Latest-per-account is the canonical "current" state.

Asset/liability classification:
- Assets: checking, savings, investment
- Liabilities: credit (balance is negative, so absolute value is owed), loan

---

### D7: `get_spending_summary` filters to debit transactions only

**Decision:** Spending summaries (`group_by=category/merchant/account`) sum `amount` for negative-amount transactions (debits) only. Credits/refunds are excluded unless explicitly requested.

**Rationale:** "Spending" semantically means money going out. Including credits/refunds would understate spending in ways that are confusing.

## Risks / Trade-offs

- **`sync()` as MCP tool adds write capability** → For a personal single-user MCP server this is fine and useful ("Claude, sync my accounts"). Not appropriate for multi-user deployment.
- **No pagination on `get_transactions`** → The `limit` parameter is the only guard. For a personal finance system with ~1000-3000 transactions/year, this is acceptable. A `offset` parameter can be added later if needed.

## Open Questions

None — all decisions resolved.
