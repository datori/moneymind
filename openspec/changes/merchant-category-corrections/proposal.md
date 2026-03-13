## Why

Pipeline re-runs unconditionally overwrite `category` on every transaction, silently discarding any manual corrections made via `fix-category` or the web review UI. There is no mechanism to persist user intent about merchant categorization across pipeline runs.

## What Changes

- **New `category_corrections` table** — stores per-merchant overrides: `merchant_key`, `category`, `canonical_name`, `is_recurring`, timestamps.
- **Pipeline cluster split** — before sending to LLM, known merchants (those with a correction entry) are separated out and written directly, bypassing LLM entirely.
- **Correction application** — bypass writes category, canonical_name (only if NULL on target transaction), and is_recurring from the corrections table; marks `needs_review = 0`.
- **LLM prompt enrichment** — known corrections are prepended to each LLM batch as few-shot reference, helping the model generalize to similar merchant names.
- **Existing correction UIs become persistent** — `fix-category` CLI and web review category change both upsert into `category_corrections`, snapshotting `canonical_name` and `is_recurring` from the transaction at that moment.

## Capabilities

### New Capabilities
- `merchant-category-corrections`: Per-merchant category override table, pipeline bypass logic, and correction persistence from existing fix flows.

### Modified Capabilities
- `transaction-categorization`: Pipeline now splits clusters into known/unknown before LLM dispatch; LLM prompt receives correction hints; manual category changes have permanent effect across re-runs.

## Impact

- `finance/db.py` — new table + migration for `category_corrections`
- `finance/ai/pipeline.py` — cluster split, bypass write path, prompt enrichment
- `finance/cli.py` — `fix-category` command upserts corrections table
- `finance/web/app.py` — review approval endpoint upserts corrections table
