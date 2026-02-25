## ADDED Requirements

### Requirement: Compute LLM cost per pipeline run

The pipeline dashboard SHALL calculate an estimated dollar cost for each past pipeline run using the token counts stored in `run_log.summary` and the known pricing for `claude-haiku-4-5-20251001`:

- Input tokens: $0.80 per 1,000,000 tokens
- Output tokens: $4.00 per 1,000,000 tokens

The cost SHALL be computed in `finance/web/app.py` within the `pipeline_page` handler, in the same loop that parses `summary` JSON, and stored as `computed_cost_usd` (float) on the run dict.

If `tokens_in` or `tokens_out` is missing or the summary is absent, `computed_cost_usd` SHALL be `None`.

#### Scenario: Run has token data

- **WHEN** a run's `summary` JSON contains both `tokens_in` and `tokens_out`
- **THEN** `computed_cost_usd` is set to `(tokens_in * 0.80 + tokens_out * 4.00) / 1_000_000`

#### Scenario: Run has no token data

- **WHEN** a run's `summary` is NULL or does not contain `tokens_in`/`tokens_out`
- **THEN** `computed_cost_usd` is `None`
