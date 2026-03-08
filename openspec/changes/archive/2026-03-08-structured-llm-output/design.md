## Context

Three LLM call sites all follow the same fragile pattern: prompt asks for "ONLY a JSON array", model sometimes wraps output in markdown fences, code strips fences and parses JSON, falls back on failure. The Anthropic SDK's `tool_use` feature guarantees structured JSON output conforming to a defined schema.

Current call sites:
- `finance/ai/pipeline.py` → `_pipeline_batch()` (primary, active)
- `finance/ai/categorize.py` → `categorize_batch()` (deprecated, still callable)
- `finance/ai/enrich.py` → `_enrich_batch()` (deprecated, still callable)

## Goals / Non-Goals

**Goals:**
- All three call sites use `tool_use` for guaranteed structured output
- Remove manual JSON parsing and fence-stripping from the response path
- Maintain identical output semantics

**Non-Goals:**
- Changing the model or prompt content
- Adding Pydantic or other schema validation libraries
- Modifying batch sizes or retry logic

## Decisions

### Decision 1: One tool definition per call site

Each of the three functions defines its own tool schema matching its expected output:

**`_pipeline_batch`** — tool name: `classify_merchants`
```python
{
    "name": "classify_merchants",
    "description": "Classify merchant clusters with category, canonical name, recurring flag, and review flags",
    "input_schema": {
        "type": "object",
        "properties": {
            "merchants": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "merchant_key": {"type": "string"},
                        "category": {"type": "string"},
                        "canonical_name": {"type": "string"},
                        "is_recurring": {"type": "integer", "enum": [0, 1]},
                        "review_ids": {"type": "array", "items": {"type": "string"}},
                        "review_reason": {"type": ["string", "null"]}
                    },
                    "required": ["merchant_key", "category", "canonical_name", "is_recurring", "review_ids"]
                }
            }
        },
        "required": ["merchants"]
    }
}
```

**`categorize_batch`** — tool name: `categorize_transactions`
```python
{
    "name": "categorize_transactions",
    "description": "Assign a category to each transaction",
    "input_schema": {
        "type": "object",
        "properties": {
            "transactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "category": {"type": "string"}
                    },
                    "required": ["id", "category"]
                }
            }
        },
        "required": ["transactions"]
    }
}
```

**`_enrich_batch`** — tool name: `enrich_merchants`
```python
{
    "name": "enrich_merchants",
    "description": "Enrich merchant clusters with canonical names, recurring flags, and review flags",
    "input_schema": {
        "type": "object",
        "properties": {
            "merchants": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "merchant_key": {"type": "string"},
                        "canonical_name": {"type": "string"},
                        "is_recurring": {"type": "integer", "enum": [0, 1]},
                        "transactions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "needs_review": {"type": "integer", "enum": [0, 1]},
                                    "review_reason": {"type": ["string", "null"]}
                                },
                                "required": ["id", "needs_review"]
                            }
                        }
                    },
                    "required": ["merchant_key", "canonical_name", "is_recurring", "transactions"]
                }
            }
        },
        "required": ["merchants"]
    }
}
```

**Rationale**: Each call site has different output shapes. Separate tools keep schemas minimal and specific.

### Decision 2: Wrap array in object for tool_use compatibility

Tool_use schemas require a top-level `"type": "object"`. The current free-text responses return bare JSON arrays. The tool schemas wrap the array in an object with a single key (e.g., `{"merchants": [...]}`). The calling code extracts the array from the wrapper.

### Decision 3: Force tool use via tool_choice

Use `tool_choice={"type": "tool", "name": "<tool_name>"}` to guarantee the model uses the tool rather than responding with text.

### Decision 4: Extract response without json.loads

The `tool_use` content block's `input` field is already a Python dict. No `json.loads()` call needed:
```python
tool_block = next(b for b in message.content if b.type == "tool_use")
results = tool_block.input["merchants"]  # already a list of dicts
```

## Risks / Trade-offs

**[Tool schema adds input tokens]** → Each schema definition adds ~100-200 tokens to the input. At $0.80/M input tokens, this is <$0.0002 per call. Negligible.

**[Category validation still needed]** → Tool_use guarantees valid JSON structure but doesn't enforce that `category` values match the canonical list. The existing fallback-to-"Other" logic remains necessary.
