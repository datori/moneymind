## 1. Database Migration

- [x] 1.1 Add `summary TEXT` column to `run_log` in `finance/db.py` `_SCHEMA` and add an `ALTER TABLE run_log ADD COLUMN summary TEXT` migration in `init_db()` (wrapped in try/except `OperationalError` to be idempotent)

## 2. Pipeline Analytics — pipeline.py

- [x] 2.1 In `_apply_results()`, change `categories_assigned` collection from a flat list to a `dict[str, int]` that counts assignments per category; update the `response_summary` JSON written to `run_steps`
- [x] 2.2 In `run_pipeline()`, snapshot `COUNT(*)` from transactions before and after the sync step call; write `response_summary = json.dumps({"accounts_synced": N, "new_transactions": delta})` to the sync `run_steps` row
- [x] 2.3 In `run_pipeline()`, after `_build_clusters()`, write `response_summary = json.dumps({"transaction_count": N, "cluster_count": M})` to the cluster-build `run_steps` row
- [x] 2.4 At run completion (both success and failure paths), compute and write `run_log.summary`: aggregate `transactions_enriched` (sum of `response_summary.transactions_updated` from write-results step), `categories` dict (merged across all batch `response_summary.categories_assigned` dicts), `recurring_count`, `review_count` (query transactions table), `tokens_in`/`tokens_out` (sum from all enrich-batch steps), `batches_processed`, `clusters_built`, `transactions_synced`

## 3. Pipeline Route — app.py

- [x] 3.1 In `GET /pipeline` route, add a query for current transaction state: total count, uncategorized count (`category IS NULL`), recurring count (`is_recurring = 1`), review queue count (`needs_review = 1`), and category distribution (`SELECT category, COUNT(*) ... GROUP BY category ORDER BY count DESC`)
- [x] 3.2 Pass current state data to `pipeline.html` template as `current_state` dict with keys: `total`, `uncategorized`, `recurring`, `needs_review`, `categories` (list of `{category, count}`)
- [x] 3.3 Update the run history query to include `summary` column from `run_log` (already selected if using `SELECT *`, otherwise add explicitly)

## 4. Pipeline Template — pipeline.html

- [x] 4.1 Add "Current State" panel at the top of the page showing: total transactions, uncategorized (with warning color if > 0), recurring count, review queue count; and a compact category table/list showing top categories with counts
- [x] 4.2 In the run history table, add Txns column (from `run.summary.transactions_enriched`, or "—" if null) and Tokens column (sum of `tokens_in + tokens_out` from summary, or "—" if null)
- [x] 4.3 In the SSE JavaScript handler, when a `step_done` event for an `enrich-batch` arrives, parse `response_summary.categories_assigned` and render top-5 categories as pill badges (with ×N count suffix when count > 1) appended to that batch's step row
