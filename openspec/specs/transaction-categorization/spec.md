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
The system SHALL automatically categorize uncategorized transactions after `finance sync` and `finance import` complete.

#### Scenario: New transactions categorized post-sync
- **WHEN** `finance sync` runs and inserts new transactions
- **THEN** `categorize_uncategorized(conn)` is called before the sync command exits
- **AND** newly inserted transactions have their `category` and `categorized_at` populated

#### Scenario: Categorization failure does not fail sync
- **WHEN** the Claude API returns an error during categorization
- **THEN** sync still reports success
- **AND** affected transactions remain with `category=NULL` and `categorized_at=NULL`

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
The system SHALL send transactions to Claude in batches of at most 50.

#### Scenario: Batching applied
- **WHEN** 120 uncategorized transactions exist
- **THEN** at least 3 API calls are made (50 + 50 + 20)

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
