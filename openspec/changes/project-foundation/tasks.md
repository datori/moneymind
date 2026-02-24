## 1. Python Project Setup

- [ ] 1.1 Create `pyproject.toml` with project metadata, Python 3.12+ requirement, and dependencies: `mcp`, `httpx`, `click`, `python-dotenv`
- [ ] 1.2 Add entry points in `pyproject.toml`: `finance = "finance.cli:main"` and `finance-mcp = "finance.server:main"`
- [ ] 1.3 Run `uv sync` to generate `uv.lock` and verify the project installs cleanly
- [ ] 1.4 Create `finance/__init__.py` (empty)

## 2. Package Structure

- [ ] 2.1 Create `finance/ingestion/__init__.py` (empty stub)
- [ ] 2.2 Create `finance/analysis/__init__.py` (empty stub)
- [ ] 2.3 Create `finance/ai/__init__.py` (empty stub)
- [ ] 2.4 Create `finance/server.py` stub: imports `mcp`, defines `main()` function with a placeholder `print("MCP server not yet implemented")`
- [ ] 2.5 Create `finance/cli.py` stub: defines a Click group `main` with `--help` output, no subcommands yet

## 3. Database Module

- [ ] 3.1 Create `finance/db.py` with `DATABASE_PATH` loaded from env (default `data/finance.db`)
- [ ] 3.2 Implement `get_connection() -> sqlite3.Connection` — opens DB, sets `row_factory = sqlite3.Row`, enables WAL mode (`PRAGMA journal_mode=WAL`)
- [ ] 3.3 Implement `init_db(conn: Connection)` — runs all `CREATE TABLE IF NOT EXISTS` statements for: `institutions`, `accounts`, `balances`, `transactions`, `sync_state`, `credit_limits`
- [ ] 3.4 Add `categorized_at INTEGER` column to `transactions` schema (as specified in design)
- [ ] 3.5 Add `credit_limits` table to schema (as specified in design)

## 4. Configuration and Environment

- [ ] 4.1 Create `.env.example` with commented entries: `DATABASE_PATH=data/finance.db`, `SIMPLEFIN_ACCESS_URL=`, `ANTHROPIC_API_KEY=`
- [ ] 4.2 Create `data/.gitkeep` so the `data/` directory is tracked but its contents are not
- [ ] 4.3 Verify `.gitignore` covers `*.db`, `*.sqlite`, `.env`, `data/` (already in place, just confirm)

## 5. Verification

- [ ] 5.1 Verify `uv run python -c "import finance"` exits 0
- [ ] 5.2 Verify `uv run python -c "from finance.db import init_db, get_connection; conn = get_connection(); init_db(conn)"` exits 0 and creates `data/finance.db`
- [ ] 5.3 Verify `uv run finance --help` prints help text and exits 0
- [ ] 5.4 Verify `uv run finance-mcp --help` (or at minimum exits without import error)
