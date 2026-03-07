# Design: Explore spending-view

## Overview

The loop added four concrete improvements to the `/spending` page across five
commits. The first three iterations layered information onto the template in
a coherent stack — summary strip, proportion column, totals footer — each
building on the same `total_spent` and `total_count` values. The fourth
addressed a UX inconsistency that the earlier iterations made more visible.
The fifth extended the summary strip with an additional stat that required a
small backend change.

The changes compose cleanly. No iteration reversed or conflicted with another.

## Iteration Progression

1. **Summary strip** — The most glaring gap: users had no total. The route
   now computes `total_spent` and `total_count` and the template renders them
   as a compact stat bar above the chart. Group count also added for context.

2. **% of Total column** — With `total_spent` already in context, adding a
   proportional breakdown required only template changes. A mini progress bar
   (Tailwind `h-1.5 rounded-full bg-indigo-400`) renders alongside the
   percentage text, making relative size visible without reading the chart.

3. **Totals footer row** — A `<tfoot>` row anchors the table with a grand
   total. This is standard in financial tables and redundantly confirms the
   summary strip values in context with the data.

4. **Auto-submit on group change** — A single `onchange="this.form.submit()"`
   attribute on the `group_by` select. Fixes an inconsistency that existed
   from the start: the `include_financial` checkbox and the month buttons both
   triggered immediately, but changing the group required pressing Apply.

5. **Avg/day stat** — Added to the summary strip. The route computes
   `days_in_range` from the ISO date strings (using `date.fromisoformat`) and
   divides `total_spent` by it (guarded against zero days). This gives
   spending velocity — useful for gauging whether the current month's pace
   is unusual.

## Design Decisions

**Summary strip as a separate card, not inline with the form**
The strip sits between the filter form and the chart/table flex row. This
makes it visible regardless of whether the user focuses on the chart or the
table. The alternative (embedding stats in the filter card) would have crowded
the form.

**% bar width capped at pct value with no clipping guard**
The progress bar width uses `style="width: {{ pct }}%"` directly. Since data
is sorted by total descending and all `pct` values sum to 100, no individual
row can exceed 100%, so no explicit cap is needed.

**tfoot rather than a final tbody row**
Using `<tfoot>` is semantically correct for a totals row and positions it at
the bottom of the table in all layouts. The `border-t-2` on the tfoot visually
separates it from data rows.

**avg_per_day computed server-side, not in template**
Jinja2 can do the math but date parsing in templates is awkward. Computing
`days_in_range` in Python using `date.fromisoformat` is cleaner and consistent
with how the route already builds the date range. `max(1, ...)` guards against
a zero-day range (same-day start/end).

## Coherence Assessment

All five iterations compose well. They form a progressive enhancement of the
same two surfaces (template and route) without stepping on each other. The
order was sensible: establish totals first (needed by later iterations),
then use them for proportions, then anchor the table, then fix interaction
consistency, then extend the stats.

The loop stopped cleanly at 5 — it output the stop signal rather than
padding with a weak change.

No redundancies or contradictions. The `total_spent` computed for the summary
strip is reused in the tfoot row and in the % column — no duplication.

## What Was Improved

- Users can see total spending for the selected period at a glance
- Relative proportions of each category/merchant/account are visible in the table
- Grand total is anchored in the table footer (standard financial table UX)
- Group by dropdown now auto-submits, consistent with checkbox and month buttons
- Avg/day stat adds spending velocity to the summary strip

## What Was Not Addressed

- The chart color palette is still arbitrary HSL — could align with the
  indigo/teal/amber app palette
- Chart tooltip still recomputes the axis direction inside the callback
  (minor code duplication: `raw.labels.length > 8` appears twice)
- No "account" drill-down link in the table (by design — account rows have
  no obvious filter target)
- The summary strip doesn't handle overflow gracefully on very narrow
  viewports (wraps awkwardly at <480px)
- No comparison to prior period (e.g., "vs. last month")
