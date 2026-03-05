## ADDED Requirements

### Requirement: Chart projected-total label
The `/recurring` route SHALL compute `chart_projected_total` (float): the sum of all merchants' `projected` values for the first future month (`future_months[0]`) from the timeline data. This represents the total expected recurring spend in the next calendar month. It SHALL be passed to the template and displayed as a label in the chart card header.

#### Scenario: Projected total reflects next-month sum
- **WHEN** two merchants each project $10.00 in the first future month
- **THEN** `chart_projected_total` is `20.00` and the chart header shows "~$20.00 projected next month" (or similar)

#### Scenario: Zero projected total handled gracefully
- **WHEN** no merchants have projected spend in the next month
- **THEN** `chart_projected_total` is `0.0` and the label is either hidden or shows "$0.00"
