## Why

All LLM calls in the pipeline use free-text prompts that ask for "ONLY a JSON array" and then manually strip markdown code fences and parse the result. This is fragile — the model can return malformed JSON, wrap it in fences despite instructions, or include explanatory text. The Anthropic SDK supports `tool_use` which guarantees valid JSON conforming to a defined schema, eliminating parsing failures entirely.

## What Changes

- **Switch `_pipeline_batch()` to use tool_use**: Define a tool schema for the enrichment response and call the model with `tool_use` instead of free-text. The response is guaranteed valid JSON matching the schema.
- **Remove fence-stripping code**: `_strip_fences()` becomes unnecessary for pipeline calls.
- **Switch deprecated `categorize_batch()` to use tool_use**: Same treatment for the deprecated categorizer (it still works and may be called).
- **Switch deprecated `_enrich_batch()` to use tool_use**: Same treatment for the deprecated enricher.

## Capabilities

### New Capabilities

_(none — this is an implementation improvement to existing capabilities)_

### Modified Capabilities

- `transaction-categorization`: LLM calls use tool_use for structured JSON output instead of free-text parsing. No change to the categories, prompt semantics, or output schema — only the delivery mechanism changes.
- `merchant-enrichment`: LLM calls use tool_use for structured JSON output instead of free-text parsing.

## Impact

- **`finance/ai/pipeline.py`**: Rewrite `_pipeline_batch()` to use `tools` parameter in `client.messages.create()`. Remove or reduce `_strip_fences()` usage.
- **`finance/ai/categorize.py`**: Rewrite `categorize_batch()` to use `tools` parameter.
- **`finance/ai/enrich.py`**: Rewrite `_enrich_batch()` to use `tools` parameter.
- **No schema changes**: The JSON structure returned is identical — only the transport changes from free-text to tool_use.
- **No dependency changes**: `anthropic` SDK already supports tool_use.
