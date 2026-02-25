## Why

The pipeline dashboard already shows total token counts for past runs, but tokens alone don't give a meaningful cost signal. Since the pipeline uses `claude-haiku-4-5-20251001` with known, stable pricing, we can compute an exact dollar cost per run and surface it alongside the token count.

## What Changes

- Calculate total LLM cost per pipeline run using Claude Haiku pricing ($0.80/MTok input, $4.00/MTok output)
- Display computed cost (e.g. `$0.0042`) in the past runs table on the pipeline dashboard, next to the existing token total
- Cost is derived at read-time from `tokens_in` / `tokens_out` already stored in `run_log.summary` — no schema changes required

## Capabilities

### New Capabilities

- `pipeline-run-cost`: Display computed LLM cost for each past pipeline run on the dashboard, calculated from stored token counts using Claude Haiku pricing rates

### Modified Capabilities

- `pipeline-run-analytics`: The dashboard display of run summaries now includes a cost column in addition to the existing token total

## Impact

- `finance/web/templates/pipeline.html`: Add cost column to run history table
- `finance/web/app.py`: Optionally compute cost server-side before passing to template (or compute in Jinja2)
- No database changes required
- No new dependencies
