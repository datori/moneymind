# Proposal: Explore info-density

## Objective

Increase information display richness and density across the finance dashboard.
Make every view show more useful context at a glance — better use of space,
richer data in table rows, smarter summary lines, subtle inline indicators
where data exists, and tighter visual layout without sacrificing readability.

## Motivation

The dashboard templates had several low-effort, high-value improvements available:
raw epoch timestamps were unreadable, dollar amounts lacked thousands separators,
category labels were plain text in places that already used badges elsewhere,
and several pages had no summary-level context visible before scrolling into tables.
The templates were functional but not information-dense — the data was there, it
just wasn't being surfaced well.

## Scope

Files explored and modified:

- `finance/web/templates/index.html` — Dashboard home page
- `finance/web/templates/transactions.html` — Transaction list
- `finance/web/templates/net_worth.html` — Net worth history chart
- `finance/web/templates/pipeline.html` — Pipeline state and run history
- `finance/web/templates/recurring.html` — Recurring charges tables
- `finance/web/templates/review.html` — Review queue
- `finance/web/templates/spending.html` — Spending breakdown
- `RALPH_PROMPT.md` — Loop prompt (overwritten from previous mobile-ux loop)

Focus area:

The Jinja2 HTML templates for the web dashboard — purely presentation layer,
no changes to backend Python or database queries.

## Approach

This change was produced by an autonomous Ralph exploration loop — iterative,
open-ended improvement with no pre-defined implementation plan. The loop ran
for 10 iterations with commit-per-iteration discipline.
