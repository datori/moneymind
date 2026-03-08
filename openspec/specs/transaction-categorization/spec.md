## ADDED Requirements

### Requirement: Transaction category taxonomy
The system SHALL use a fixed flat category taxonomy stored in `finance/ai/categories.py`.

Categories:
- Food & Dining
- Groceries
- Transportation
- Shopping
- Entertainment
- Travel
- Health & Fitness
- Home & Utilities
- Subscriptions & Software
- Personal Care
- Education
- Financial
- Income
- Investment
- Other

#### Scenario: Valid category assigned
- **WHEN** a transaction is categorized
- **THEN** the stored `category` value is one of the above 15 categories

---

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

### Requirement: Batch API calls
The system SHALL send transactions to Claude in batches of at most 25. The API call SHALL use `tool_use` with a defined tool schema to guarantee valid structured JSON output. The tool SHALL be named `categorize_transactions` and SHALL return an object containing a `transactions` array of `{id, category}` objects.

The model SHALL be called with `tool_choice={"type": "tool", "name": "categorize_transactions"}` to force structured output.

#### Scenario: Batching applied with tool_use
- **WHEN** 60 uncategorized transactions exist
- **THEN** at least 3 API calls are made (25 + 25 + 10)
- **AND** each call uses `tool_use` with the `categorize_transactions` tool
- **AND** the response is extracted from the `tool_use` content block's `input` field (no `json.loads` needed)

#### Scenario: Response is guaranteed valid JSON
- **WHEN** the model responds to a categorization batch
- **THEN** the response is a `tool_use` content block with `input` matching the schema
- **AND** no markdown fence stripping is required

---

### Requirement: categorized_at timestamp updated
The system SHALL set `categorized_at` to the current time (unix ms) when a transaction is successfully categorized.

#### Scenario: Timestamp set on success
- **WHEN** a transaction is categorized successfully
- **THEN** `categorized_at` is a unix ms timestamp and `category` is one of the valid categories

#### Scenario: Timestamp remains null on failure
- **WHEN** a batch API call fails
- **THEN** `categorized_at` and `category` remain NULL for transactions in that batch

---

### Requirement: Missing API key error
The system SHALL print a clear error if `ANTHROPIC_API_KEY` is not configured when `finance categorize` is run.

#### Scenario: Missing API key
- **WHEN** `finance categorize` is run without `ANTHROPIC_API_KEY` set
- **THEN** an error message is printed explaining the missing key and the command exits non-zero

---

## MODIFIED Requirements

### Requirement: Cluster-first single-pass pipeline

The transaction enrichment pipeline SHALL use a cluster-first single-pass approach implemented in `finance/ai/pipeline.py`. The two-pass system (`categorize.py` Pass 1 + `enrich.py` Pass 2) is replaced. A single LLM call per batch SHALL return `category`, `canonical_name`, `is_recurring`, and per-transaction `needs_review`/`review_reason` for all transactions in a merchant cluster.

The pipeline steps in order are:

1. **Sync** (optional, configurable): call `sync_all(conn)` to fetch latest transactions.
2. **Cluster build**: group all transactions by normalized merchant key using the existing `_normalize_merchant_key` logic (moved from `enrich.py` to `pipeline.py`). Each cluster contains: `merchant_key`, `raw_samples` (up to 5 distinct descriptions), `transaction_ids`, `amounts`.
3. **Incremental filter** (skipped when `full=True`): remove clusters where every transaction already has `categorized_at IS NOT NULL`.
4. **Enrich batches**: send up to 40 clusters per batch to Claude Haiku. The prompt returns per-cluster: `category`, `canonical_name`, `is_recurring`, and a `transactions` array with per-transaction `needs_review` / `review_reason`.
5. **Write results**: bulk-apply all results to the `transactions` table in a single commit per batch. Results are written for ALL transactions in each processed cluster (not just uncategorized ones).
6. **Recurring overrides**: call `apply_recurring_overrides(conn)` from `finance/analysis/review.py` to promote any `(merchant_normalized, amount)` pair seen in 3+ distinct months to `is_recurring=1`, correcting LLM false-negatives.

