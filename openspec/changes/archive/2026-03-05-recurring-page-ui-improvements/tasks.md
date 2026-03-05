## 1. Route — Summary Stats & Cadence Grouping

- [x] 1.1 In `finance/web/app.py` `/recurring` route, compute `summary_monthly_total` (sum of per-item monthly-equivalent cost for non-cancelled items with known `interval_days`)
- [x] 1.2 Compute `summary_annual_total = summary_monthly_total * 12`
- [x] 1.3 Compute `summary_due_soon_count` (attention items where `abs(days_until_next) <= 7`)
- [x] 1.4 Build `active_groups` list: bucket active items by cadence (Weekly/Monthly/Quarterly/Annual/Other via `interval_days`), compute per-group `subtotal_monthly`, omit empty groups
- [x] 1.5 Compute `chart_projected_total` from `timeline["merchants"]` — sum of each merchant's `projected[0]` (first future month)
- [x] 1.6 Pass all new variables (`summary_monthly_total`, `summary_annual_total`, `summary_due_soon_count`, `active_groups`, `chart_projected_total`) to the template context

## 2. Template — Summary Strip

- [x] 2.1 Add a three-chip summary strip between the page `<h1>` and the chart card, showing: Monthly (~$X), Annual (~$X), and Due Soon (N)
- [x] 2.2 Style chips consistently with the rest of the page (white card, border, rounded, small label + large value)

## 3. Template — Chart Header Label

- [x] 3.1 In the chart card header row, add the projected-total label ("~$X next month") next to the existing "Monthly Recurring Spend" heading, only when `chart_projected_total > 0`

## 4. Template — Consistent Status Pills

- [x] 4.1 Rewrite the `status_cell` macro to always return a colored `<span>` badge: red for `past_due`, blue for `due_any_day`, amber for `due_soon`, light-amber for upcoming ≤7d, gray for upcoming >7d and ≤30d, muted-gray for upcoming >30d, red-muted for `likely_cancelled`
- [x] 4.2 Apply the updated macro in all three sections (Attention, Active, Cancelled) — no section should use raw colored text anymore

## 5. Template — Attention Row Background Tints

- [x] 5.1 Add conditional `bg-red-50` / `bg-blue-50` / `bg-amber-50` row class to Attention table rows based on status (keep the left-border accent as a secondary cue)

## 6. Template — Active Subscriptions by Cadence

- [x] 6.1 Replace the single Active Subscriptions table with a loop over `active_groups`
- [x] 6.2 Each group has a labeled sub-header (e.g., "Monthly") and its own `<table>`
- [x] 6.3 Add a subtotal footer row at the bottom of each group table showing the `~/mo` monthly-equivalent total for that group

## 7. Template — Harmonize Cancelled Section Header

- [x] 7.1 Replace the `<details>/<summary>` pattern with the same `<div class="mb-4">` + `flex items-center gap-2` header used by Attention and Active sections
- [x] 7.2 Add a JS-toggled collapse (chevron icon button) to the Cancelled header to preserve collapsed-by-default behavior
- [x] 7.3 Default the Cancelled section body to `hidden`, toggled by clicking the header chevron

## 8. Financial Category Exclusion

- [x] 8.1 Add `category` field to `get_recurring()` SQL query (dominant category per merchant via MODE aggregate or subquery)
- [x] 8.2 In the `/recurring` route, exclude items with `category = 'Financial'` from `attention`, `active`, `cancelled`, `active_groups`, and all summary stat calculations
- [x] 8.3 Add `AND amount < 0` filter to `get_recurring()` SQL query to exclude income/credit transactions (e.g. payroll) from recurring charge detection
