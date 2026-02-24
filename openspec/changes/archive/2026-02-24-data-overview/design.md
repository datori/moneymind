## Context

The system mixes two data sources with very different temporal ranges: SimpleFIN provides a rolling 90-day window refreshed on each sync, while CSV imports can reach back years. Currently there is no way to inspect what is actually stored — how many transactions, which date ranges, or when each account was last synced. This creates uncertainty about data freshness and coverage gaps.

The existing `finance/analysis/` pattern is well-established: pure functions taking a `sqlite3.Connection`, returning plain dicts. The web layer (FastAPI + Jinja2) and CLI (Click) both call into this layer directly. The database schema has everything needed: `transactions` (with `date`, `account_id`), `accounts` (with `name`), `balances` (snapshot history), `sync_state` (per-account `last_synced_at`), and `institutions` (for the institution name).

## Goals / Non-Goals

**Goals:**
- Add a single `get_data_overview(conn)` analysis function that returns global and per-account coverage data in one query round-trip
- Expose coverage data on the web `/accounts` page (added section below existing balance table) and a dedicated `/data` route
- Add a `finance data` CLI command using the same analysis function
- No new dependencies, no schema changes

**Non-Goals:**
- Detecting or filling coverage gaps automatically
- Showing per-source (SimpleFIN vs CSV) breakdowns — account-level granularity is sufficient for now
- MCP tool exposure (this is observability, not analysis Claude needs to invoke)
- Pagination or export of the overview data

## Decisions

### Decision: Single `get_data_overview` function, two sub-dicts

Return `{"global": {...}, "per_account": [...]}` from one function. The global stats are derivable from per-account aggregation in SQL, avoiding two separate calls. The web and CLI both consume the same dict without reshaping.

Alternative considered: two separate functions (`get_global_coverage`, `get_per_account_coverage`). Rejected because they always appear together on every surface; a single function avoids two DB round-trips and keeps the call site simple.

### Decision: Compute coverage via SQL aggregation, not Python post-processing

Use `MIN(t.date)`, `MAX(t.date)`, `COUNT(t.id)` grouped by `account_id` in a single LEFT JOIN query against `transactions`, joined to `accounts`, `sync_state`, and `balances`. This keeps the Python function small and the query efficient even for large transaction sets.

Alternative considered: fetch all transactions into Python and aggregate. Rejected — unnecessary data transfer for a display-only feature.

### Decision: Enhance `/accounts` in place; add `/data` as a separate route

The `/accounts` page already shows the balance table. Appending a "Data Coverage" section below keeps related account information together without splitting the user's mental model. The separate `/data` route gives a full-page view for users who want to focus solely on data coverage, and can be linked from the nav.

Alternative considered: replace `/accounts` entirely with a combined page and drop the separate `/data` route. Rejected — the two concerns (current balances vs. historical coverage) are distinct enough to warrant a dedicated page for coverage.

### Decision: Format date range as "Mon YY – Mon YY" (abbreviated month + 2-digit year)

Compact, human-readable, and fits in a table column without wrapping. The global summary line uses "Z months" computed as the number of calendar months between earliest and latest transaction dates across all accounts.

Alternative considered: ISO dates (YYYY-MM-DD). Rejected — too verbose for a coverage summary.

### Decision: `last_synced_at` displayed as relative time ("3 days ago") in the web UI; absolute in CLI

Relative time communicates freshness more naturally in the browser. The CLI output is typically piped or read in a terminal where an absolute timestamp is more useful.

## Risks / Trade-offs

- **Accounts with no transactions**: The LEFT JOIN will return NULL for `earliest_txn`, `latest_txn`, `txn_count`. Templates and CLI must render these gracefully (e.g., "—" or "No data"). This is expected and handled in the spec.
- **`last_synced_at` NULL**: SimpleFIN-synced accounts always populate `sync_state`; CSV-imported accounts may not. Display "Never" when NULL.
- **Global months calculation with gaps**: "Z months" is computed from absolute date range (latest − earliest), not number of months with transactions. A large gap in the middle will inflate the count. Acceptable for a personal tool; if misleading, a future change can refine it.

## Migration Plan

No schema changes and no breaking API changes. Rollout is additive:
1. Add `finance/analysis/overview.py`
2. Add `GET /data` route and template; pass overview data to existing `/accounts` route
3. Add `finance data` CLI command

Rollback: revert the three file changes. No data migration required.

## Open Questions

None — requirements are well-defined and the existing patterns fully cover the implementation approach.
