## Context

The pipeline dashboard already retrieves `run_log.summary` (a JSON blob) and parses it server-side in `app.py`. The summary already contains `tokens_in` and `tokens_out` and the template displays their sum. The pipeline uses `claude-haiku-4-5-20251001` exclusively, which has public, stable pricing.

## Goals / Non-Goals

**Goals:**
- Show a computed dollar cost for each past pipeline run on the dashboard
- Keep pricing constants in one maintainable place (not scattered in template logic)

**Non-Goals:**
- Storing cost in the database (derived data, not worth the migration)
- Supporting multiple model pricing (only Haiku is used)
- Cumulative cost totals across runs

## Decisions

**Compute cost in `app.py`, not in the Jinja template.**

Rationale: Jinja2 arithmetic is awkward for floating-point division and formatting. Computing in Python keeps the template clean and lets us format the value properly before passing it. The `pipeline_page` handler already iterates over runs to parse the summary JSON — we add cost computation in the same loop.

Pricing constants go in a small module-level dict or inline constants in `app.py` (not a separate config file — over-engineering for two numbers).

**Pricing used (claude-haiku-4-5-20251001):**
- Input: $0.80 per 1,000,000 tokens
- Output: $4.00 per 1,000,000 tokens

**Cost field added to run dict as `computed_cost_usd` (float or None).**

If `tokens_in` or `tokens_out` is absent from summary, cost is `None` and the template shows `—`.

## Risks / Trade-offs

- [Pricing changes] → If Haiku pricing changes, the constant in `app.py` must be updated manually. Acceptable for a personal tool; no automation needed.
- [Old runs without token data] → Runs before token tracking was added will show `—` gracefully via the None check.
