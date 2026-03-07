# Proposal: Explore mobile-ux

## Objective

Continue improving mobile UX and responsive design across the finance app, focusing on
the pages left unaddressed by the previous mobile-responsive loop: the transactions
table (6 columns), accounts table (8 columns), review queue (7-column table with
embedded forms), and recurring charges tables (8 columns across three sections).

## Motivation

The first mobile-responsive exploration loop (explore/mobile-responsive-2026-03-06)
addressed structural layout issues — stacking layouts, wrapping summary strips, and
reducing padding. However, the densest data tables remained unchanged: they relied
on `overflow-x-auto` to handle width, which forces horizontal scrolling on phones.

For pages like Transactions (visited frequently) and Review Queue (requires interaction
to approve items), horizontal scrolling is a friction point that makes the app
effectively unusable on mobile. Hiding non-essential columns at appropriate breakpoints
is a low-risk, high-impact improvement that preserves all data for larger screens.

## Scope

Files explored and modified:
- `finance/web/templates/transactions.html`
- `finance/web/templates/accounts.html`
- `finance/web/templates/review.html`
- `finance/web/templates/recurring.html`

Files in scope but not modified (no meaningful improvement needed):
- `finance/web/templates/index.html`
- `finance/web/templates/base.html`
- `finance/web/templates/_macros.html`

Focus area: Jinja2 HTML templates — specifically wide data tables on the transactions,
accounts, review, and recurring pages.

## Approach

This change was produced by an autonomous Ralph exploration loop — iterative,
open-ended improvement with no pre-defined implementation plan. The loop ran
for 4 iterations with commit-per-iteration discipline.
