## ADDED Requirements

### Requirement: Python package structure
The system SHALL be organized as a `finance` Python package at the root of the repository, installable via `uv`.

Expected layout:
```
finance/
├── __init__.py
├── db.py
├── ingestion/
│   └── __init__.py
├── analysis/
│   └── __init__.py
├── ai/
│   └── __init__.py
├── server.py        (stub)
└── cli.py           (stub)
```

#### Scenario: Package importable
- **WHEN** `uv run python -c "import finance"` is executed
- **THEN** the command exits with code 0

#### Scenario: DB module importable
- **WHEN** `uv run python -c "from finance.db import init_db, get_connection"` is executed
- **THEN** the command exits with code 0

---

### Requirement: pyproject.toml defines entry points
The system SHALL define two entry points in `pyproject.toml`:
- `finance` → `finance.cli:main` (Click CLI)
- `finance-mcp` → `finance.server:main` (MCP server)

#### Scenario: CLI entry point available
- **WHEN** `uv run finance --help` is executed after installation
- **THEN** the command outputs help text and exits with code 0

#### Scenario: MCP entry point available
- **WHEN** `uv run finance-mcp --help` is executed after installation
- **THEN** the command outputs help text and exits with code 0

---

### Requirement: Environment configuration
The system SHALL read configuration from environment variables, with `.env` file support via `python-dotenv`.

Required variables:
- `DATABASE_PATH` — path to SQLite file (default: `data/finance.db`)
- `SIMPLEFIN_ACCESS_URL` — SimpleFIN access URL (required for sync)
- `ANTHROPIC_API_KEY` — Claude API key (required for categorization)

#### Scenario: .env.example committed
- **WHEN** the repository is cloned
- **THEN** `.env.example` exists at the root with all required variable names and placeholder values

#### Scenario: Missing optional variable
- **WHEN** `SIMPLEFIN_ACCESS_URL` is not set and `finance sync` is not invoked
- **THEN** no error is raised at startup

---

### Requirement: data/ directory gitignored
The system SHALL gitignore the `data/` directory where SQLite files are stored.

#### Scenario: Database not committed
- **WHEN** `git status` is run after `init_db()` creates the database
- **THEN** the `.db` file does not appear as an untracked file
