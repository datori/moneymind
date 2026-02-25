## Context

The pipeline already records `run_log` and `run_steps` rows with token counts and timing. However several gaps exist:

1. `run_log` has no aggregate summary column — the history table can't show "how many transactions did this run process?" without joining all steps.
2. The `sync` and `cluster-build` steps never wrote their `response_summary` to `run_steps` — those rows are null today.
3. `categories_assigned` in `enrich-batch` response_summary is a flat list, making it hard to aggregate or display counts.
4. The `/pipeline` page has no live view into current transaction state — you have to go to the Transactions page to know how many are uncategorized or in the review queue.
5. The live streaming panel shows token counts per batch but not what categories were assigned.

## Goals / Non-Goals

**Goals:**
- Add `summary` JSON column to `run_log` with aggregate analytics written on run completion
- Fix `sync` and `cluster-build` steps to write `response_summary` to `run_steps`
- Convert `categories_assigned` to a count dict in batch response summaries
- Add "Current State" panel on `/pipeline` page (live query, not from run_log)
- Show per-batch category pills in the live streaming panel
- Add Txns and Tokens columns to the run history table

**Non-Goals:**
- Historical trend charts (not this change)
- Real-time category state pushed via SSE (the Current State panel is static on page load)
- Modifying MCP tools or CLI output format
- Backfilling analytics for old runs (null summary = pre-analytics run, shown as "—")

## Decisions

### 1. Where to store aggregate run analytics: `run_log.summary` column

**Decision**: Add a single `summary TEXT` (JSON) column to `run_log`, written once at run completion.

**Rationale**: Alternatives considered:
- *Join `run_steps` on read*: Viable for token sums but not for category distribution (categories are spread across multiple batch response_summary JSONs and require JSON parsing + merging in Python or complex SQL). Doing this inline in every `/pipeline` page load is fragile.
- *Separate `run_analytics` table*: Unnecessary overhead for a single aggregate row per run.
- *Inline in `run_log.summary`*: Clean, one-row per run, queryable via `json_extract` if ever needed, written once.

**Migration**: `ALTER TABLE run_log ADD COLUMN summary TEXT` — SQLite allows this without rebuilding.

### 2. categories_assigned format: list → count dict

**Decision**: Change `categories_assigned` in `_apply_results()` from a flat list of category strings to a `dict[str, int]` counting assignments per category.

**Rationale**: The current flat list was designed for simple inspection but can be very long (e.g., `["Dining", "Dining", "Subscriptions & Software", ...]`). A count dict is:
- Smaller serialized size
- Directly renderable as pills with counts
- Easily merged across batches for aggregate summary

**Compatibility**: The flat list is only used in `run_steps.response_summary` (internal only, not exposed via MCP or API). No migration of old rows needed — they predate analytics.

### 3. Current State panel: live query vs. from last run summary

**Decision**: Query the transactions table directly on each `/pipeline` page load for Current State data.

**Rationale**: `run_log.summary` only captures what changed during a run. The "current state" panel should reflect reality (e.g., if someone manually fixed a category, that should show up). A direct query is cheap for a single-user SQLite DB with <500 transactions, and it's simpler than trying to reconcile incremental run summaries.

### 4. sync step analytics: count new transactions

**Decision**: Track `new_transactions` as the delta between pre-sync and post-sync transaction counts.

**Rationale**: The existing `sync_simplefin()` call doesn't return a count. Easiest approach is to query `COUNT(*)` from transactions before and after the sync call and diff them. This is a read-only query, safe to add around the sync call.

## Risks / Trade-offs

- **`ALTER TABLE` on run_log**: Safe in SQLite (no rebuild), but if the app is running during migration there's a tiny window. Not a concern for a single-user local app.
- **categories count dict size**: A run processing 400 transactions across 15 categories generates a dict with at most 15 keys (~200 bytes). Well within any practical limit.
- **Current State query performance**: `SELECT category, COUNT(*) FROM transactions GROUP BY category` with <1000 rows is instant. No index needed.
- **Old run_steps rows have null response_summary for sync/cluster-build**: Acceptable — the analytics feature simply didn't exist. The UI handles nulls with "—".

## Migration Plan

1. `ALTER TABLE run_log ADD COLUMN summary TEXT` — run on startup if column absent (use `PRAGMA table_info` check or `ALTER TABLE` wrapped in try/except on `OperationalError: duplicate column`).
2. Deploy updated `pipeline.py` and `app.py`.
3. Old runs show "—" in Txns/Tokens columns — no data loss, just missing analytics for pre-migration runs.
4. No rollback complexity: if reverted, the extra column is ignored by older code.

## Open Questions

- None — scope is well-defined and confined to internal analytics data.
