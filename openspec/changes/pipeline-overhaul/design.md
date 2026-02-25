## Context

The finance app currently runs a two-pass AI pipeline:

- **Pass 1** (`finance/ai/categorize.py`): Sends uncategorized transactions individually in batches of 25 to Claude Haiku. Returns `{id, category}` pairs. Updates `category` and `categorized_at` on each transaction.
- **Pass 2** (`finance/ai/enrich.py`): Builds merchant clusters from all transactions using `_normalize_merchant_key()`, then sends up to 40 clusters per batch to Claude Haiku. Returns `canonical_name`, `is_recurring`, and per-transaction `needs_review`/`review_reason`. Does **not** update `category`.

Both passes are triggered manually from the CLI (`finance categorize`, then `finance enrich` implicitly). There is no web UI trigger, no run history, and no visibility into what the model is processing or returning.

Current file state:
- `finance/ai/categorize.py` — `categorize_batch()`, `categorize_uncategorized()`, `categorize_all()`
- `finance/ai/enrich.py` — `_normalize_merchant_key()`, `_build_clusters()`, `_strip_fences()`, `_enrich_batch()`, `_write_results()`, `enrich_transactions()`
- `finance/db.py` — `_SCHEMA` contains 6 tables; no run tracking tables
- `finance/web/app.py` — has `POST /sync`; no pipeline trigger route

## Goals / Non-Goals

**Goals:**
- Replace two-pass pipeline with a single cluster-first pass in `finance/ai/pipeline.py` that returns `category` alongside enrichment data.
- Add `run_log` and `run_steps` tables to track pipeline history with per-batch LLM metadata.
- Add `GET /pipeline/run/stream` SSE endpoint that runs the pipeline and streams progress events to the browser.
- Add `GET /pipeline` page with run history table and a "Run Pipeline" button that connects to the SSE stream.
- Add a "Recent Runs" widget to `index.html`.
- Add `emit` callback to `run_pipeline()` so progress events work in both CLI and HTTP contexts.

**Non-Goals:**
- Removing `categorize.py` or `enrich.py` — they are deprecated but kept for this change.
- WebSocket bidirectional communication — SSE is sufficient for server→client progress.
- Parallel batch execution — sequential batching is simple and fits Claude API rate limits.
- Streaming individual token output — event granularity is per batch, not per token.
- Authentication for the pipeline trigger endpoint — the app is single-user, local.
- Re-enriching only new/uncategorized transactions — the cluster-first pass operates on all transactions to ensure consistency across the cluster.

## Decisions

### Decision 1: Single cluster-first pass vs. keeping separate categorize + enrich

**Options considered:**
- A: Keep two passes, add visibility to both (simplest but redundant).
- B: Merge into one prompt that handles category + enrichment at the cluster level.

**Chosen: B.** Cluster-level categorization is strictly more accurate than per-transaction categorization — 40 NETFLIX transactions arriving with similar amounts and descriptions is unambiguous evidence of "Subscriptions & Software" and "is_recurring: 1" in a way that a single isolated transaction is not. The merged prompt is a net reduction in API calls and token usage for equivalent (or better) accuracy.

**Implementation:** New file `finance/ai/pipeline.py`. The `_normalize_merchant_key()` helper is moved from `enrich.py` to `pipeline.py`; `enrich.py` imports it from there to preserve backward compat. The merged prompt includes `CATEGORIES` (from `finance/ai/categories.py`) and instructs the model to return one of those values as `category` per cluster.

### Decision 2: write-back adds `category` and `categorized_at`

The current `_write_results()` in `enrich.py` does not update `category` or `categorized_at` (those were handled by Pass 1). The new `_write_results()` equivalent in `pipeline.py` **must** update both:

```python
UPDATE transactions SET
    category           = ?,
    categorized_at     = ?,
    merchant_normalized = ?,
    is_recurring       = ?,
    needs_review       = ?,
    review_reason      = ?
WHERE id = ?
```

This is the key correctness requirement for the unified pass. Category validation (fall back to `"Other"` for unrecognized values) mirrors existing `categorize_batch()` behavior.

### Decision 3: SSE via StreamingResponse (not WebSockets)

**Options considered:**
- A: Polling — client polls `/pipeline/status/{run_id}` every second.
- B: Server-Sent Events (SSE) — single long-lived HTTP GET, server pushes events.
- C: WebSockets — bidirectional, more complex setup.

**Chosen: B.** SSE is simpler than WebSockets for a one-way progress stream. FastAPI's `StreamingResponse` supports it natively without additional packages. The browser's `EventSource` API handles reconnection. Polling would require a separate status store and extra round-trips.

