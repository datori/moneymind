## MODIFIED Requirements

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

#### Scenario: Batch failure is non-fatal
- **WHEN** the LLM call for a batch raises `anthropic.APIError`
- **THEN** the batch is logged as a warning and skipped; the pipeline continues with the next batch
