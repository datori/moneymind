# Design: Explore viz-enhancements

## Overview

The loop made five focused improvements across four templates and one route handler.
Three of the five iterations targeted interactivity (tooltip enrichment and click
navigation); one added a new dataset to an existing chart; one added a brand-new
chart to the only page that had none. The changes are independent — each iteration
works without the others — and all are additive (nothing was removed or restructured).

The unifying pattern: every chart should tell you more on hover, and clicking
something with a dollar value attached should take you to the underlying transactions.

## Iteration Progression

**Iteration 1** — Spending bar chart tooltip. The existing tooltip showed a bare
dollar amount. The loop added the % of total and transaction count to the tooltip,
requiring a small server change to include `counts` in `chart_data_json`. This was
the lowest-friction improvement: purely additive, no layout change, maximum
information gain per hover.

**Iteration 2** — Net worth chart breakdown. The single "Net Worth" line on
`/net-worth` gave no insight into whether changes came from assets or liabilities.
The loop split the server-side computation into three arrays (net worth, assets,
liabilities) and rendered them as three lines: indigo-filled net worth (existing
style, slightly reduced fill opacity), green dashed assets, red dashed liabilities.
The legend was enabled for the first time on this chart.

**Iteration 3** — Spending chart click navigation. Each bar in the spending chart
already linked to filtered transactions from the *table* row (existing behavior via
`<a href>`). The loop made the *chart bars* do the same thing via `onClick` and
`onHover` (cursor pointer). Works for category and merchant groupings; account
grouping is excluded (no meaningful transactions filter for account).

**Iteration 4** — Dashboard doughnut click and tooltip. Applied the same two
improvements from iterations 1 and 3 to the index page doughnut: tooltip shows
`$X.XX (XX.X%)` and clicking a slice navigates to transactions filtered by that
category for the current month's date range.

**Iteration 5** — Daily spending chart on transactions page. The transactions page
(`/transactions`) was the only major page with no visualization. The loop added a
compact daily spending bar chart above the table. The server queries all matching
expense transactions for the selected date range (bypassing the row limit) and
returns daily totals as `txn_chart_json`. The chart is only rendered when a date
range is present and matching data exists.

## Design Decisions

**Tooltip format: `$X.XX (XX.X%) · N txns`**
Alternative: separate tooltip lines per field. Chosen approach uses a single line
per dataset for compactness — doughnut tooltips work better with one-line labels,
and bar chart tooltips rarely show multiple datasets.

**Assets/liabilities as dashed lines, not stacked areas**
Alternative: stacked area chart showing assets on top, liabilities subtracted below.
Dashed lines were chosen to avoid visual confusion with the filled net worth area and
to keep all three values legible at the same scale.

**Click navigation via `onClick` + `onHover` cursor**
Alternative: add "click to drill-down" text to chart title. The onClick/onHover
pattern is consistent with standard web UX and requires no layout change.

**Daily chart queries bypass the page `limit`**
The transactions page has a configurable row limit (default 100). The daily chart
queries all matching transactions (no LIMIT), using the same WHERE conditions as the
main query. This means the chart always reflects the full date range, not just
visible rows. The mismatch is intentional — the chart is a range overview, not a
per-row aggregate.

**Chart only renders when start+end are both set**
When no date range is specified, `txn_chart_json = "null"` and the chart block is
not rendered. This prevents a chart of unknown scope from appearing when the user
hasn't constrained the query.

## Coherence Assessment

The iterations compose well. Each one is independent and builds on the same pattern:
identify a chart that is missing interactivity or context, add it. No iteration
undid or contradicted another.

One mild redundancy: iterations 3 and 4 both add click navigation + cursor hover to
different charts using the same pattern. A human architect might have abstracted this
into a shared utility, but given Chart.js options are per-instance inline objects,
the duplication is minimal and the clarity benefit of keeping each chart
self-contained outweighs DRY concerns.

The net worth legend was enabled for the first time in iteration 2 — a small
side-effect that improves the chart but was not the stated goal of that iteration.
This is appropriate scope creep (required to make the new lines identifiable).

## What Was Improved

- Spending bar chart tooltip: shows `$X.XX (XX.X%) · N txns` instead of `$X.XX`
- Spending bar chart: bars are clickable drill-downs to transactions (category/merchant)
- Net worth chart: shows assets and liabilities as separate dashed lines; legend enabled
- Dashboard doughnut: tooltip shows `$X.XX (XX.X%)`; slices are clickable drill-downs
- Transactions page: gains a daily spending bar chart above the table when a date range is set

## What Was Not Addressed

- **Recurring chart**: no tooltip improvements or interactivity added (complex stacked structure with ghost/projected datasets makes this harder)
- **Accounts timeline chart**: transaction-count chart not enhanced with interactivity or richer tooltips
- **Month-over-month comparison**: no side-by-side current vs. prior month chart was added to spending
- **Trend lines**: no linear regression or moving average overlay was added to the net worth chart
- **Spending chart — account grouping click**: clicking account bars does not navigate (no natural transaction filter by account name)
