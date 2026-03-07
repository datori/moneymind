# Proposal: Explore accounts-page

## Objective

Improve the accounts page — better information density, UX polish, visual clarity,
and surface useful data that was already available but not displayed (credit
utilization, available balance, net worth snapshot, account type cues).

## Motivation

The accounts page (`/accounts`) had a solid foundation: a transaction timeline
chart, per-account table, and a global summary bar. However, several pieces of
high-value data were computed or available but never surfaced:

- `get_credit_utilization()` was imported and defined but never called in the route
- The `available` field (available credit) was fetched per account but never rendered
- The route passed a `msg` flash parameter after deletion, but the template never
  rendered it — users got no feedback after deleting an account
- The Type column showed plain unstyled text, making account types hard to scan
- The summary bar showed only counts and date range, not any balance totals

## Scope

Files explored and modified:
- `finance/web/templates/accounts.html`
- `finance/web/app.py` (accounts_page route)
- `finance/analysis/accounts.py` (read-only — no changes needed)
- `finance/web/templates/_macros.html` (read-only — no changes needed)

Focus area: The `/accounts` page — its route handler and HTML template.

## Approach

This change was produced by an autonomous Ralph exploration loop — iterative,
open-ended improvement with no pre-defined implementation plan. The loop ran
for 5 iterations with commit-per-iteration discipline.
