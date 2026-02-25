## 1. Database: run_log and run_steps tables

- [ ] 1.1 In `finance/db.py`, append the following to `_SCHEMA` (before the closing `"""`):
  ```sql
  CREATE TABLE IF NOT EXISTS run_log (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      run_type    TEXT NOT NULL,
      started_at  INTEGER NOT NULL,
      finished_at INTEGER,
      status      TEXT NOT NULL DEFAULT 'running',
      error_msg   TEXT
  );

  CREATE TABLE IF NOT EXISTS run_steps (
      id               INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id           INTEGER NOT NULL REFERENCES run_log(id),
      step_type        TEXT NOT NULL,
      batch_index      INTEGER,
      batch_total      INTEGER,
      started_at       INTEGER NOT NULL,
      finished_at      INTEGER,
      request_summary  TEXT,
      response_summary TEXT,
      tokens_in        INTEGER,
      tokens_out       INTEGER,
      error_msg        TEXT
  );
  ```
- [ ] 1.2 Start the app (`finance-web`) and confirm `run_log` and `run_steps` tables exist via `sqlite3 data/finance.db ".tables"`

---

## 2. New file: finance/ai/pipeline.py

- [ ] 2.1 Create `finance/ai/pipeline.py`. Move `_normalize_merchant_key()` and `_build_clusters()` from `finance/ai/enrich.py` into this file verbatim. Update `enrich.py` to import them from `pipeline.py` to preserve backward compatibility:
  ```python
  from finance.ai.pipeline import _normalize_merchant_key, _build_clusters
  ```
- [ ] 2.2 Move `_strip_fences()` to `pipeline.py` as well. Update `enrich.py` to import it from `pipeline.py`.
- [ ] 2.3 Implement `_pipeline_batch(clusters: list[dict]) -> tuple[list[dict], int, int]` in `pipeline.py`. This function:
  - Builds the prompt including the full `CATEGORIES` list from `finance/ai/categories.py`
  - Instructs the model to return a JSON array where each object has: `merchant_key`, `category`, `canonical_name`, `is_recurring`, `transactions` (array of `{id, needs_review, review_reason}`)
  - Calls `claude-haiku-4-5-20251001` with `max_tokens=4096`
  - Returns `(results_list, tokens_in, tokens_out)`
  - Raises `ValueError` on JSON parse failure; raises `anthropic.APIError` on API failure (callers catch these)
- [ ] 2.4 Validate `category` field in results: if the returned value is not in `CATEGORIES`, replace with `"Other"` and log a warning (mirrors existing `categorize_batch()` behavior in `categorize.py`)
- [ ] 2.5 Implement `_apply_results(conn, results, run_id, batch_index, tokens_in, tokens_out, request_summary, response_summary)` in `pipeline.py`:
  - For each cluster result, `UPDATE transactions SET category=?, categorized_at=?, merchant_normalized=?, is_recurring=?, needs_review=?, review_reason=? WHERE id=?` for every transaction ID in the cluster
  - Commits once per batch
  - Inserts a `run_steps` row with `step_type='write-results'` and `response_summary={"transactions_updated": N}`
  - Returns total rows updated
- [ ] 2.6 Implement `run_pipeline(conn, emit=None, run_sync=True) -> int` as the public entry point:
  - Insert a `run_log` row with `status='running'`, capture `run_id`
  - If `run_sync=True`: call `sync_all(conn)` (import from `finance.ingestion.sync`); record a `run_steps` row for `step_type='sync'`; emit `step_start` + `step_done` events
  - Call `_build_clusters(conn)`; record a `run_steps` row for `step_type='cluster-build'`; emit events
  - Iterate batches of 40 clusters: for each batch, emit `step_start`; call `_pipeline_batch()`; on success record `run_steps` row, call `_apply_results()`, emit `step_done`; on failure record error in `run_steps`, emit error event, continue
  - After all batches: update `run_log` row with `status='success'`, `finished_at`; emit `run_done` event
  - On unhandled exception: update `run_log` with `status='error'`, `error_msg`, `finished_at`; emit `error` event; re-raise
  - Return total transactions updated
- [ ] 2.7 Implement the `emit` call sites. Each `emit(event)` call constructs a dict matching the SSE event schema:
  ```python
  {"type": "step_start", "step": "sync", "ts": now_ms(), "data": {}}
  {"type": "step_done", "step": "sync", "ts": now_ms(), "data": {"new_transactions": N}}
  {"type": "step_start", "step": "enrich-batch", "ts": ..., "data": {"batch_index": i, "batch_total": total}}
  {"type": "step_done", "step": "enrich-batch", "ts": ..., "data": {"batch_index": i, "tokens_in": N, "tokens_out": M, ...}}
  {"type": "run_done", "step": null, "ts": ..., "data": {"run_id": ..., "status": "success", "transactions_updated": N, "duration_ms": D}}
  {"type": "error", "step": ..., "ts": ..., "data": {"message": "..."}}
  ```
  If `emit is None`, skip the call silently.
- [ ] 2.8 Add a helper `now_ms() -> int` to `pipeline.py` that returns current time as unix milliseconds.

---

## 3. Deprecation warnings in old functions

- [ ] 3.1 In `finance/ai/categorize.py`, add `import warnings` at the top and insert `warnings.warn("categorize_uncategorized() is deprecated; use run_pipeline() from finance.ai.pipeline instead.", DeprecationWarning, stacklevel=2)` at the start of `categorize_uncategorized()`.
- [ ] 3.2 Do the same for `categorize_all()` in `categorize.py`.
- [ ] 3.3 In `finance/ai/enrich.py`, add the same deprecation warning at the start of `enrich_transactions()`.
- [ ] 3.4 Confirm: running `finance categorize` from the CLI still works (executes, produces output) but emits a DeprecationWarning to stderr.

