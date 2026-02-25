## Why

The current two-pass AI pipeline (Pass 1: categorize each transaction individually; Pass 2: enrich merchant clusters) wastes LLM tokens by sending every transaction through a separate categorization call before the cluster-level enrichment pass already produces richer signals per merchant group. There is also no visibility into pipeline execution — runs happen silently in the CLI with no progress feedback, no history, and no way to trigger or observe them from the web UI.

## What Changes

- The two-pass pipeline (categorize.py + enrich.py) is replaced by a single cluster-first pass: build merchant clusters, then send 40 clusters per batch to Claude Haiku with a prompt that returns `category`, `canonical_name`, `is_recurring`, and per-transaction `needs_review`/`review_reason` in one response.
- A `run_log` table and a `run_steps` table are added to the database to record every pipeline execution with per-batch token counts, durations, and request/response summaries.
- A `GET /pipeline/run/stream` SSE endpoint is added so the web UI can stream live progress events as each pipeline step completes.
- A dedicated `/pipeline` page is added to the web UI with a full run history table and a "Run Pipeline" button that opens a live streaming view.
- The dashboard index gains a "Recent Runs" widget showing the last 5 pipeline runs.
- `enrich_transactions(conn, emit=None)` is refactored into `finance/ai/pipeline.py` and accepts an optional `emit` callback for progress events; the old `categorize.py` functions are deprecated but not removed immediately.

## Capabilities

### New Capabilities

- `run-log`: Persistent `run_log` and `run_steps` tables that record every pipeline run's status, timing, and per-batch LLM token usage and summaries.
- `pipeline-streaming`: SSE streaming endpoint (`GET /pipeline/run/stream`) and a live web UI panel that shows real-time step-by-step pipeline progress as each batch is sent and received.

### Modified Capabilities

- `transaction-categorization`: Replaced by cluster-first single-pass pipeline in `finance/ai/pipeline.py`. Categories are assigned at the cluster level alongside merchant enrichment in one LLM call; old `categorize_uncategorized` / `categorize_all` are deprecated.
- `web-dashboard`: Dashboard index gains a "Recent Runs" widget. New `/pipeline` route added with run history and trigger button.

## Impact

- **New file**: `finance/ai/pipeline.py` — cluster-first pipeline replacing two-pass logic; exports `run_pipeline(conn, emit=None)`.
- **Modified**: `finance/db.py` — adds `run_log` and `run_steps` table definitions to `_SCHEMA` and `init_db()`.
- **Modified**: `finance/web/app.py` — adds `GET /pipeline` (history page), `POST /pipeline/run` (trigger), `GET /pipeline/run/stream` (SSE endpoint).
- **New templates**: `finance/web/templates/pipeline.html` — pipeline page with run history table and trigger button; inline streaming panel.
- **Modified**: `finance/web/templates/index.html` — adds "Recent Runs" widget section.
- **Modified**: `finance/ai/enrich.py` — `enrich_transactions` deprecated in favor of `pipeline.run_pipeline`; existing function kept for backwards compatibility.
- **Modified**: `finance/ai/categorize.py` — `categorize_uncategorized` / `categorize_all` deprecated; existing functions kept.
- **Dependencies**: No new packages beyond existing `anthropic` and `fastapi`; SSE uses `fastapi.responses.StreamingResponse` (already available).
