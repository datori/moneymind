## Why

Sharing the dashboard with others (or demoing it publicly) currently exposes real financial data. A `?demo=1` query parameter mode lets the app render with realistic but synthetic data on any page without touching or risking real user data.

## What Changes

- Add a `demo` query parameter (`?demo=1`) to any route to render that page with synthetic data
- Add a visible "Demo Mode" banner to the base template when active
- Pre-seed a `data/demo.db` SQLite file with synthetic accounts, transactions, balance history, and recurring charges
- `get_db()` dependency checks for `?demo=1` and returns a connection to `demo.db` instead of the real database
- Dangerous external-call routes (`/sync`, `/pipeline/run/stream`) return HTTP 400 in demo mode
- All other mutations (approve review, cancel/resolve recurring, delete account) operate against `demo.db` — real data is never touched

## Capabilities

### New Capabilities

- `demo-mode`: Query-param-triggered display mode that swaps the database connection to a pre-seeded synthetic dataset; surfaces a banner; blocks dangerous mutations

### Modified Capabilities

<!-- none -->

## Impact

- `finance/web/app.py`: `get_db` dependency, two route guards for `/sync` and `/pipeline/run/stream`, banner context var threaded to all template responses
- `finance/web/templates/base.html`: Demo banner
- New `finance/demo/seed.py`: Script to generate `data/demo.db`
- New `data/demo.db`: Pre-seeded synthetic SQLite database (committed to repo)
- No changes to analysis functions, ingestion, or AI pipeline
