## MODIFIED Requirements

### Requirement: /pipeline route — run history page

The application SHALL expose a `GET /pipeline` route that renders `finance/web/templates/pipeline.html`. The route SHALL query `run_log` for all runs (most recent first, limit 50) and join with `run_steps` to provide per-run aggregate token usage. The route SHALL also query the current transaction state (total count, uncategorized count, recurring count, review queue count, and category distribution) from the transactions table to populate a "Current State" panel. The template SHALL display:

- A "Current State" panel at the top showing: total transactions, uncategorized count, recurring count, review queue depth, and top categories by transaction count.
- A "Run Pipeline" button below the Current State panel.
- A streaming progress panel (hidden by default) that becomes visible when the button is clicked.
- A run history table with columns: Run ID, Type, Started, Duration, Status, Txns, Tokens In, Tokens Out, Error.

#### Scenario: Pipeline page loads with current state
- **WHEN** a browser navigates to `/pipeline`
- **THEN** the "Current State" panel shows counts for: total transactions, uncategorized, recurring, needs_review; and a list of top categories with their counts
- **THEN** the run history table and "Run Pipeline" button are visible

#### Scenario: Current state reflects zero uncategorized
- **WHEN** all transactions have been categorized
- **THEN** the "Current State" panel shows uncategorized count as 0

#### Scenario: Run history Txns and Tokens columns
- **WHEN** a completed run has a non-null `summary` in `run_log`
- **THEN** the run history row shows `summary.transactions_enriched` in the Txns column and the sum of `tokens_in + tokens_out` from `summary` in the Tokens column

#### Scenario: Run history row with null summary
- **WHEN** a run has no `summary` (failed early or pre-analytics)
- **THEN** the Txns and Tokens cells show "—"

---

### Requirement: /pipeline route — streaming progress panel per-batch categories

The streaming progress panel in `pipeline.html` SHALL display per-batch category breakdowns in addition to token counts. When a `step_done` event arrives for an `enrich-batch` step, the step row SHALL expand to show the top categories assigned in that batch (from `response_summary.categories_assigned`), rendered as compact pill badges.

#### Scenario: Completed batch shows category pills
- **WHEN** an enrich-batch `step_done` event arrives with a `response_summary` containing `categories_assigned`
- **THEN** the step row shows the top 5 categories (by count) as small pills alongside the token count
- **THEN** categories with count > 1 show the count next to the category name (e.g., "Dining ×3")

#### Scenario: Batch with empty categories_assigned
- **WHEN** `response_summary.categories_assigned` is empty
- **THEN** no category pills are rendered for that batch row
