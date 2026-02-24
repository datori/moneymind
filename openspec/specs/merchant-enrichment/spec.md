## ADDED Requirements

### Requirement: Schema migration for enrichment columns
The system SHALL add four columns to the `transactions` table if they do not already exist, using `ALTER TABLE … ADD COLUMN` with `OperationalError` suppression to be safe on existing databases.

Columns added:
- `needs_review INTEGER DEFAULT 0`
- `review_reason TEXT`
- `is_recurring INTEGER DEFAULT 0`
- `merchant_normalized TEXT`

#### Scenario: Fresh database
- **WHEN** `init_db(conn)` is called on a new empty database
- **THEN** the `transactions` table contains all four new columns

#### Scenario: Existing database without enrichment columns
- **WHEN** `init_db(conn)` is called on a database that has `transactions` but lacks the four new columns
- **THEN** all four columns are added without error and existing row data is preserved

#### Scenario: Already-migrated database
- **WHEN** `init_db(conn)` is called and the four columns already exist
- **THEN** no error is raised and no data is changed

---

### Requirement: Merchant key normalization
The system SHALL normalize raw transaction description and merchant name strings to a canonical `merchant_key` using Python string transforms before any LLM call.

Normalization steps (applied in order):
1. Use `merchant_name` if non-empty, else `description`.
2. Lowercase the string.
3. Strip trailing `*<SUFFIX>` patterns (e.g. `netflix*1234` → `netflix`).
4. Strip `.com`, `.net`, `.org` suffixes.
5. Collapse whitespace; strip leading/trailing punctuation.

#### Scenario: Suffix stripping
- **WHEN** `merchant_name` is `"NETFLIX.COM *1234"`
- **THEN** the `merchant_key` is `"netflix"`

#### Scenario: Variant grouping
- **WHEN** transactions have descriptions `"Netflix"`, `"NETFLIX*"`, `"NETFLIX.COM *5678"`
- **THEN** all three produce the same `merchant_key` and are grouped into one cluster

#### Scenario: Fallback to description
- **WHEN** `merchant_name` is empty or NULL and `description` is `"WHOLEFDS #123 AUSTIN TX"`
- **THEN** the `merchant_key` is derived from `description`

---

### Requirement: Merchant cluster enrichment via LLM
The system SHALL call `claude-haiku-4-5-20251001` with batches of up to 40 merchant clusters. Each batch request provides the cluster's `merchant_key`, sample raw descriptions, and all transaction IDs and amounts. The model SHALL return for each cluster:
- `canonical_name`: clean human-readable merchant name (stored as `merchant_normalized`)
- `is_recurring`: `true` if the merchant represents a subscription/recurring charge
- `transactions`: array of `{id, needs_review, review_reason}` for any transactions that warrant review

#### Scenario: Normal enrichment run
- **WHEN** `enrich_transactions(conn)` is called with 60 distinct merchant clusters
- **THEN** at least 2 API calls are made (40 + 20 clusters per batch)
- **AND** `merchant_normalized` is written for every transaction
- **AND** `is_recurring` and `needs_review` / `review_reason` are written as returned by the model

#### Scenario: Partial API failure
- **WHEN** one batch API call raises an `anthropic.APIError`
- **THEN** the error is logged as a warning and the batch is skipped
- **AND** remaining batches continue processing
- **AND** `enrich_transactions` does not raise

#### Scenario: Idempotent re-run
- **WHEN** `enrich_transactions(conn)` is called a second time on the same dataset
- **THEN** all `merchant_normalized`, `is_recurring`, `needs_review`, and `review_reason` values are overwritten with fresh model output
- **AND** no duplicate records are created

---

### Requirement: Enrichment triggered after sync and categorize
The system SHALL call `enrich_transactions(conn)` at the end of `finance sync` and `finance categorize` when `ANTHROPIC_API_KEY` is set.

#### Scenario: Enrichment runs after sync
- **WHEN** `finance sync` completes successfully and `ANTHROPIC_API_KEY` is set
- **THEN** `enrich_transactions(conn)` is called before the command exits

#### Scenario: Enrichment runs after categorize
- **WHEN** `finance categorize` completes (with or without new categorizations) and `ANTHROPIC_API_KEY` is set
- **THEN** `enrich_transactions(conn)` is called before the command exits

#### Scenario: Enrichment skipped without API key
- **WHEN** `ANTHROPIC_API_KEY` is not set
- **THEN** `enrich_transactions` is not called and no error is shown

#### Scenario: Enrichment failure does not fail sync
- **WHEN** `enrich_transactions` raises an unhandled exception
- **THEN** sync still reports success
- **AND** the enrichment error is logged as a warning
