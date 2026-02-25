## Context

The recurring page already computes `interval_days`, `last_date`, `typical_amount`, and `status` per merchant via `get_recurring()`. This design adds a parallel `get_recurring_spend_timeline()` that reuses the same raw transaction data but produces a month-bucketed structure for chart rendering.

Chart.js is already loaded via CDN in `base.html`. The accounts page established the pattern: server assembles a JSON blob, the template renders a Chart.js bar chart. This change follows the same pattern but adds two new visual layers: ghost bars (expected-but-missing) and projected future bars.

## Goals / Non-Goals

**Goals:**
- Show 13 months of actual recurring spend per merchant as a stacked bar chart
- Overlay a single combined ghost bar for months where expected charges didn't appear
- Project 3 future months of expected spend as lighter bars
- Visually separate past from future with a vertical "today" divider
- Add `likely_cancelled` status to `get_recurring()` for merchants overdue > 1 full interval
- Style `likely_cancelled` rows distinctively in the table

**Non-Goals:**
- Per-merchant ghost bars (combined ghost bar is sufficient; table handles per-merchant status)
- User-selectable merchant filter (Chart.js legend click handles show/hide client-side)
- Persisting cancellation state to the database
- Handling sub-monthly recurring items (weekly, bi-weekly) differently — they're treated like any other merchant

## Decisions

### D1: Two separate functions vs. enriching `get_recurring()`

**Decision**: New `get_recurring_spend_timeline()` function, separate from `get_recurring()`.

**Rationale**: `get_recurring()` is already used by the table and is called first. The timeline needs a different return shape (month-bucketed arrays). Merging them would make `get_recurring()` return an awkward hybrid. Separate functions keep each focused and easy to test.

### D2: Expected-charge projection algorithm

**Decision**: Generate expected charge months by stepping backward and forward from `last_date` using `interval_days`.

**Rationale**: Simpler than generating from `first_date` (avoids drift over long histories). Starting from `last_date` and stepping backwards by `interval_days` produces the most accurate expected dates for recent history.

Ghost bar threshold: a month is "expected but missing" if the projected charge date for that month falls more than `tolerance` days before today and no actual charge exists. `tolerance = max(3, int(interval_days * 0.35))` (same as `get_recurring()`).

For future months: project forward from `last_date + interval_days` (i.e., `next_due_date`), stepping by `interval_days`.

### D3: Ghost bars — combined vs. per-merchant

**Decision**: One combined ghost dataset (total expected-but-missing $ per month), not per-merchant.

**Rationale**: Per-merchant ghost bars require careful stacking math in Chart.js to avoid obscuring actual bars. A single combined outlined bar is simpler, clearly signals "something was expected here," and avoids the visual complexity of mixing stacked and non-stacked layers. Per-merchant detail is available in the table.

Ghost bar rendering: `backgroundColor: 'rgba(156,163,175,0.12)'`, `borderColor: '#9ca3af'`, `borderWidth: 1.5`, `borderDash: [4,2]`, not stacked, no legend entry (using a custom label "Expected (not received)").

### D4: Projected bars — opacity per-merchant vs. combined

**Decision**: Per-merchant projected datasets, same colors at 40% opacity, stacked.

**Rationale**: Projected bars appear in the future-month columns. Using per-merchant colors (dimmed) makes clear "Netflix is projected to charge $15.99 in March." Stacking them gives the total projected monthly commitment. Consistent with the actual spend stacking.

### D5: Today divider implementation

**Decision**: Chart.js `afterDraw` plugin using canvas drawing (a vertical dashed gray line).

**Rationale**: No annotation plugin needed. The divider sits between the last past month and first future month. Implementation: calculate x-position of the boundary between month index `(months-1)` and `months`, draw a vertical dashed line with `ctx.setLineDash`.

### D6: `likely_cancelled` threshold

**Decision**: `days_until_next < -interval_days` → `"likely_cancelled"`.

**Rationale**: If a merchant is overdue by more than a full interval, it almost certainly stopped charging. Examples: monthly → overdue > 30d, annual → overdue > 365d. This is a more lenient threshold than 1.5x to catch cancellations that happened mid-cycle.

Table styling for `likely_cancelled`: muted gray row text + a red "Cancelled?" badge in the Status cell.

### D7: Y-axis — dollars not counts

**Decision**: Y axis in dollars, tooltips formatted as `$X.XX`.

**Rationale**: The accounts chart used counts (volume). For recurring spend, dollar amount is the actionable metric. Chart.js tooltip callback formats `ctx.parsed.y` as `$${ctx.parsed.y.toFixed(2)}`.

## Risks / Trade-offs

- **Irregular intervals produce noisy ghost bars**: A merchant with high interval variance (e.g., "Every ~45d") may generate ghost bars for months where the charge was just a few weeks late. Mitigation: the `tolerance` factor absorbs minor jitter; only confirmed gaps beyond `tolerance` trigger ghost bars.
- **Weekly/bi-weekly merchants produce multiple expected charges per month**: The aggregation sums all expected charges within a calendar month, so a weekly charge at $5 generates ~$20/month. This is correct but may surprise users who expect to see individual charges. Acceptable for a summary chart.
- **Future projections assume steady interval**: If a user price-adjusted (e.g., Netflix raised price), projected amounts use `typical_amount` (median historical), not the new price. Acceptable limitation for now.

## Migration Plan

No database changes. No data migration. Route and template changes are backward-compatible. Ship as a single commit.
