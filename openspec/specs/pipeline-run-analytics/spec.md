## ADDED Requirements

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
  "categories": {"Subscriptions & Software": 3, "Dining": 2, ...},
  "recurring_count": R,
  "review_count": V,
  "tokens_in": T1,
  "tokens_out": T2
}
```

The `clusters_skipped` field SHALL be included to provide visibility into how much work was saved by incremental mode.

The `summary` column SHALL be NULL while the run is in `running` status and only written on final status update.

#### Scenario: Run completes with full summary
- **WHEN** `run_pipeline()` completes successfully
- **THEN** the `run_log` row is updated with a JSON `summary` containing aggregate counts from all steps
- **THEN** the `categories` field is a dict mapping category name to count of transactions assigned that category

#### Scenario: Run fails before enrichment
- **WHEN** the pipeline fails before any LLM step completes
- **THEN** the `run_log` `summary` is NULL (not written)

---

### Requirement: categories_assigned as count dict in batch response_summary

For `enrich-batch` run_steps rows, the `response_summary` JSON `categories_assigned` field SHALL be a dict mapping category name to count of transactions assigned that category in that batch (e.g., `{"Dining": 3, "Subscriptions & Software": 1}`), not a flat list.

#### Scenario: Batch response_summary records category counts
- **WHEN** an enrich-batch step writes its `response_summary` to `run_steps`
- **THEN** `response_summary.categories_assigned` is a JSON object with category names as keys and integer counts as values

#### Scenario: Batch with no categories assigned
- **WHEN** no transactions in a batch are assigned a known category
- **THEN** `response_summary.categories_assigned` is an empty object `{}`

---

### Requirement: sync step persists response summary

The `sync` pipeline step SHALL write a `response_summary` JSON to its `run_steps` row upon completion.

The `response_summary` SHALL include: `{"accounts_synced": N, "new_transactions": M}` where `accounts_synced` is the number of accounts synced and `new_transactions` is the count of net-new transactions inserted.

#### Scenario: Sync step records accounts and transactions
- **WHEN** the sync step completes
- **THEN** the `run_steps` row for `step_type = 'sync'` has a non-null `response_summary` with `accounts_synced` and `new_transactions` counts

#### Scenario: Sync step with zero new transactions
- **WHEN** sync completes but no new transactions were found
- **THEN** `response_summary` records `{"accounts_synced": N, "new_transactions": 0}`

---

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

### Requirement: Pipeline run history table displays token and cost summary

The pipeline dashboard run history table SHALL display a "Cost" column alongside the existing token total column for each past run.

- When `computed_cost_usd` is not None, it SHALL be formatted as `$X.XXXX` (4 decimal places) to show sub-cent precision for small runs.
- When `computed_cost_usd` is None, the cell SHALL display `—`.
- The cost column SHALL appear immediately after (or adjacent to) the token count column.

#### Scenario: Run with cost data shows formatted cost

- **WHEN** the past runs table renders a row where `computed_cost_usd` is set
- **THEN** the cost cell displays a value like `$0.0042`

#### Scenario: Run without token data shows dash

- **WHEN** the past runs table renders a row where `computed_cost_usd` is None
- **THEN** the cost cell displays `—`
