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
