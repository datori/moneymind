## Why

The recurring charges page surfaces subscription status but gives no visual sense of spending trends over time — it's hard to see when a subscription started, whether charges are growing, or confirm that a cancellation actually took hold. A spend timeline with ghost bars for expected-but-missing charges turns the page into an active management tool, not just a status list.

## What Changes

- **New**: `get_recurring_spend_timeline(conn, months=13, future_months=3)` analysis function in `finance/analysis/review.py` — returns monthly actual spend, expected-but-missing (ghost) spend, and projected future spend per recurring merchant
- **New**: `likely_cancelled` status value added to recurring merchant enrichment — triggered when a merchant is overdue by more than one full interval
- **Modified**: `/recurring` route enriched with timeline chart data (stacked actual spend + ghost overlay + projected bars + today divider)
- **Modified**: `recurring.html` template adds a Chart.js stacked bar chart above the existing table

## Capabilities

### New Capabilities
- `recurring-spend-timeline`: Monthly spend chart on the recurring page: stacked bars per merchant (actual $), outlined ghost bars (expected-but-missing), lighter projected bars (next 3 months), vertical today-divider, and `likely_cancelled` status detection

### Modified Capabilities
- `recurring-detection`: `get_recurring()` gains a new `likely_cancelled` status value (overdue by > 1 full interval); existing status logic unchanged
- `web-dashboard`: `/recurring` route and `recurring.html` template gain the spend timeline chart

## Impact

- `finance/analysis/review.py`: new `get_recurring_spend_timeline()` function; `get_recurring()` gains `likely_cancelled` status branch
- `finance/web/app.py`: `/recurring` route imports and calls `get_recurring_spend_timeline()`, assembles Chart.js JSON
- `finance/web/templates/recurring.html`: chart card added above table; `likely_cancelled` table row styling added
- No schema changes, no new dependencies (Chart.js already loaded via CDN in base.html)
