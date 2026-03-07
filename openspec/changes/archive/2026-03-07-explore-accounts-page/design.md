# Design: Explore accounts-page

## Overview

The loop made five focused, independent improvements to the `/accounts` page.
Each iteration identified one concrete gap — a feature already supported by
backend data but not surfaced in the UI, or a UX defect — and addressed it
cleanly. The changes compose naturally without conflict: they add new panels,
fix a rendering bug, and improve visual clarity in the existing table.

No changes were made to `finance/analysis/accounts.py` or `_macros.html` —
all required data was already available; only the route and template needed
updating.

## Iteration Progression

1. **Credit utilization panel** — The most impactful missing feature. `get_credit_utilization()`
   was already imported in `app.py` but never called. The loop wired it into the route and
   added a new panel between the summary bar and the timeline chart: aggregate utilization
   percentage with a color-coded progress bar (green <30%, amber 30-70%, red ≥70%), plus
   a responsive card grid for per-card breakdowns when multiple credit cards exist.

2. **Flash message rendering** — A clear bug: the route redirects to `/accounts?msg=...`
   after deletion, and `msg` is already in the template context, but the template never
   rendered it. A single green alert banner added at the top of the content block fixes this.

3. **Available credit sub-line** — `get_accounts()` fetches the `available` field from the
   balances table but it was never displayed. For credit accounts, showing available credit
   under the balance adds meaningful context without cluttering the layout. Shown as a small
   muted sub-line ("$X,XXX avail") only for credit-type accounts where available is not null.

4. **Account type badges** — The Type column rendered plain capitalized text. Replacing it
   with colored pill badges (blue=checking, emerald=savings, orange=credit, purple=investment)
   makes account types immediately scannable — consistent with the badge pattern used
   throughout the app (e.g., `category_badge` in `_macros.html`).

5. **Balance totals in summary bar** — The summary bar showed only count and date range.
   The loop added Assets (sum of positive balances), Liabilities (sum of absolute negative
   balances), and Net Worth (assets - liabilities) with color coding (emerald for positive,
   red for negative/deficit). These are computed in the route from `merged_accounts`.

## Design Decisions

**Credit utilization placement**: The panel is placed after the summary bar and before
the timeline chart. This priority ordering (financial health → historical volume) makes
more immediate sense than leading with the chart. Alternative: a collapsible section or
inline column; rejected as heavier UI for commonly-needed data.

**Aggregate utilization threshold colors**: 30%/70% breakpoints (green/amber/red) are
standard credit health thresholds. Applied consistently to both the aggregate bar and
per-card mini bars.

**Available credit gating**: Available is only shown for `type == 'credit'` accounts.
For checking/savings, `available` may equal `balance` and adds no signal.

**Balance totals computation**: Assets/liabilities computed from the sign of `balance`
in `merged_accounts`, not from account type. This is pragmatic — a positive balance on
any account is an asset regardless of type. The `asset_types` variable defined in the
route is unused (dead code from an earlier draft of the iteration); it could be cleaned up.

**Flash message style**: Emerald/green for deletion confirmation follows the pattern used
elsewhere in the app. Deletion is destructive but the message confirms it completed
successfully — a success state.

## Coherence Assessment

The five iterations compose cleanly with no contradictions or redundancies. Each targets
a distinct gap. The loop correctly avoided modifying anything already addressed by a
prior iteration.

Minor issue: the route now defines `asset_types = {"checking", "savings", "investment"}`
but never uses it — this was likely scaffolding from drafting the balance computation.
It's harmless but could be deleted.

The credit utilization panel has an edge case: if there is exactly one credit card with
no configured limit, the panel shows the card name and balance with "no limit set" but
no progress bar. This is correct behavior — utilization cannot be computed without a limit.

## What Was Improved

- Credit utilization is now visible on the accounts page (was silently missing)
- Deleting an account now shows a confirmation flash message (was broken)
- Available credit is shown for credit accounts under their balance
- Account types are visually scannable via colored badges
- The summary bar communicates total financial position (assets/liabilities/net)

## What Was Not Addressed

- The `asset_types` variable in the route is defined but unused — minor cleanup needed
- The timeline chart has no y-axis label or count tooltip for the single-account view
- No link from an account row to a filtered transactions view for that account
- The "last synced" relative time JS only uses minutes/hours/days — no "just now"
  granularity for sub-minute freshness (it does output "just now" but only at exactly 0 mins)
- No handling for accounts with null balance in the assets/liabilities totals beyond
  filtering them out (correct, but undocumented)
