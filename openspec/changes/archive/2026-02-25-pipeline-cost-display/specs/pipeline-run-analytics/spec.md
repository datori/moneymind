## MODIFIED Requirements

### Requirement: Pipeline run history table displays token and cost summary

The pipeline dashboard run history table SHALL display a "Cost" column alongside the existing token total column for each past run.

- When `computed_cost_usd` is not None, it SHALL be formatted as `$X.XXXX` (4 decimal places) to show sub-cent precision for small runs.
- When `computed_cost_usd` is None, the cell SHALL display `—`.
- The cost column SHALL appear immediately after (or adjacent to) the token count column.

#### Scenario: Run with cost data shows formatted cost

- **WHEN** the past runs table renders a row where `computed_cost_usd` is set
- **THEN** the cost cell displays a value like `$0.0042`

#### Scenario: Run without token data shows dash

- **WHEN** the past runs table renders a row where `computed_cost_usd` is None
- **THEN** the cost cell displays `—`