---

## 4. Web routes: /pipeline and /pipeline/run/stream

- [ ] 4.1 In `finance/web/app.py`, add the import: `from finance.ai.pipeline import run_pipeline`
- [ ] 4.2 Add `GET /pipeline` route that:
  - Queries the last 20 rows from `run_log` ordered by `started_at DESC`
  - Passes them as `runs` to `pipeline.html`
  - Returns `templates.TemplateResponse("pipeline.html", {"request": request, "runs": runs})`
- [ ] 4.3 Add `GET /pipeline/run/stream` route that returns a `StreamingResponse` with `media_type="text/event-stream"`:
  - The generator function opens its own DB connection directly (not via `Depends(get_db)` — see design Decision 3)
  - Calls `run_pipeline(conn, emit=emit_fn, run_sync=True)`
  - `emit_fn` converts each event dict to SSE format: `f"data: {json.dumps(event)}\n\n"` and yields it
  - Closes the DB connection in a `finally` block
  - Sets response headers: `Cache-Control: no-cache`, `X-Accel-Buffering: no` (prevents nginx buffering)
- [ ] 4.4 Add `GET /pipeline` to the nav in `finance/web/templates/base.html` as "Pipeline" (after "Recurring")

---

## 5. Template: pipeline.html

- [ ] 5.1 Create `finance/web/templates/pipeline.html` extending `base.html`.
- [ ] 5.2 Add a "Run Pipeline" button (`id="run-btn"`) that, when clicked, disables itself, reveals the streaming panel, and creates an `EventSource` pointing to `/pipeline/run/stream`.
- [ ] 5.3 Add a streaming panel (`id="stream-panel"`, hidden by default via Tailwind `hidden` class):
  - Each SSE event (`step_start`, `step_done`, `enrich-batch` events) appends a row to the panel
  - Show: step name, status icon (⟳ running / ✓ done / ✗ error), elapsed time, and for LLM steps: `tokens_in` / `tokens_out` and batch index
  - For `enrich-batch` step_done events, show a summary of what the batch returned (e.g., "Netflix → Subscriptions & Software (recurring)")
  - On `run_done` event: show final summary line, re-enable "Run Pipeline" button, reload the run history table (full page reload via `location.reload()` is acceptable)
  - On `error` event for catastrophic failure: show error message in red, re-enable button, close EventSource
- [ ] 5.4 Add a run history table below the button + panel, listing `runs` from template context:
  - Columns: ID, Type, Started, Duration, Status
  - Duration computed in template as `(finished_at - started_at) / 1000` seconds (show "—" if `finished_at` is null)
  - Status shown as colored badge: `success` → green, `error` → red, `running` → yellow
- [ ] 5.5 Implement all JS inline in the template (no separate JS files); use `addEventListener` on the `EventSource` for `message` events (default event type when server uses `data:` without `event:` field)

---

## 6. Dashboard: Recent Runs widget

- [ ] 6.1 In `finance/web/app.py`, modify the `GET /` (index) route to also query the last 5 rows from `run_log` ordered by `started_at DESC` and pass them as `recent_runs` to `index.html`.
- [ ] 6.2 In `finance/web/templates/index.html`, add a "Recent Runs" card in the existing card grid:
  - Shows up to 5 recent runs
  - Each row: status badge, run type, relative time ("2 hrs ago"), duration in seconds
  - If no runs exist yet, show "No pipeline runs yet. Go to Pipeline to run."
  - Include a link to `/pipeline`

---

## 7. CLI: finance pipeline command

- [ ] 7.1 In `finance/cli.py`, add a `@main.command("pipeline")` command with an `--enrich-only` flag (is_flag=True, default False).
- [ ] 7.2 The command calls `run_pipeline(conn, emit=cli_emit, run_sync=not enrich_only)` where `cli_emit` pretty-prints each event to stdout (e.g., `[sync] done — 5 new transactions`).
- [ ] 7.3 On completion, print total transactions updated and duration.
- [ ] 7.4 Remove the existing `finance categorize` and `finance enrich` CLI commands (or mark them deprecated with a note in their help text pointing to `finance pipeline`). They still work internally due to task 3 above.

---

## 8. Verification

- [ ] 8.1 Start the web app and navigate to `/pipeline`. Confirm the page loads with an empty run history.
- [ ] 8.2 Click "Run Pipeline". Confirm the streaming panel appears and SSE events arrive in the browser (check DevTools → Network → EventStream).
- [ ] 8.3 After the run completes, confirm the run history table shows the new run with `status = 'success'`.
- [ ] 8.4 Confirm `run_steps` rows were inserted: `sqlite3 data/finance.db "SELECT step_type, tokens_in, tokens_out FROM run_steps ORDER BY id DESC LIMIT 10;"`.
- [ ] 8.5 Navigate to `/transactions` and confirm some transactions have been re-categorized (non-null `category` and `categorized_at`).
- [ ] 8.6 Navigate to `/` and confirm the "Recent Runs" widget shows the run.
- [ ] 8.7 Run `finance pipeline` from the CLI and confirm progress events print to stdout.
- [ ] 8.8 Confirm `finance categorize` still works but emits a DeprecationWarning to stderr.
