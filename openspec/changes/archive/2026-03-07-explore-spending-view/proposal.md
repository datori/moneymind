# Proposal: Explore spending-view

## Objective

Improve the `/spending` page — the breakdown chart and table showing expenses
grouped by category, merchant, or account. Focus on UX clarity, data density,
and visual quality without over-engineering.

## Motivation

The spending page was functional but sparse. Users had no at-a-glance summary
of total spending for the selected period, no sense of relative proportions in
the table, no confirmation of grand total at the bottom, and inconsistent
filter UX (some controls auto-submitted, the group selector did not). Adding
information density and fixing UX inconsistencies makes the page substantially
more useful with minimal added complexity.

## Scope

Files explored and modified:
- `finance/web/templates/spending.html`
- `finance/web/app.py`

Files explored but not modified:
- `finance/analysis/spending.py`
- `finance/web/templates/_macros.html`

Focus area:
The `/spending` route and its Jinja2 template — specifically the filter form,
the summary/stats section, the breakdown table, and the route-level data
computation in `spending_page()`.

## Approach

This change was produced by an autonomous Ralph exploration loop — iterative,
open-ended improvement with no pre-defined implementation plan. The loop ran
for 5 iterations with commit-per-iteration discipline.
