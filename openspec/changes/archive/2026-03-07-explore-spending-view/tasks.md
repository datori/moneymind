# Tasks: Explore spending-view

All tasks below were completed by the Ralph exploration loop.

- [x] Add summary strip above the chart showing total spent, transaction count, group count, and avg/day — route computes these from spending data and passes them to template
- [x] Add % of Total column to the breakdown table with percentage text and a mini indigo progress bar showing each row's proportion of total spending
- [x] Add `<tfoot>` totals row to the spending table displaying grand total amount, transaction count, and 100% — anchors the table with a confirmatory summary
- [x] Make the Group By select auto-submit on change (`onchange="this.form.submit()"`) for consistent instant filtering, matching the existing behavior of the include_financial checkbox and month navigation buttons
- [x] Add avg/day stat to the summary strip — route computes `days_in_range` from start/end ISO dates and divides total_spent; guarded with `max(1, ...)` for same-day ranges

## Loop Metadata

- Iterations: 5
- Branch: explore/spending-view-2026-03-06
- Commits: 6 (1 setup + 5 exploration)
