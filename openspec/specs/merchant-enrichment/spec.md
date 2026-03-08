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
The system SHALL call `claude-haiku-4-5-20251001` with batches of up to 40 merchant clusters. The API call SHALL use `tool_use` with a defined tool schema to guarantee valid structured JSON output. The tool SHALL be named `enrich_merchants` and SHALL return an object containing a `merchants` array.

Each merchant object SHALL have fields:
- `merchant_key`: string (unchanged from input)
- `canonical_name`: string (clean human-readable merchant name, stored as `merchant_normalized`)
- `is_recurring`: integer (0 or 1)
- `transactions`: array of `{id, needs_review, review_reason}` objects

The model SHALL be called with `tool_choice={"type": "tool", "name": "enrich_merchants"}` to force structured output.

#### Scenario: Normal enrichment run with tool_use
- **WHEN** `_enrich_batch(clusters)` is called with 40 merchant clusters
- **THEN** the API call uses `tool_use` with the `enrich_merchants` tool
- **AND** the response is extracted from the `tool_use` content block's `input` field
- **AND** `merchant_normalized` is written for every transaction
- **AND** `is_recurring` and `needs_review` / `review_reason` are written as returned by the model

#### Scenario: Response is guaranteed valid JSON
- **WHEN** the model responds to an enrichment batch
- **THEN** the response is a `tool_use` content block with `input` matching the schema
- **AND** no markdown fence stripping or `json.loads` parsing is required

#### Scenario: Partial API failure
- **WHEN** one batch API call raises an `anthropic.APIError`
- **THEN** the error is logged as a warning and the batch is skipped
- **AND** remaining batches continue processing

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
