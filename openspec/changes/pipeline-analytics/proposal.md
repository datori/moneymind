## Why

The pipeline view currently shows only basic run status and token counts — it doesn't tell us what actually happened: how many transactions were processed, what categories were assigned, how many were flagged for review, or what the current state of the transaction data looks like. Richer analytics make the pipeline actionable and give confidence that enrichment is working correctly.

## What Changes

- Add a `summary` JSON column to `run_log` to store aggregate analytics at run completion (transactions processed, categories assigned by type, recurring count, review count, tokens used)
- Fix `sync` and `cluster-build` pipeline steps to persist their response summaries to `run_steps` (currently null)
- Convert `categories_assigned` from a flat list to a count dict in batch response summaries (e.g., `{"Subscriptions & Software": 3, "Dining": 2}`)
- Add a "Current State" panel to the `/pipeline` page showing live category distribution, recurring count, and review queue depth (queried directly from transactions table)
- Show per-batch category breakdown in the live streaming SSE view alongside existing token counts
- Add Txns and Tokens aggregate columns to the run history table on `/pipeline`

## Capabilities

### New Capabilities
- `pipeline-run-analytics`: Structured analytics captured per pipeline run — aggregate summary stored in `run_log.summary`, per-batch category counts in `run_steps.response_summary`, sync and cluster-build step summaries persisted

### Modified Capabilities
- `web-dashboard`: The `/pipeline` page gains a "Current State" panel (live category distribution, recurring, review counts) and richer run history table (Txns, Tokens columns)

## Impact

- `finance/db.py`: Add `summary TEXT` column to `run_log` table (migration needed)
- `finance/ai/pipeline.py`: Capture aggregate stats at run end; fix sync/cluster-build step persistence; change categories_assigned to count dict
- `finance/web/app.py`: `/pipeline` route queries current transaction state for "Current State" panel
- `finance/web/templates/pipeline.html`: New "Current State" panel; per-batch category rows in live view; Txns/Tokens columns in history table
