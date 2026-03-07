# Design: Explore info-density

## Overview

The loop made 10 focused improvements across 7 template files, all targeting
presentation-layer information density. Two broad themes emerged organically:
(1) contextual enrichment — adding summary strips, inline indicators, and visual
encoding to make each view show more at a glance; and (2) formatting consistency
— propagating thousands separators to all dollar amounts across the app.

The loop operated entirely in Jinja2 templates, requiring no changes to FastAPI
routes or backend Python. This was the right call — most data was already being
passed to templates, just not being displayed.

## Iteration Progression

**Iteration 1** targeted the most jarring UX failure first: raw epoch millisecond
timestamps in the pipeline run history table on the dashboard. A `js-rel-time`
data attribute pattern with an inline JavaScript formatter converts these to
human-friendly strings ("3d ago", "just now") at render time.

**Iteration 2** added category color badges to the dashboard's "Spending This Month"
table. The `category_badge` macro was already available and used on the transactions
page; this import was simply missing on `index.html`. A one-line import plus one
template expression change.

**Iteration 3** added a mini progress bar to the credit utilization column on the
dashboard. The utilization percentage already existed as a number and was already
color-coded (red/yellow/green). The loop added a `w-20` filled bar below the
percentage — directly using the existing color logic and Tailwind utility classes.

**Iteration 4** added a summary strip to the transactions page. The strip uses
Jinja2's `namespace()` trick to accumulate spent/income totals in a template loop,
then renders count, spent, income, and net in a compact pill bar above the table.
This required no backend changes.

**Iteration 5** added a summary strip to the net worth history page. Since the
net worth page only receives `chart_data_json` (not individual values), the
strip is populated client-side in JavaScript after the chart data is available:
it reads `raw.values[0]` (period start) and `raw.values[vals.length-1]` (current),
computes delta and percentage change, and renders inline HTML into a hidden div
that is then un-hidden.

**Iteration 6** applied the `js-rel-time` pattern to the pipeline page's own run
history table (separate from the dashboard widget), and added category badges to
the pipeline category breakdown table.

**Iterations 7–10** systematically propagated thousands separators (`{:,.2f}` and
`{:,.0f}`) across all templates: dashboard (7), transactions (8), recurring (9),
and spending + review (10). Prior to this, large amounts like "$12345.67" were
displayed without comma grouping, making them harder to parse at a glance.

## Design Decisions

**`js-rel-time` pattern instead of server-side formatting**

Timestamps are stored as epoch milliseconds. Server-side relative formatting
would require passing the current time to the template (or computing it in the
route handler). The JS approach is simpler and avoids stale rendering — the
relative label is computed at page load time in the user's browser, so "3m ago"
is accurate when the page renders, not when the server responded.

Alternative: format timestamps in the route handler using Python `datetime`. This
would work but requires touching `app.py` and hardcoding a timezone assumption.
The JS approach defers the relative formatting to the client, which is appropriate
for display-only labels.

**Template-side aggregation for transaction summary strip**

The transaction summary strip (total spent, income, net) is computed via
`{% set ns = namespace(spent=0.0, income=0.0) %}` accumulation in the Jinja2
template loop. This avoids any backend change.

Alternative: compute totals in the route handler and pass them as template
variables. This would be cleaner architecturally but would require touching
`app.py`. For a display-only aggregation of an already-loaded list, the
template approach was sufficient.

**Client-side net worth summary strip**

The net worth page only passes `chart_data_json` to the template; there are
no separate `current_value` or `start_value` template variables. Extracting
these from the chart data in JS (which already has access to `raw.values`)
was the minimal-change approach.

Alternative: pass `current_value`, `start_value`, and `delta_pct` from the
route handler. This would be cleaner and allow server-side formatting, but
requires a backend change.

**`{:,.2f}` vs `"%.2f"|format`**

The codebase used `"%.2f"|format(value)` in many places, which produces no
thousands separator. The `"{:,.2f}".format(value)` Python string format
produces commas. Both are valid Jinja2 expressions (Python string methods work
in Jinja2). The loop replaced all `%.2f` and `%.0f` patterns with the
comma-producing equivalents for financial amounts.

## Coherence Assessment

The iterations composed well. The first six were about adding new information
(summaries, badges, indicators). The last four were a systematic sweep of
formatting inconsistencies. This is a natural and coherent order — richer
data first, then consistent presentation.

No contradictions or redundancies were introduced. The `js-rel-time` pattern
was reused across both the dashboard and the pipeline page without duplication
(each page has its own inline script, which is the right approach given they
use different DOM scopes and the pipeline page already had a large inline script
block).

One minor imperfection: the dashboard index.html spending table amounts
(`row.total`) still use `"%.2f"|format` (not `{:,.2f}`) as of the final
commit — this was addressed on the spending.html page but the dashboard's
own spending table cell was not updated. This is a small oversight.

## What Was Improved

- Pipeline run timestamps throughout the app are now human-readable relative
  strings ("3d ago", "just now") instead of raw epoch milliseconds
- Category color badges appear on the dashboard spending table and the pipeline
  breakdown table, consistent with how they appear on transactions and spending pages
- Credit utilization column has a mini color-coded progress bar (red/yellow/green)
  alongside the percentage, matching the pattern already used on the spending page
- Transactions page shows a summary strip (count / spent / income / net) before
  the table, giving immediate context without scrolling
- Net worth page shows a summary strip (current, period start, delta + %) computed
  from the chart data client-side
- All dollar amounts across recurring, spending, review, transactions, and dashboard
  now use thousands-separator formatting (`$12,345.67` instead of `$12345.67`)

## What Was Not Addressed

- Dashboard spending table `row.total` still uses `"%.2f"|format` (minor oversight)
- No improvements to the accounts page (balances already used `{:,.2f}` for
  positive amounts per the existing template; negative branch was noted as a gap
  in the loop prompt but not fixed during the loop)
- No improvements to the reports page or report detail page
- The net worth summary strip relies on JS and won't render if JavaScript is
  disabled; a server-side fallback was not added
- No new data was surfaced that required backend changes — all improvements were
  display-layer only
