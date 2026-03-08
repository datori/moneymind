## ADDED Requirements

### Requirement: SSE streaming endpoint

The application SHALL expose a `GET /pipeline/run/stream` route that triggers the pipeline and streams Server-Sent Events (SSE) to the client as each step starts and completes. The response SHALL have `Content-Type: text/event-stream` and be implemented with FastAPI's `StreamingResponse`.

Each SSE event SHALL be a single `data:` line containing a JSON-encoded object followed by two newlines (`\n\n`). The event object SHALL always include at minimum:

```json
{
  "type": "step_start" | "step_done" | "run_done" | "error",
  "step": "sync" | "cluster-build" | "enrich-batch" | "write-results" | null,
  "ts": <unix_ms>,
  "data": { ... }
}
```

For `enrich-batch` events, `data` SHALL include `batch_index`, `batch_total`, and on `step_done`: `tokens_in`, `tokens_out`, `request_summary`, `response_summary`.

For `run_done`, `data` SHALL include `run_id`, `status`, `transactions_updated`, and `duration_ms`.

For `error`, `data` SHALL include `message` containing the error string.

The endpoint SHALL run the pipeline synchronously in a generator function using `yield` statements to emit SSE events, wrapped in `StreamingResponse`. The connection SHALL be closed by the server after the `run_done` or `error` event is emitted.

#### Scenario: Client connects to stream endpoint
- **WHEN** a browser `EventSource` connects to `GET /pipeline/run/stream`
- **THEN** the server immediately emits a `step_start` event for the first pipeline step (sync)

#### Scenario: Each step emits start and done events
- **WHEN** each pipeline step begins
- **THEN** a `step_start` event is emitted with the step name and current timestamp
- **WHEN** each pipeline step completes
- **THEN** a `step_done` event is emitted with timing and any relevant data (token counts for LLM steps)

#### Scenario: Each enrich batch streams progress
- **WHEN** batch N of M is sent to the LLM
- **THEN** a `step_start` event is emitted with `{"step": "enrich-batch", "data": {"batch_index": N, "batch_total": M}}`
- **WHEN** the LLM returns the response for batch N
- **THEN** a `step_done` event is emitted with token counts and summaries for that batch

#### Scenario: Pipeline completes successfully
- **WHEN** all steps complete and results are written to the database
- **THEN** a `run_done` event is emitted with `status = 'success'`, total `transactions_updated`, and `duration_ms`; the SSE stream closes

#### Scenario: Pipeline step fails
- **WHEN** an individual enrich batch raises an exception
- **THEN** an `error` event is emitted for that batch with `message` containing the error; the stream continues to the next batch rather than closing

#### Scenario: Catastrophic pipeline failure
- **WHEN** an unhandled exception terminates the pipeline before completion
- **THEN** an `error` event is emitted with `message` containing the exception string and the stream closes

---

### Requirement: Pipeline trigger button

The `/pipeline` page SHALL include a "Run Pipeline" button. When clicked, the UI SHALL open a streaming progress panel in-page (not a new tab) and begin consuming the SSE stream from `GET /pipeline/run/stream`. The button SHALL be disabled while a stream is active.

#### Scenario: Run button clicked
- **WHEN** the user clicks "Run Pipeline"
- **THEN** the button becomes disabled, the streaming progress panel becomes visible, and the browser connects an `EventSource` to `/pipeline/run/stream`

#### Scenario: Live step updates appear in panel
- **WHEN** SSE events arrive from the server
- **THEN** each step is shown in the panel with its name, status (running / done / error), elapsed time, and for LLM steps: token counts and batch index

#### Scenario: Stream completes
- **WHEN** the `run_done` event arrives
- **THEN** the panel shows a final summary (transactions updated, total duration), the EventSource is closed, and the "Run Pipeline" button re-enables; the run history table on the page refreshes to include the new run

---

### Requirement: emit callback for pipeline functions

`run_pipeline(conn, emit=None, run_sync=True, full=False)` in `finance/ai/pipeline.py` SHALL accept an optional `emit` callable with signature `emit(event: dict) -> None`. When `emit` is not None, the pipeline SHALL call it at each step boundary with the same event dict that the SSE endpoint would stream. This decouples progress reporting from the HTTP layer and enables CLI usage with a custom emit (e.g., print to stdout).

The `full` parameter SHALL control whether all clusters are sent to the LLM (`full=True`) or only clusters with uncategorized transactions (`full=False`, default).

#### Scenario: Pipeline called with emit=None (CLI or test)
- **WHEN** `run_pipeline(conn)` is called without an emit argument
- **THEN** the pipeline runs normally with no event emission; return value is total transactions updated

#### Scenario: Pipeline called with emit callback (SSE handler)
- **WHEN** `run_pipeline(conn, emit=my_callback)` is called
- **THEN** `my_callback` is invoked at each step boundary with the appropriate event dict

#### Scenario: Cluster-build event reports filtered counts in incremental mode
- **WHEN** `run_pipeline(conn)` runs in incremental mode (default)
- **THEN** the `cluster-build` `step_done` event data includes `cluster_count` (clusters to process), `clusters_skipped` (fully-categorized clusters filtered out), and `transaction_count` (transactions in clusters to process)

---

### Requirement: CLI pipeline command supports full mode

The `finance pipeline` CLI command SHALL accept a `--full` flag that causes the pipeline to re-process all merchant clusters regardless of categorization status.

#### Scenario: Pipeline run without --full
- **WHEN** `finance pipeline` is run without `--full`
- **THEN** `run_pipeline(conn, full=False)` is called (incremental mode)

#### Scenario: Pipeline run with --full
- **WHEN** `finance pipeline --full` is run
- **THEN** `run_pipeline(conn, full=True)` is called (full mode, all clusters processed)
