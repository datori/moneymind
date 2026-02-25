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
The system SHALL automatically categorize uncategorized transactions after `finance sync` and `finance import` complete. After categorization completes, the system SHALL also call `enrich_transactions(conn)` if `ANTHROPIC_API_KEY` is set.

#### Scenario: New transactions categorized post-sync
- **WHEN** `finance sync` runs and inserts new transactions
- **THEN** `categorize_uncategorized(conn)` is called before the sync command exits
- **AND** newly inserted transactions have their `category` and `categorized_at` populated

#### Scenario: Enrichment runs after post-sync categorization
- **WHEN** `finance sync` completes and `ANTHROPIC_API_KEY` is set
- **THEN** `enrich_transactions(conn)` is called after `categorize_uncategorized(conn)` completes

#### Scenario: Categorization failure does not fail sync
- **WHEN** the Claude API returns an error during categorization
- **THEN** sync still reports success
- **AND** affected transactions remain with `category=NULL` and `categorized_at=NULL`

#### Scenario: Enrichment failure does not fail sync
- **WHEN** `enrich_transactions(conn)` raises an exception
- **THEN** sync still reports success
- **AND** the enrichment error is logged as a warning but not shown to the user as a fatal error

#### Scenario: Enrichment skipped without API key
- **WHEN** `ANTHROPIC_API_KEY` is not set
- **THEN** `enrich_transactions` is not called during sync or categorize

---

### Requirement: Manual categorize command
The system SHALL provide a `finance categorize` CLI command.

#### Scenario: Incremental run (default)
- **WHEN** `finance categorize` is run without flags
- **THEN** only transactions with `categorized_at IS NULL` are processed

#### Scenario: Force re-categorize all
- **WHEN** `finance categorize --all` is run
- **THEN** all transactions are re-categorized regardless of `categorized_at`

#### Scenario: Summary printed
- **WHEN** `finance categorize` completes
- **THEN** stdout shows number of transactions categorized and number of API calls made

---

### Requirement: Batch API calls
The system SHALL send transactions to Claude in batches of at most 25.

#### Scenario: Batching applied
- **WHEN** 60 uncategorized transactions exist
- **THEN** at least 3 API calls are made (25 + 25 + 10)

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
3. **Enrich batches**: send up to 40 clusters per batch to Claude Haiku. The prompt returns per-cluster: `category`, `canonical_name`, `is_recurring`, and a `transactions` array with per-transaction `needs_review` / `review_reason`.
4. **Write results**: bulk-apply all results to the `transactions` table in a single commit per batch.

The public entry point SHALL be:

```python
def run_pipeline(conn: sqlite3.Connection, emit=None, run_sync: bool = True) -> int:
    ...
```

returning the total number of transaction rows updated.

---

### Requirement: LLM prompt for cluster-first enrichment

The prompt sent to Claude Haiku per batch SHALL instruct the model to return a JSON array of objects with the following fields per cluster:

```json
{
  "merchant_key": "<unchanged from input>",
  "category": "<one of the 15 canonical categories>",
  "canonical_name": "<clean human-readable name>",
  "is_recurring": 0 | 1,
  "transactions": [
    {
      "id": "<transaction id>",
      "needs_review": 0 | 1,
      "review_reason": "<short string or null>"
    }
  ]
}
```

The prompt SHALL include the full 15-category list from `finance/ai/categories.py` (same `CATEGORIES` constant). The model SHALL be `claude-haiku-4-5-20251001` with `max_tokens = 4096`. Batch size SHALL be 40 clusters.

#### Scenario: Single-pass assigns category
- **WHEN** a merchant cluster is sent in an enrich batch
- **THEN** the LLM response includes a `category` field for that cluster matching one of the 15 canonical categories
- **THEN** the `category` and `categorized_at` columns are updated for all transactions in that cluster

#### Scenario: Unrecognized category falls back to "Other"
- **WHEN** the model returns a `category` value not in the 15-category list
- **THEN** the pipeline falls back to `"Other"` and logs a warning (consistent with existing `categorize_batch` behavior)

#### Scenario: Cluster enrichment applied to all transactions in cluster
- **WHEN** a cluster with 12 transactions is processed
- **THEN** all 12 transactions receive the same `merchant_normalized`, `is_recurring`, and `category`
- **THEN** each transaction receives its own `needs_review` and `review_reason` values from the per-transaction entries

#### Scenario: Batch failure is non-fatal
- **WHEN** the LLM call for a batch of 40 clusters raises `anthropic.APIError` or `ValueError`
- **THEN** the batch is logged as a warning and skipped; the pipeline continues with the next batch; the run does not abort

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
