## 1. Analysis Layer

- [x] 1.1 Add `likely_cancelled` branch to status logic in `get_recurring()` in `finance/analysis/review.py` — triggers when `days_until_next <= -interval_days`; update sort key to place `likely_cancelled` after `past_due`
- [x] 1.2 Implement `get_recurring_spend_timeline(conn, months=13, future_months=3)` in `finance/analysis/review.py` — generate month list, query actual charges, compute ghost slots and projected slots per merchant, return structured dict

## 2. Route

- [x] 2.1 Import `get_recurring_spend_timeline` in `finance/web/app.py`
- [x] 2.2 Call `get_recurring_spend_timeline(conn)` in the `/recurring` route; assemble Chart.js JSON (`spend_chart_json`) with actual stacked datasets, ghost dataset, and projected stacked datasets using the 10-color palette; pass `has_spend_data` boolean and `today_index` (index of the last past month, for the divider) to the template

## 3. Template

- [x] 3.1 Add the spend timeline chart card to `finance/web/templates/recurring.html` above the existing table — include chart canvas, `has_spend_data` guard, and placeholder message
- [x] 3.2 Add Chart.js initialization script: stacked actual bars, non-stacked ghost bar, stacked projected bars, tooltip dollar formatting, legend toggle, and `afterDraw` today-divider plugin
- [x] 3.3 Update the recurring table's Status cell to render `likely_cancelled` rows with muted gray row text and a red "Cancelled?" badge
