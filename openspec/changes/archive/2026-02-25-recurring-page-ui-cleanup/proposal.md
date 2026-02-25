## Why

The recurring charges page is hard to scan: all merchants render in a single flat table regardless of urgency, `likely_cancelled` entries pollute the active view, and the most important signal (status) is the last column. Users need to immediately see what requires action and separate that from healthy subscriptions.

## What Changes

- The `/recurring` page table is replaced with **three visual sections**: "Needs Attention" (past_due, due_any_day, due_soon), "Active Subscriptions" (upcoming, None), and "Likely Cancelled" (collapsed by default via `<details>`)
- **Colored left-border stripes** per row in the Needs Attention section: red for past_due, blue for due_any_day, amber for due_soon
- **Columns simplified** to: Merchant · Interval · Typical Amount · Next Due · Status (dropping Total Spent and Occurrences from the table — visible in chart)
- **Server-side grouping** in the `/recurring` route: passes `attention`, `active`, `cancelled` lists separately instead of a flat `recurring` list
- The `GET /recurring` spec is updated to reflect the new layout and column structure

## Capabilities

### New Capabilities

*(none — this is a UI-only rework of an existing page)*

### Modified Capabilities

- `web-dashboard`: The `GET /recurring` route rendering requirement changes — new sectioned layout, new column set, collapsed Likely Cancelled section

## Impact

- `finance/web/templates/recurring.html`: full rewrite of table section
- `finance/web/app.py`: `/recurring` route — groups data into `attention`, `active`, `cancelled` before passing to template
- `openspec/specs/web-dashboard/spec.md`: updated `/recurring` display requirement
