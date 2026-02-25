## ADDED Requirements

### Requirement: run_log aggregate summary column

The `run_log` table SHALL have a `summary` TEXT column (JSON) that is populated on run completion with aggregate analytics across all steps in that run.

The summary JSON SHALL include at minimum:
```json
{
  "transactions_synced": N,
  "clusters_built": M,
  "batches_processed": K,
  "transactions_enriched": P,
  "categories": {"Subscriptions & Software": 3, "Dining": 2, ...},
  "recurring_count": R,
  "review_count": V,
  "tokens_in": T1,
  "tokens_out": T2
}
```

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

The `cluster-build` pipeline step SHALL write a `response_summary` JSON to its `run_steps` row with: `{"transaction_count": N, "cluster_count": M}`.

#### Scenario: Cluster-build step records counts
- **WHEN** `_build_clusters()` completes
- **THEN** the `run_steps` row for `step_type = 'cluster-build'` has `response_summary` with `transaction_count` (uncategorized transactions) and `cluster_count` (distinct merchant clusters)
