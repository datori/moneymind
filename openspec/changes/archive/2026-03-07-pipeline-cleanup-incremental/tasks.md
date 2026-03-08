## 1. Remove deprecated auto-categorize from ingestion

- [x] 1.1 Remove `categorize_uncategorized()` call from `finance/ingestion/sync.py:sync_all()` (lines 123-130: the `if os.getenv("ANTHROPIC_API_KEY")` block)
- [x] 1.2 Remove `categorize_uncategorized()` call from `finance/ingestion/csv_import.py:import_csv()` (lines 669-676: the `if os.getenv("ANTHROPIC_API_KEY")` block)
- [x] 1.3 Remove `enrich_transactions()` call from `finance/cli.py:_sync_run()` (lines 88-96: the pass-2 enrichment block after sync)
- [x] 1.4 Remove `enrich_transactions()` call from `finance/cli.py:categorize()` (lines 658-666: the pass-2 enrichment block after categorize)

## 2. Add pipeline reminder to sync output

- [x] 2.1 Add reminder message to `finance/cli.py:_sync_run()` — after printing sync summary, if `result['new_transactions'] > 0`, print: "Run `finance pipeline` to categorize new transactions."

## 3. Add incremental cluster filtering to pipeline

- [x] 3.1 Add `full: bool = False` parameter to `run_pipeline()` signature in `finance/ai/pipeline.py`
- [x] 3.2 After `_build_clusters()`, add filtering logic: query `categorized_at` for all transaction IDs in each cluster; keep only clusters where at least one transaction has `categorized_at IS NULL`. Skip filtering when `full=True`.
- [x] 3.3 Track `clusters_total` (pre-filter count) and `clusters_skipped` (filtered out count) for reporting
- [x] 3.4 Update cluster-build `run_steps` row to include `clusters_total` and `clusters_skipped` in `response_summary`
- [x] 3.5 Update cluster-build `step_done` emit event to include `clusters_skipped` in `data`
- [x] 3.6 Update run_log `summary` JSON to include `clusters_skipped` field
- [x] 3.7 Handle edge case: if all clusters are filtered out in incremental mode, complete the run with success and 0 batches (same as the existing empty-clusters path)

## 4. Add --full flag to CLI

- [x] 4.1 Add `--full` click option to `finance pipeline` command in `finance/cli.py`
- [x] 4.2 Pass `full=` parameter through to `run_pipeline()` call

## 5. Verify and clean up

- [x] 5.1 Verify `finance sync` no longer makes LLM API calls (check no anthropic imports execute in sync path)
- [x] 5.2 Verify `finance import` no longer makes LLM API calls
- [x] 5.3 Verify `finance pipeline` in incremental mode skips fully-categorized clusters
- [x] 5.4 Verify `finance pipeline --full` processes all clusters
- [x] 5.5 Verify web dashboard `POST /sync` still works (it calls `sync_all()` which no longer categorizes)
- [x] 5.6 Verify web dashboard `GET /pipeline/run/stream` still works with incremental pipeline
