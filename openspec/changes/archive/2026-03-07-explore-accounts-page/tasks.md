# Tasks: Explore accounts-page

All tasks below were completed by the Ralph exploration loop.

- [x] Wire `get_credit_utilization()` into the `accounts_page` route and add a credit
      utilization panel to the template — aggregate % with color-coded progress bar,
      per-card grid with individual bars and utilization percentages
- [x] Fix flash message rendering — the `msg` template variable was passed by the route
      after account deletion but never rendered; added a green alert banner at the top
      of the accounts page content block
- [x] Show available credit as a sub-line under balance for credit-type accounts —
      surfaces the `available` field already fetched by `get_accounts()` but never displayed
- [x] Replace plain Type text with colored pill badges — checking (blue), savings (emerald),
      credit (orange), investment (purple) — consistent with badge pattern used elsewhere
- [x] Add assets, liabilities, and net worth totals to the summary bar — computed from
      merged_accounts balance signs; color-coded emerald (positive) / red (negative)

## Loop Metadata

- Iterations: 5
- Branch: explore/accounts-page-2026-03-07
- Commits: 5 (plus 1 setup commit)
