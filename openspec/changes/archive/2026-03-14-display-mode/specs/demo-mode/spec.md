## ADDED Requirements

### Requirement: Demo mode activates via query parameter
Any route that accepts `?demo=1` as a query parameter SHALL render with synthetic data from `data/demo.db` instead of the real database. The real database (`data/finance.db`) MUST NOT be opened or modified when demo mode is active.

#### Scenario: GET route with demo param uses demo database
- **WHEN** a GET request is made to any page route with `?demo=1`
- **THEN** the response renders with data sourced from `data/demo.db`

#### Scenario: GET route without demo param uses real database
- **WHEN** a GET request is made to any page route without `?demo=1`
- **THEN** the response renders with data sourced from `data/finance.db`

#### Scenario: Real database untouched in demo mode
- **WHEN** any request is made with `?demo=1`
- **THEN** `data/finance.db` is never opened, read, or written

### Requirement: Demo banner displayed in demo mode
When demo mode is active, the base template SHALL display a visible banner indicating the user is viewing demo data.

#### Scenario: Banner present in demo mode
- **WHEN** a page is rendered with `?demo=1`
- **THEN** a "Demo Mode" banner is visible on the page

#### Scenario: Banner absent in normal mode
- **WHEN** a page is rendered without `?demo=1`
- **THEN** no demo banner is displayed

### Requirement: Dangerous mutations blocked in demo mode
The `/sync` and `/pipeline/run/stream` routes SHALL return HTTP 400 when `?demo=1` is present, to prevent external API calls.

#### Scenario: Sync blocked in demo mode
- **WHEN** POST `/sync` is called with `?demo=1`
- **THEN** the server returns HTTP 400 without calling SimpleFIN

#### Scenario: Pipeline stream blocked in demo mode
- **WHEN** GET `/pipeline/run/stream` is called with `?demo=1`
- **THEN** the server returns HTTP 400 without calling the Anthropic API

#### Scenario: Sync allowed in normal mode
- **WHEN** POST `/sync` is called without `?demo=1`
- **THEN** the sync proceeds normally

### Requirement: Safe mutations operate against demo database
All non-dangerous mutation routes (review approval, recurring cancel/resolve/delete, account delete) SHALL operate against `data/demo.db` when demo mode is active.

#### Scenario: Review approval in demo mode modifies demo database only
- **WHEN** POST `/review/{id}/approve` is called (directly, not from a browser with ?demo=1)
- **THEN** the transaction `needs_review` flag is updated in `demo.db`
- **THEN** `finance.db` is not modified

### Requirement: Demo database pre-seeded with realistic synthetic data
A `data/demo.db` file SHALL be committed to the repository, pre-seeded with synthetic financial data sufficient to make all dashboard pages appear populated and realistic.

#### Scenario: All pages render without empty states in demo mode
- **WHEN** any dashboard page is loaded with `?demo=1`
- **THEN** charts, tables, and summaries contain synthetic data (not empty states)

#### Scenario: Demo database covers required data types
- **WHEN** `data/demo.db` is inspected
- **THEN** it contains: at least 4 accounts (checking, savings, credit, investment), at least 6 months of transactions, balance history, recurring merchants, and items in the review queue

### Requirement: Demo seed script is runnable
A script at `finance/demo/seed.py` SHALL generate (or regenerate) `data/demo.db` deterministically, applying the current schema before inserting synthetic data.

#### Scenario: Seed script produces valid demo database
- **WHEN** `python -m finance.demo.seed` is run
- **THEN** `data/demo.db` is created (or overwritten) with all tables initialized and synthetic data inserted

#### Scenario: Seed script is idempotent
- **WHEN** `python -m finance.demo.seed` is run multiple times
- **THEN** each run produces a clean, consistent `data/demo.db` without accumulating duplicate data
