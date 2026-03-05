## Context

The Recurring Charges page (`/recurring`) is a Jinja2 template backed by a single Flask route in `finance/web/app.py`. It already passes `attention`, `active`, `cancelled` lists and `spend_chart_json` to the template. All improvements are either template-side (HTML/Tailwind/JS) or minor Python additions to the route to pre-compute summary values — no new analysis functions or schema changes needed.

## Goals / Non-Goals

**Goals:**
- Surface a three-stat summary strip (monthly spend, annual spend, due-soon count) above the chart
- Group Active rows by inferred billing cadence with per-group subtotals
- Unify status display into colored pills used consistently across all sections
- Improve Attention row visibility via background tints (keep left border as a secondary cue)
- Make the Cancelled section header structurally identical to Attention/Active
- Add a current-month projected total label to the chart card header

**Non-Goals:**
- No new database queries or schema changes
- No changes to detection logic (`get_recurring`, `get_recurring_spend_timeline`)
- No new MCP tools or CLI commands
- No pagination, search, or sort controls on the recurring tables

## Decisions

**1. Compute summary stats in the route, not the template**
Template arithmetic is error-prone in Jinja2 (especially for cadence detection). Python is the right place to derive monthly_total, annual_total, and due_soon_count, and pass them as simple floats/ints to the template.

**2. Cadence grouping via `interval_days` threshold**
Items in `active` already carry `interval_days`. Classify: ≤10 → Weekly, ≤45 → Monthly, ≤100 → Quarterly, ≤400 → Annual, else → Other. Groups with no items are omitted. This avoids any new DB calls.

To normalize annual/quarterly costs to a monthly equivalent for subtotals: divide typical_amount by (interval_days / 30.44). Show the raw typical_amount per row but show $/mo subtotals in group footers.

**3. Status pills as a shared Jinja2 macro**
Replace the existing `status_cell` macro with one that always returns a styled `<span>` badge, using consistent color semantics:
- `past_due` → red pill
- `due_any_day` → blue pill
- `due_soon` → amber pill
- `upcoming` (≤7d) → amber-light pill
- `upcoming` (>7d, ≤30d) → gray pill
- `upcoming` (>30d) → muted gray pill
- `likely_cancelled` → red-muted pill

**4. Row background tints (Attention section)**
Apply `bg-red-50` to past_due rows, `bg-blue-50` to due_any_day rows, `bg-amber-50` to due_soon rows. Keep the left-border accent as a complementary cue — it aids colorblind accessibility.

**5. Harmonize Cancelled section**
Replace the `<details>/<summary>` pattern with the same `<div class="mb-4">` + header `<div>` pattern used by Attention/Active. Add a JS-toggled collapse (chevron button) to preserve the "collapsed by default" behavior without `<details>` semantics.

**6. Chart header projected total**
`spend_chart_json` already contains projected data. In the route, extract the sum of projected values for the current month from `timeline["merchants"]` and pass it as `chart_projected_total`. Render as a subtle label in the chart card header row.

## Risks / Trade-offs

- [Cadence bucket mislabeling] A 28-day cycle vs 31-day cycle both land in "Monthly" — acceptable since the bucket is an approximation for display purposes. → No mitigation needed.
- [JS collapse for Cancelled] Adds a small inline script. → Keep it minimal (3-5 lines, no library).
- [Monthly subtotal math] Dividing by interval_days/30.44 is an estimate. Annual subscriptions will show ~$/mo. → Label subtotals clearly as "~/mo" to signal approximation.
