## MODIFIED Requirements

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
