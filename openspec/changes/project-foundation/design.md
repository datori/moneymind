## Context

Starting from an empty directory (two commits: gitignore + proposal). No existing code to migrate. This change lays the skeleton that every subsequent change builds on — schema, package structure, DB client, and project config.

## Goals / Non-Goals

**Goals:**
- Working Python package installable via `uv`
- SQLite database that initializes from code (no external migration tool)
- Consistent, importable module structure for all future changes
- `.env.example` as the contract for required configuration

**Non-Goals:**
- Any data ingestion logic
- Any analysis or query functions
- CLI commands beyond a stub entry point
- MCP server

## Decisions

### D1: uv over poetry/pip-tools

**Decision:** Use `uv` with `pyproject.toml`.

**Rationale:** `uv` is dramatically faster than pip, handles both venv and package management in one tool, and produces a lockfile (`uv.lock`) without ceremony. For a single-user scripts project this is the lowest-friction modern Python setup.

**Alternatives considered:** `poetry` (heavier, slower), plain `requirements.txt` (no lockfile, no entry points).

---

### D2: Flat package layout (no `src/`)

**Decision:** `finance/` package at root, not `src/finance/`.

**Rationale:** `src/` layout prevents accidental imports from the root during development — a valuable guard for library packages published to PyPI. This project is never published; `src/` adds indirection with no benefit.

**Alternatives considered:** `src/finance/` layout — rejected as unnecessary overhead.

---

### D3: Raw sqlite3 with row_factory, no ORM

**Decision:** Use Python's stdlib `sqlite3` directly. Set `row_factory = sqlite3.Row` so rows behave like dicts.

**Rationale:** SQLAlchemy or any ORM adds significant complexity and abstraction overhead. At this scale (one person, one DB file), raw SQL is clearer, easier to debug, and has zero dependencies. DuckDB can be run against the same file for complex analytical queries if needed.

**Alternatives considered:** SQLAlchemy Core (rejected — extra dep, adds query builder complexity), SQLModel (rejected — same).

---

### D4: Schema inline in `db.py`, WAL mode on by default

**Decision:** Schema defined as a string constant in `db.py`, applied in `init_db()`. WAL (Write-Ahead Logging) mode enabled on every connection open.

**Rationale:** A separate `.sql` file adds no value — the schema is small (~50 lines) and having it in Python avoids the need to locate and read a separate file at runtime. WAL mode is strictly better for this use case: faster reads, no blocking between reader and writer, crash-safe.

---

### D5: `categorized_at` column on transactions

**Decision:** Add `categorized_at INTEGER` (unix ms) to the `transactions` table.

**Rationale:** Without this, there's no way to know which transactions have been through the AI categorizer vs. which are still raw. Required by the `ai-categorize` change. Better to add it now than migrate later.

---

### D6: `credit_limits` table

**Decision:** Add a `credit_limits` table to store manually-configured credit limits per account.

**Rationale:** SimpleFIN does not reliably provide credit limits. The `get_credit_utilization()` MCP tool needs limit data. Rather than hard-coding in `.env` or a config file, a DB table allows the CLI to manage limits with standard CRUD commands.

```sql
CREATE TABLE credit_limits (
    account_id   TEXT PRIMARY KEY REFERENCES accounts(id),
    credit_limit REAL NOT NULL,
    updated_at   INTEGER NOT NULL  -- unix ms
);
```

---

### D7: No migration framework

**Decision:** `init_db()` uses `CREATE TABLE IF NOT EXISTS`. Schema changes require manual ALTER or a recreate-from-backup.

**Rationale:** This is a single-user personal tool. The data can be re-imported from SimpleFIN/CSV at any time. Alembic or similar adds ceremony not worth the overhead. If a breaking schema change is needed, it will be handled ad-hoc.

## Risks / Trade-offs

- **No migrations** → Schema evolution requires manual SQL. Acceptable given data is always re-importable from source.
- **WAL mode** → Creates `-wal` and `-shm` sidecar files next to the DB. Not a problem locally, just needs to be documented (and these files are already gitignored via `*.db`).
- **`credit_limits` manual entry** → Credit utilization only works for cards where limits are configured. MCP tool must handle missing limits gracefully (return null utilization for unconfigured cards).

## Open Questions

None — all decisions above are resolved.
