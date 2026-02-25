## 1. Backend: Compute cost in pipeline_page handler

- [x] 1.1 Add Haiku pricing constants near the top of `finance/web/app.py` (`HAIKU_INPUT_COST_PER_M = 0.80`, `HAIKU_OUTPUT_COST_PER_M = 4.00`)
- [x] 1.2 In the `pipeline_page` handler, after parsing `run["summary"]`, compute `computed_cost_usd` from `tokens_in` and `tokens_out` and attach it to the run dict (set to `None` if token data is absent)

## 2. Frontend: Display cost column in run history table

- [x] 2.1 Add a "Cost" column header to the past runs table in `finance/web/templates/pipeline.html`
- [x] 2.2 In each run row, render `computed_cost_usd` formatted as `$X.XXXX` when present, or `—` when None
