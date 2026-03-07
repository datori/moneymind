# Design: Explore transaction-ui

## Overview

The loop made two focused changes to `finance/web/templates/transactions.html`.
Both target visual clarity in the transaction table: one removes structural
noise (an empty column), the other improves affordance legibility (the sort
indicator). Neither change touches the filter bar, the macro library, or the
base template. The result is a marginally tighter, clearer table.

## Iteration Progression

**Iteration 1** targeted the Pending column — a dedicated `<th>` and `<td>` pair
that was empty for virtually every row. The loop chose to fold the pending flag
into the Date cell as a small yellow dot (`w-1.5 h-1.5 rounded-full bg-yellow-400`)
with a `title="Pending"` tooltip, then removed the column entirely. This reduced
the column count from 7 to 6 and eliminated persistent visual whitespace on the
right side of the table.

**Iteration 2** targeted the active sort indicator. Previously, the active sort
column's link applied `text-gray-700` — a barely perceptible change from the
thead's base `text-gray-500`. The loop replaced this with `text-indigo-600
font-semibold`, making the sorted column clearly distinguishable and consistent
with the app's indigo accent color used throughout navigation and buttons.

The two iterations are independent and additive — neither responds to or depends
on the other.

## Design Decisions

**Inline dot vs. text badge for pending:**
The original design used a text badge ("Pending" in yellow) inside a dedicated
column. The loop chose a minimal dot indicator rather than moving the text badge
inline. This keeps the Date cell compact and avoids adding text that competes
with the date itself. The `title` attribute preserves discoverability.

**Indigo for active sort vs. underline or background:**
The loop chose color + weight (`text-indigo-600 font-semibold`) rather than an
underline or background highlight. This is consistent with how the app uses
indigo elsewhere (nav active state, buttons) and doesn't require additional
layout space.

**Scope restraint:**
The loop did not touch `_macros.html` or `base.html` despite them being in scope.
This reflects good judgment — neither file had clear improvement opportunities
relative to the stated objective.

## Coherence Assessment

High coherence. Two iterations, two independent changes, no conflicts or
redundancies. Both changes are improvements in the same direction (reduce noise,
increase clarity). The loop was terminated early by a hook counter issue (a
ToolSearch hang consumed the third iteration slot), so the coherence assessment
benefits from the fact that it never had a chance to overreach.

## What Was Improved

- Removed a dedicated Pending column that was empty ~99% of the time; pending
  status is now a compact inline indicator in the Date cell
- Active sort column is now visually distinct (indigo, bold) rather than
  imperceptibly darker gray

## What Was Not Addressed

- Amount formatting: `{% if txn.amount < 0 %}-{% endif %}${{ ... }}` is verbose
  template logic; a macro or filter could clean this up
- Count line: "Showing N transaction(s)." uses the awkward `(s)` pattern
- Empty state: plain gray text paragraph with no visual treatment
- Filter bar: no changes to layout, label alignment, or mobile behavior
- `_macros.html`: category badge macro is a long if/elif chain; could be a dict
  lookup; not addressed
