## 1. Define tool schemas

- [x] 1.1 Define `classify_merchants` tool schema dict in `finance/ai/pipeline.py` matching the design spec (merchants array with merchant_key, category, canonical_name, is_recurring, review_ids, review_reason)
- [x] 1.2 Define `categorize_transactions` tool schema dict in `finance/ai/categorize.py` matching the design spec (transactions array with id, category)
- [x] 1.3 Define `enrich_merchants` tool schema dict in `finance/ai/enrich.py` matching the design spec (merchants array with merchant_key, canonical_name, is_recurring, transactions)

## 2. Update _pipeline_batch() to use tool_use

- [x] 2.1 Modify `_pipeline_batch()` in `finance/ai/pipeline.py`: add `tools=[CLASSIFY_MERCHANTS_TOOL]` and `tool_choice={"type": "tool", "name": "classify_merchants"}` to the `client.messages.create()` call
- [x] 2.2 Replace response parsing: extract results from `tool_use` content block's `input["merchants"]` instead of `json.loads(message.content[0].text)`
- [x] 2.3 Remove `_strip_fences()` call from `_pipeline_batch()` response path
- [x] 2.4 Keep existing category validation (fallback to "Other") — tool_use guarantees structure but not valid category values

## 3. Update categorize_batch() to use tool_use

- [x] 3.1 Modify `categorize_batch()` in `finance/ai/categorize.py`: add `tools=[CATEGORIZE_TRANSACTIONS_TOOL]` and `tool_choice={"type": "tool", "name": "categorize_transactions"}` to the `client.messages.create()` call
- [x] 3.2 Replace response parsing: extract results from `tool_use` content block's `input["transactions"]` instead of `json.loads()` with fence stripping
- [x] 3.3 Remove inline fence-stripping code from `categorize_batch()`
- [x] 3.4 Keep existing category validation logic

## 4. Update _enrich_batch() to use tool_use

- [x] 4.1 Modify `_enrich_batch()` in `finance/ai/enrich.py`: add `tools=[ENRICH_MERCHANTS_TOOL]` and `tool_choice={"type": "tool", "name": "enrich_merchants"}` to the `client.messages.create()` call
- [x] 4.2 Replace response parsing: extract results from `tool_use` content block's `input["merchants"]` instead of `json.loads()` with fence stripping
- [x] 4.3 Remove `_strip_fences()` call from `_enrich_batch()` response path

## 5. Clean up

- [x] 5.1 Verify `_strip_fences()` is no longer called in any active code path (it may still be imported by `enrich.py` — leave the function but remove unused calls)
- [x] 5.2 Verify `finance pipeline` runs successfully with tool_use responses
- [x] 5.3 Verify `finance categorize` runs successfully with tool_use responses (deprecated but functional)
