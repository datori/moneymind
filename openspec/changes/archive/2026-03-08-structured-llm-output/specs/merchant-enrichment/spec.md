## MODIFIED Requirements

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
