# Proposal: Explore mobile-responsive

## Objective

Improve mobile friendliness and responsive design throughout the app. The
navigation bar is already mobile-aware (hamburger menu, vertical dropdown), but
many pages have dense tables, side-by-side chart/table layouts with fixed
minimum widths, static grid columns, and large paddings that break or look poor
on small screens.

## Motivation

The app runs as a local web server accessed from any device on the network,
including phones. Several pages — particularly Spending, Recurring, and the
report detail view — had layout patterns that overflowed the viewport on narrow
screens, forcing awkward horizontal scrolling of full page content (not just
table content) or squeezing multi-stat summary bars into illegible single lines.
Addressing these with targeted Tailwind responsive class changes is low-risk and
high-value.

## Scope

Files explored and modified:
- `finance/web/templates/spending.html`
- `finance/web/templates/recurring.html`
- `finance/web/templates/report_detail.html`
- `finance/web/templates/index.html`

Files examined but not modified (already adequate or out of scope for this loop):
- `finance/web/templates/base.html`
- `finance/web/templates/transactions.html`
- `finance/web/templates/accounts.html`
- `finance/web/templates/pipeline.html`
- `finance/web/templates/review.html`
- `finance/web/templates/reports.html`
- `finance/web/templates/net_worth.html`
- `finance/web/templates/_macros.html`

Focus area: Jinja2/HTML templates only — layout and responsive classes, no
backend logic or route changes.

## Approach

This change was produced by an autonomous Ralph exploration loop — iterative,
open-ended improvement with no pre-defined implementation plan. The loop ran
for 5 iterations with commit-per-iteration discipline.
