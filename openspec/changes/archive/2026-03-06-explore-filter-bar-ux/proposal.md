# Proposal: Explore filter-bar-ux

## Objective

Improve the transactions filter bar layout, label clarity, and mobile usability.
The bar uses a flat flex-wrap layout that can crowd or misalign on narrow viewports.
Target improvements: grouping related controls, responsive behavior, visual
de-emphasis of low-priority fields, a clear/reset affordance, and fixing the
awkward "transaction(s)" count phrasing.

## Motivation

The filter bar on `/transactions` had two small but persistent UX warts:
no way to reset all filters without manually clearing each field individually,
and an awkward `(s)` suffix on the result count. Both are friction points with
low implementation cost and clear fixes. The broader responsive/grouping
improvements were identified as candidates but not reached due to the loop
running only 2 iterations.

## Scope

Files explored and modified:
- `finance/web/templates/transactions.html`

Also modified (meta, not UI):
- `.claude/skills/ralph-explore/SKILL.md` — off-by-one fix in max_iterations docs
- `RALPH_PROMPT.md` — updated for this exploration objective

Focus area:
The filter form (lines 9–60 of transactions.html) — controls, layout, and the
result count line below the table.

## Approach

This change was produced by an autonomous Ralph exploration loop — iterative,
open-ended improvement with no pre-defined implementation plan. The loop ran
for 2 iterations with commit-per-iteration discipline. A third iteration was
intended but did not run due to a `max_iterations` off-by-one in the state file
(fixed in the meta commit on this branch).
