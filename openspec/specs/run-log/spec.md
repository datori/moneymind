## ADDED Requirements

### Requirement: run_log table

The database SHALL contain a `run_log` table that records every top-level pipeline execution. The schema is:

```sql
CREATE TABLE IF NOT EXISTS run_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type    TEXT NOT NULL,          -- 'full' | 'enrich-only'
    started_at  INTEGER NOT NULL,       -- unix ms
    finished_at INTEGER,                -- unix ms; NULL while running
    status      TEXT NOT NULL,          -- 'running' | 'success' | 'error'
    error_msg   TEXT                    -- NULL on success
);
```

A new row with `status = 'running'` SHALL be inserted before any pipeline work begins. On successful completion, `finished_at` and `status = 'success'` SHALL be written. On failure, `status = 'error'` and `error_msg` SHALL be set.

#### Scenario: Run starts
- **WHEN** `run_pipeline(conn)` is called
- **THEN** a row is inserted into `run_log` with `status = 'running'` and `started_at` set to the current time in unix milliseconds before any sync or LLM call is made

#### Scenario: Run succeeds
- **WHEN** all pipeline steps complete without error
- **THEN** the `run_log` row is updated with `status = 'success'` and `finished_at` set to the current time

#### Scenario: Run fails
- **WHEN** an unhandled exception terminates the pipeline
- **THEN** the `run_log` row is updated with `status = 'error'` and `error_msg` containing the exception message; `finished_at` is still recorded

---

### Requirement: run_steps table

The database SHALL contain a `run_steps` table that records each individual step within a pipeline run. The schema is:

```sql
CREATE TABLE IF NOT EXISTS run_steps (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           INTEGER NOT NULL REFERENCES run_log(id),
    step_type        TEXT NOT NULL,   -- 'sync' | 'cluster-build' | 'enrich-batch' | 'write-results'
    batch_index      INTEGER,         -- 1-based; NULL for non-batch steps
    batch_total      INTEGER,         -- total batch count; NULL for non-batch steps
    started_at       INTEGER NOT NULL,-- unix ms
    finished_at      INTEGER,         -- unix ms; NULL while step is running
    request_summary  TEXT,            -- JSON string summarizing what was sent to the LLM
    response_summary TEXT,            -- JSON string summarizing what was received
    tokens_in        INTEGER,         -- prompt tokens consumed; NULL for non-LLM steps
    tokens_out       INTEGER,         -- completion tokens produced; NULL for non-LLM steps
    error_msg        TEXT             -- NULL on success
);
```

A row SHALL be inserted at the start of each step with `finished_at = NULL`. On completion (success or error), `finished_at`, token counts, summaries, and any error message SHALL be written.

`request_summary` for an `enrich-batch` step SHALL be a JSON object with at least: `{"cluster_count": N, "merchant_keys": [...first 5 keys...]}`.

`response_summary` for an `enrich-batch` step SHALL be a JSON object with at least: `{"cluster_count": N, "categories_assigned": [...], "recurring_count": K}`.

#### Scenario: Sync step recorded
- **WHEN** the pipeline runs a SimpleFIN sync as the first step
- **THEN** a `run_steps` row with `step_type = 'sync'` is created; on completion it records `finished_at` and `error_msg` if sync failed (step failure does not abort the run)

#### Scenario: Cluster-build step recorded
- **WHEN** `build_clusters(conn)` completes
- **THEN** a `run_steps` row with `step_type = 'cluster-build'` and `finished_at` is written; `request_summary` contains `{"transaction_count": N, "cluster_count": M}`

#### Scenario: Enrich batch step recorded
- **WHEN** a batch of clusters is sent to the LLM and a response is received
- **THEN** a `run_steps` row with `step_type = 'enrich-batch'`, the correct `batch_index`, `batch_total`, `tokens_in`, `tokens_out`, `request_summary`, and `response_summary` is written

#### Scenario: Failed enrich batch recorded
- **WHEN** the LLM call for a batch raises an exception
- **THEN** the `run_steps` row for that batch is updated with `error_msg` set; the overall run continues processing remaining batches

#### Scenario: Write-results step recorded
- **WHEN** all enrichment results are bulk-written back to the transactions table
- **THEN** a `run_steps` row with `step_type = 'write-results'` records the number of rows updated in `response_summary` as `{"transactions_updated": N}`
