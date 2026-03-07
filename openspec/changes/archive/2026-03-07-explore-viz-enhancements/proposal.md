# Proposal: Explore viz-enhancements

## Objective

Enhance existing charts and add new visualizations across the finance dashboard.
The dashboard had charts on several pages (doughnut on index, bar on spending, line
on net worth, stacked bars on recurring and accounts), but they were mostly passive
displays with minimal interactivity and thin tooltips. The goal was to make charts
more informative and actionable.

## Motivation

Charts in the finance dashboard were decorative rather than functional — they showed
data but gave no additional context on hover, no way to navigate from a chart to the
underlying transactions, and no breakdown beyond a single aggregated metric. A user
looking at the spending doughnut on the dashboard couldn't click through to see what
made up a category. A user on the net worth page couldn't tell whether net worth
changes were driven by asset growth or debt paydown. The transactions page had no
visualization at all.

This exploration aimed to close those gaps with targeted, additive improvements.

## Scope

Files explored and modified:
- `finance/web/app.py`
- `finance/web/templates/index.html`
- `finance/web/templates/spending.html`
- `finance/web/templates/net_worth.html`
- `finance/web/templates/transactions.html`

Focus area:
Chart.js visualizations across the web dashboard — tooltip content, chart
interactivity, new datasets, and new chart instances.

## Approach

This change was produced by an autonomous Ralph exploration loop — iterative,
open-ended improvement with no pre-defined implementation plan. The loop ran
for 5 iterations with commit-per-iteration discipline.
