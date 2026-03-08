## Why

The pipeline has three problems that compound as the transaction database grows:

1. **Deprecated code still active**: `sync_all()` and `import_csv()` both call deprecated `categorize_uncategorized()`, which triggers the old two-pass LLM flow. This means `finance sync` silently burns LLM tokens on the deprecated path, and those calls have no cost tracking. The modern `run_pipeline()` then re-processes everything again.

2. **Full re-processing on every run**: `_build_clusters()` loads ALL transactions and sends ALL clusters to the LLM, even if every transaction is already categorized. With growing data, this is O(n) API cost per pipeline run — wasteful for routine syncs that add 5-10 new transactions.

3. **Hidden LLM costs**: The deprecated auto-categorize calls embedded in `sync_all()` and `import_csv()` consume tokens with zero cost tracking. Only `run_pipeline()` logs to `run_log`/`run_steps`.

## What Changes

- **Remove deprecated auto-categorize from `sync_all()`**: Sync becomes purely about data fetching — no LLM calls. The `categorize_uncategorized()` call inside `sync_all()` is removed.
- **Remove deprecated auto-categorize from `import_csv()`**: CSV import becomes purely about data ingestion — no LLM calls.
- **Remove deprecated auto-enrich from `finance sync` CLI**: The `enrich_transactions()` call in the CLI `_sync_run()` is removed.
- **Remove deprecated auto-enrich from `finance categorize` CLI**: The `enrich_transactions()` call in the `categorize` command is removed.
- **Add incremental mode to `run_pipeline()`**: Build clusters from ALL transactions (preserving LLM context), but only send clusters containing at least one uncategorized transaction. Add `--full` flag to bypass the filter for taxonomy changes.
- **Update `finance pipeline` CLI**: Add `--full` flag that forces re-processing of all clusters.

## Capabilities

### New Capabilities

_(none — this change modifies existing capabilities)_

### Modified Capabilities

- `transaction-categorization`: Remove requirement for auto-categorize after sync/import. Remove requirement for auto-enrich after sync/categorize. Add deprecation removal timeline for old functions.
- `simplefin-ingestion`: Remove requirement that sync triggers auto-categorization.
- `csv-ingestion`: Remove requirement that CSV import triggers auto-categorization.
- `pipeline-streaming`: Add incremental processing mode — pipeline only sends clusters with uncategorized transactions by default, with `--full` override. Update `cluster-build` step to report filtered vs total cluster counts.
- `pipeline-run-analytics`: Update cluster-build response_summary to include `clusters_skipped` count for incremental runs.

## Impact

- **`finance/ingestion/sync.py`**: Remove `categorize_uncategorized()` import and call
- **`finance/ingestion/csv_import.py`**: Remove `categorize_uncategorized()` import and call
- **`finance/cli.py`**: Remove `enrich_transactions()` calls from `_sync_run()` and `categorize` command
- **`finance/ai/pipeline.py`**: Modify `_build_clusters()` to accept filter mode; modify `run_pipeline()` to support incremental vs full; add `--full` parameter
- **`finance/ai/categorize.py`**: No changes (remains deprecated but functional)
- **`finance/ai/enrich.py`**: No changes (remains deprecated but functional)
- **User workflow change**: After `finance sync`, users must explicitly run `finance pipeline` to categorize new transactions. The web dashboard "Sync" button already only calls `sync_all()` (no pipeline), so web users already need to click "Run Pipeline" separately — no behavior change there.
