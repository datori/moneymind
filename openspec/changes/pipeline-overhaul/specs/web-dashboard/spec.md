## MODIFIED Requirements

### Requirement: Dashboard index — "Recent Runs" widget

The `GET /` route SHALL pass a `recent_runs` list to the `index.html` template. The list SHALL contain the 5 most recent rows from `run_log`, ordered by `started_at DESC`, each with: `id`, `run_type`, `started_at` (formatted as a human-readable datetime string), `finished_at`, `status`, and `error_msg`.

`index.html` SHALL render a "Recent Runs" section below the existing Credit Utilization section. The section SHALL display the runs in a table with columns: Run ID, Type, Started, Duration, Status. Status SHALL be color-coded: green for `success`, yellow for `running`, red for `error`. If no runs exist, the section SHALL display "No pipeline runs yet."

#### Scenario: Dashboard loads with no prior runs
- **WHEN** a browser navigates to `/` and `run_log` is empty
- **THEN** the "Recent Runs" section renders with the message "No pipeline runs yet."

#### Scenario: Dashboard loads with recent runs
- **WHEN** `run_log` contains one or more rows
- **THEN** the "Recent Runs" widget shows up to 5 most recent runs with their status, start time, and duration
- **THEN** successful runs show a green status indicator, errored runs show red

#### Scenario: Running pipeline appears in widget
- **WHEN** a pipeline run is in progress (`status = 'running'`)
- **THEN** the dashboard shows that run with a yellow "running" status and no duration (since `finished_at` is NULL)

---

### Requirement: /pipeline route — run history page

The application SHALL expose a `GET /pipeline` route that renders `finance/web/templates/pipeline.html`. The route SHALL query `run_log` for all runs (most recent first, limit 50) and join with `run_steps` to provide per-run step counts and total token usage. The template SHALL display:

- A "Run Pipeline" button at the top of the page.
- A streaming progress panel (hidden by default) that becomes visible when the button is clicked.
- A run history table with columns: Run ID, Type, Started, Finished, Duration, Status, Steps, Total Tokens In, Total Tokens Out, Error.

#### Scenario: Pipeline page loads
- **WHEN** a browser navigates to `/pipeline`
- **THEN** the page renders with the run history table and the "Run Pipeline" button visible
- **THEN** the streaming progress panel is not visible

#### Scenario: Empty run history
- **WHEN** `run_log` is empty
- **THEN** the run history table shows "No runs yet."

#### Scenario: Run history shows all runs
- **WHEN** `run_log` has rows
- **THEN** each row in the table shows the run's ID, status (color-coded), started time, duration, and aggregate token usage summed from `run_steps`

---

### Requirement: /pipeline route — streaming progress panel

The streaming progress panel in `pipeline.html` SHALL use JavaScript `EventSource` to consume the `GET /pipeline/run/stream` SSE endpoint. The panel SHALL:

- Show each pipeline step as a row with: step name, status icon (spinner while running, checkmark on success, X on error), elapsed time, and for LLM steps: "batch N/M", tokens in, tokens out.
- Append new step rows as `step_start` events arrive.
- Update existing step rows in-place when the corresponding `step_done` event arrives.
- Show a final summary banner when `run_done` arrives with total transactions updated and total wall-clock duration.
- Refresh the run history table after `run_done` by reloading the page or fetching updated table HTML.

#### Scenario: Streaming panel shows live batch progress
- **WHEN** the pipeline is processing enrich batch 3 of 7
- **THEN** the panel shows "Enrich batch 3/7" with a spinner and the elapsed time since that batch started

#### Scenario: Completed step shows token counts
- **WHEN** an enrich batch completes
- **THEN** the step row updates to show a checkmark, elapsed ms, tokens in, and tokens out for that batch

#### Scenario: Error step shown in red
- **WHEN** an enrich batch emits an error event
- **THEN** the step row shows a red X and the error message text; subsequent batches continue to appear

#### Scenario: Run completes — history refreshes
- **WHEN** the `run_done` event is received
- **THEN** the "Run Pipeline" button re-enables, a success banner shows the summary, and the run history table updates to include the newly completed run