The public entry point SHALL be:

```python
def run_pipeline(conn: sqlite3.Connection, emit=None, run_sync: bool = True, full: bool = False) -> int:
    ...
```

returning the total number of transaction rows updated.

In **incremental mode** (`full=False`, default), the pipeline SHALL:
1. Build merchant clusters from ALL transactions (for full historical context).
2. Filter clusters to only those containing at least one transaction where `categorized_at IS NULL`.
3. Send only filtered clusters to the LLM in batches of 40.
4. Write results back for ALL transactions in each processed cluster.

In **full mode** (`full=True`), step 2 is skipped — all clusters are sent.

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

### Requirement: LLM prompt for cluster-first enrichment

The prompt sent to Claude Haiku per batch SHALL instruct the model to classify merchant clusters. The model SHALL be called with `tool_use` using a tool named `classify_merchants` whose schema defines the response structure. The tool SHALL return an object containing a `merchants` array.

Each merchant object SHALL have fields:
- `merchant_key`: string (unchanged from input)
- `category`: string (one of the 15 canonical categories)
- `canonical_name`: string (clean human-readable name)
- `is_recurring`: integer (0 or 1)
- `review_ids`: array of strings (transaction IDs needing review, empty if none)
- `review_reason`: string or null

The model SHALL be called with `tool_choice={"type": "tool", "name": "classify_merchants"}` to force structured output. The prompt SHALL include the full 15-category list. The model SHALL be `claude-haiku-4-5-20251001` with `max_tokens = 8096`. Batch size SHALL be 40 clusters.

#### Scenario: Single-pass assigns category via tool_use
- **WHEN** a batch of merchant clusters is sent to the LLM
- **THEN** the response is a `tool_use` content block with valid structured JSON
- **AND** each merchant in the response includes `category`, `canonical_name`, `is_recurring`, and `review_ids`

#### Scenario: Unrecognized category falls back to "Other"
- **WHEN** the model returns a `category` value not in the 15-category list
- **THEN** the pipeline falls back to `"Other"` and logs a warning

#### Scenario: Cluster enrichment applied to all transactions in cluster
- **WHEN** a cluster with 12 transactions is processed
- **THEN** all 12 transactions receive the same `merchant_normalized`, `is_recurring`, and `category`
- **THEN** each transaction receives its own `needs_review` value based on whether its ID appears in `review_ids`

#### Scenario: Batch failure is non-fatal
- **WHEN** the LLM call for a batch raises `anthropic.APIError`
- **THEN** the batch is logged as a warning and skipped; the pipeline continues with the next batch

---

### Requirement: Write-back to transactions table

For each cluster result, the pipeline SHALL update the following columns for every `transaction_id` in the cluster:

- `category` — from cluster-level `category`
- `categorized_at` — set to current unix ms (same semantics as existing `categorize_batch`)
- `merchant_normalized` — from cluster-level `canonical_name`
- `is_recurring` — from cluster-level `is_recurring`
- `needs_review` — from per-transaction `needs_review`
- `review_reason` — from per-transaction `review_reason`

All updates SHALL be committed per batch (not per cluster) for performance.

#### Scenario: Transactions table fully updated after pipeline run
- **WHEN** `run_pipeline(conn)` completes successfully
- **THEN** every transaction that was in a processed cluster has non-null `category`, `categorized_at`, `merchant_normalized`, and `is_recurring`

---

### Requirement: Deprecation of two-pass functions

`categorize_uncategorized(conn)`, `categorize_all(conn)` in `finance/ai/categorize.py` and `enrich_transactions(conn)` in `finance/ai/enrich.py` SHALL remain in place but SHALL emit a `DeprecationWarning` (via `warnings.warn`) when called. They SHALL NOT be deleted in this change.

#### Scenario: Old categorize function called
- **WHEN** `categorize_uncategorized(conn)` is called
- **THEN** a `DeprecationWarning` is emitted with message directing callers to use `run_pipeline` instead; the function executes normally

#### Scenario: Old enrich function called
- **WHEN** `enrich_transactions(conn)` is called
- **THEN** a `DeprecationWarning` is emitted; the function executes normally
