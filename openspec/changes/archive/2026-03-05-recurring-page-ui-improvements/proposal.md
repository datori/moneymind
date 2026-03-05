## Why

The Recurring Charges page is functional but lacks at-a-glance clarity: there are no summary KPIs, the Active section mixes billing cadences without subtotals, status indicators are visually inconsistent across sections, and minor structural inconsistencies make the page feel unpolished.

## What Changes

- Add a summary strip (stat chips) at the top of the page showing monthly spend, annual spend, and count of subscriptions due within 7 days
- Group the Active Subscriptions table by billing cadence (Monthly / Annual / Other), each group with a subtotal row
- Replace plain-text status labels with consistent colored pills/badges across all three sections (Attention, Active, Cancelled)
- Replace left-border-only row styling on Attention items with subtle row background tints for better scanability
- Harmonize the Cancelled section header to use the same `<div class="flex items-center ...">` pattern as Attention and Active (rather than a raw `<details>` summary)
- Add a current-month projected total label to the chart card header

## Capabilities

### New Capabilities
<!-- None — all changes are presentational within the existing recurring page -->

### Modified Capabilities
- `recurring-detection`: Display requirements changing — summary strip, cadence grouping, consistent status pills, and row tinting are new UI behaviors layered on the existing detection output.
- `recurring-spend-timeline`: Chart header now surfaces a projected-total label derived from timeline data.

## Impact

- `finance/web/templates/recurring.html`: Primary file changed (template logic, layout, macros)
- `finance/web/app.py`: Minor additions to the `/recurring` route — compute summary stats (monthly total, annual total, due-soon count) and current-month projected total for the chart header
- No schema changes, no new dependencies, no MCP tool changes
