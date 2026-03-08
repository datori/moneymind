## MODIFIED Requirements

### Requirement: cluster-build step persists response summary

The `cluster-build` pipeline step SHALL write a `response_summary` JSON to its `run_steps` row with: `{"transaction_count": N, "cluster_count": M, "clusters_total": T, "clusters_skipped": S}`.

- `cluster_count`: number of clusters that will be sent to the LLM (after filtering in incremental mode)
- `clusters_total`: total number of clusters built from all transactions
- `clusters_skipped`: number of clusters filtered out because all transactions were already categorized (`clusters_total - cluster_count`)
- `transaction_count`: total transactions across clusters to be processed

#### Scenario: Cluster-build step records counts in incremental mode
- **WHEN** `_build_clusters()` completes in incremental mode
- **AND** 200 total clusters are built, 195 are fully categorized, 5 have new transactions
- **THEN** the `run_steps` row for `step_type = 'cluster-build'` has `response_summary` with `cluster_count: 5`, `clusters_total: 200`, `clusters_skipped: 195`

#### Scenario: Cluster-build step records counts in full mode
- **WHEN** `_build_clusters()` completes in full mode
- **THEN** `clusters_skipped` is `0` and `cluster_count` equals `clusters_total`

---

### Requirement: run_log aggregate summary column

The `run_log` table SHALL have a `summary` TEXT column (JSON) that is populated on run completion with aggregate analytics across all steps in that run.

The summary JSON SHALL include at minimum:
```json
{
  "transactions_synced": N,
  "clusters_built": M,
  "clusters_skipped": S,
  "batches_processed": K,
  "transactions_enriched": P,
  "categories": {"Subscriptions & Software": 3, "Dining": 2},
  "recurring_count": R,
  "review_count": V,
  "tokens_in": T1,
  "tokens_out": T2
}
```

The `clusters_skipped` field SHALL be included to provide visibility into how much work was saved by incremental mode.

#### Scenario: Run completes with full summary
- **WHEN** `run_pipeline()` completes successfully
- **THEN** the `run_log` row is updated with a JSON `summary` containing aggregate counts from all steps, including `clusters_skipped`

#### Scenario: Run fails before enrichment
- **WHEN** the pipeline fails before any LLM step completes
- **THEN** the `run_log` `summary` is NULL (not written)
