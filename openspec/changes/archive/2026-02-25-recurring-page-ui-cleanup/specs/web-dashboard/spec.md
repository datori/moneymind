## MODIFIED Requirements

### Requirement: Recurring page — spend timeline chart

The `GET /recurring` route SHALL render a Chart.js stacked bar chart above the recurring charges table showing monthly recurring spend per merchant. The chart SHALL span the past 13 calendar months (ending with the current month) plus 3 projected future months, for 16 total x-axis labels.

The chart SHALL include:
- **Actual spend datasets**: one stacked bar dataset per merchant, colored from the standard 10-color palette, showing total absolute dollars charged per month
- **Ghost dataset**: a single non-stacked outlined bar dataset (gray, dashed border) showing the total expected-but-missing dollar amount per month across all merchants; labeled "Expected (not received)" in the tooltip; not shown in the legend
- **Projected datasets**: one stacked bar dataset per merchant (same colors at 40% opacity) for the 3 future months, showing projected charges based on `typical_amount` and `interval_days`
- **Today divider**: a vertical dashed gray line drawn between the last past month and first future month using a Chart.js `afterDraw` plugin
- **Y axis**: dollar amounts, formatted as `$X.XX` in tooltips; `beginAtZero: true`
- **Legend**: displayed when more than one merchant; legend click toggles merchant visibility client-side

The route SHALL call `get_recurring_spend_timeline(conn)` to build chart data. Chart JSON SHALL be passed to the template as `spend_chart_json` (safe). A boolean `has_spend_data` SHALL be passed; when `False`, a placeholder message SHALL be shown instead of the chart.

Below the chart, the route SHALL render the recurring charges table using three grouped sections (Needs Attention, Active Subscriptions, Likely Cancelled) as specified in the `recurring-detection` capability. The route SHALL pre-group the `get_recurring()` result into `attention`, `active`, and `cancelled` lists before passing to the template.

#### Scenario: Recurring chart renders with active merchants

- **WHEN** `GET /recurring` is requested and multiple active recurring merchants exist
- **THEN** the page renders a stacked bar chart with one colored dataset per merchant and a legend

#### Scenario: Ghost bars visible for cancelled merchant

- **WHEN** a merchant's last charge was more than one interval ago
- **THEN** the ghost dataset has non-zero values in the months where charges were expected but absent, displayed as outlined gray bars

#### Scenario: Projected bars appear in future months

- **WHEN** an active merchant is expected to charge in the next 3 months
- **THEN** lighter-colored bars appear in the future-month columns for that merchant

#### Scenario: Today divider separates past from projected

- **WHEN** the chart renders
- **THEN** a vertical dashed gray line appears between the current month column and the first future month column

#### Scenario: No recurring data shows placeholder

- **WHEN** `has_spend_data` is `False`
- **THEN** a placeholder message is shown instead of the chart canvas

#### Scenario: Table renders in grouped sections below chart

- **WHEN** `GET /recurring` is requested and recurring merchants exist across multiple urgency tiers
- **THEN** the page shows the spend timeline chart at top, followed by the grouped table sections (Needs Attention, Active Subscriptions, Likely Cancelled)
