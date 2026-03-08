## MODIFIED Requirements

### Requirement: Automatic categorization after sync and import
The system SHALL NOT automatically categorize transactions after `finance sync` or `finance import`. Sync and import are purely data ingestion operations. Users SHALL run `finance pipeline` to categorize and enrich transactions.

#### Scenario: Sync does not trigger categorization
- **WHEN** `finance sync` runs and inserts new transactions
- **THEN** newly inserted transactions have `category = NULL` and `categorized_at = NULL`
- **AND** no LLM API calls are made during sync

#### Scenario: CSV import does not trigger categorization
- **WHEN** `finance import` runs and inserts new transactions
- **THEN** newly inserted transactions have `category = NULL` and `categorized_at = NULL`
- **AND** no LLM API calls are made during import

#### Scenario: Sync output reminds user to run pipeline
- **WHEN** `finance sync` completes and new transactions were inserted
- **THEN** stdout includes a message reminding the user to run `finance pipeline` to categorize

---

### Requirement: Cluster-first single-pass pipeline

The transaction enrichment pipeline SHALL use a cluster-first single-pass approach implemented in `finance/ai/pipeline.py`. The pipeline SHALL support two modes: **incremental** (default) and **full**.

In **incremental mode**, the pipeline SHALL:
1. Build merchant clusters from ALL transactions (for full historical context).
2. Filter clusters to only those containing at least one transaction where `categorized_at IS NULL`.
3. Send only filtered clusters to the LLM in batches of 40.
4. Write results back for ALL transactions in each processed cluster.

In **full mode** (`full=True`), step 2 is skipped — all clusters are sent.

The public entry point SHALL be:

```python
def run_pipeline(conn, emit=None, run_sync: bool = True, full: bool = False) -> int:
```

#### Scenario: Incremental mode skips fully-categorized clusters
- **WHEN** `run_pipeline(conn)` is called and the database has 200 clusters
- **AND** 195 clusters have all transactions with non-null `categorized_at`
- **AND** 5 clusters have at least one transaction with `categorized_at IS NULL`
- **THEN** only 5 clusters are sent to the LLM (1 batch of 5)
- **AND** the run_log summary includes `clusters_skipped: 195`

#### Scenario: Incremental mode preserves clustering context
- **WHEN** a cluster for "Netflix" has 12 historical transactions and 1 new uncategorized transaction
- **THEN** the cluster sent to the LLM includes all 13 transaction amounts and up to 5 raw_samples
- **AND** the LLM sees the full history for accurate recurring/category inference

#### Scenario: Incremental mode writes back to entire cluster
- **WHEN** a cluster with 12 categorized + 1 uncategorized transaction is processed
- **THEN** all 13 transactions receive updated `category`, `categorized_at`, `merchant_normalized`, `is_recurring`, `needs_review`, `review_reason`

#### Scenario: Full mode processes all clusters
- **WHEN** `run_pipeline(conn, full=True)` is called
- **THEN** all clusters are sent to the LLM regardless of `categorized_at` status
- **AND** the run_log summary includes `clusters_skipped: 0`

#### Scenario: No uncategorized transactions in incremental mode
- **WHEN** `run_pipeline(conn)` is called and every transaction has non-null `categorized_at`
- **THEN** the pipeline completes immediately after cluster-build with 0 batches processed
- **AND** the run_log status is `success` with `transactions_enriched: 0`

---

### Requirement: Manual categorize command
The system SHALL provide a `finance categorize` CLI command. The command SHALL NOT trigger enrichment (`enrich_transactions`) after categorization.

#### Scenario: Incremental run (default)
- **WHEN** `finance categorize` is run without flags
- **THEN** only transactions with `categorized_at IS NULL` are processed
- **AND** `enrich_transactions` is NOT called

#### Scenario: Force re-categorize all
- **WHEN** `finance categorize --all` is run
- **THEN** all transactions are re-categorized regardless of `categorized_at`

#### Scenario: Summary printed
- **WHEN** `finance categorize` completes
- **THEN** stdout shows number of transactions categorized

---

## REMOVED Requirements

### Requirement: Enrichment triggered after sync and categorize
**Reason**: Sync and categorize are being decoupled from enrichment. All enrichment is handled by `run_pipeline()` via the `finance pipeline` command. Running LLM calls inside sync/import was causing hidden token consumption with no cost tracking.
**Migration**: Run `finance pipeline` after `finance sync` or `finance import` to categorize and enrich new transactions.