**Implementation:** `GET /pipeline/run/stream` returns `StreamingResponse(generator, media_type="text/event-stream")`. The generator is a synchronous Python generator (not `async`) that calls `run_pipeline(conn, emit=...)`. Each `emit()` call yields one SSE line. The generator holds the DB connection for the duration of the pipeline run.

**Known limitation:** FastAPI's `Depends(get_db)` doesn't compose cleanly with `StreamingResponse` generators because the dependency's `finally` block runs after the generator is exhausted, not during. The `/pipeline/run/stream` route opens its own connection directly (same pattern as `get_db` but inline) to avoid this.

### Decision 4: emit callback pattern

`run_pipeline(conn, emit=None)` accepts an optional callable:

```python
def emit(event: dict) -> None: ...
```

The SSE endpoint passes a generator-yield wrapper as the emit. The CLI `finance pipeline` command (or future CLI trigger) can pass `lambda e: print(json.dumps(e))` for terminal output. When `emit=None`, the pipeline runs silently — backward compatible with any code that calls it without a callback.

### Decision 5: run_log and run_steps schema

Two separate tables rather than a single JSON blob. `run_log` records the overall run (type, status, timing). `run_steps` records per-batch detail. This allows querying "how many tokens did the last 5 runs consume?" without parsing JSON blobs.

**run_log.run_type** values: `'full'` (sync + enrich) and `'enrich-only'` (skip sync). The SSE endpoint always runs `'full'` by default; a future flag could allow `'enrich-only'`.

**run_steps.step_type** values: `'sync'`, `'cluster-build'`, `'enrich-batch'`, `'write-results'`. The `batch_index` / `batch_total` columns are only meaningful for `'enrich-batch'` steps.

**Migration:** `run_log` and `run_steps` are new tables added directly to `_SCHEMA` in `db.py` using `CREATE TABLE IF NOT EXISTS`. No ALTER TABLE migration needed (these tables don't exist yet).

### Decision 6: Deprecation of old functions

`categorize_uncategorized()`, `categorize_all()` (in `categorize.py`) and `enrich_transactions()` (in `enrich.py`) emit `DeprecationWarning` via `warnings.warn()` but continue to function. This provides a grace period: any script calling them still works, but the warning signals the transition. Deletion is deferred to a future change.

### Decision 7: Pipeline page and dashboard widget

The `/pipeline` page (`pipeline.html`) shows:
1. A "Run Pipeline" button that triggers SSE connection.
2. A live streaming panel (hidden until button clicked) showing step-by-step progress.
3. A run history table (most recent 20 runs from `run_log`).

The dashboard `/` index page gains a "Recent Runs" widget in the existing card grid showing the last 5 runs (status, type, when, duration).

After the SSE stream emits `run_done`, the browser refreshes the run history table via a full page reload (simplest approach — no AJAX table refresh needed for a personal tool).

## Risks / Trade-offs

- **Long-running SSE connection:** The pipeline may take 30–120 seconds for a large transaction set. Browser SSE connections time out by default at 30s in some environments. Mitigation: emit a `keep-alive` event (or `step_start` for sync) within the first 5 seconds to prevent timeout.
- **Single connection limit:** If two browser tabs both click "Run Pipeline" simultaneously, two pipeline runs will execute concurrently on the same DB. For a single-user personal tool this is acceptable; the `run_log` will show both runs.
- **Cluster-first re-categorizes everything:** Running the pipeline re-assigns categories to all transactions, including ones a user may have manually corrected via `/review`. A user-corrected transaction has `needs_review = 0` but no "manually_categorized" marker. This means a pipeline run may overwrite manual corrections. Mitigation: this is a known trade-off deferred to a future "pinned category" feature. Document in the CLI/web UI.
- **Prompt size:** 40 clusters with 5 raw samples and all transaction IDs can produce large payloads. At `max_tokens = 4096` for the response, very large clusters (100+ transactions per merchant) truncate the transaction list in the response. Mitigation: the prompt already uses a compact representation; truncation would mean some transactions don't get per-transaction review flags but still receive the cluster-level category and merchant_normalized.

## Migration Plan

1. Add `run_log` and `run_steps` to `db.py` `_SCHEMA`. On next app start, `init_db()` creates the tables.
2. Create `finance/ai/pipeline.py` with `run_pipeline()`.
3. Add deprecation warnings to `categorize.py` and `enrich.py`.
4. Add web routes and template.
5. No data migrations required; existing transactions retain their current `category` and `categorized_at` values until the next pipeline run.

Rollback: revert file changes; `run_log` and `run_steps` tables remain empty but harmless.
