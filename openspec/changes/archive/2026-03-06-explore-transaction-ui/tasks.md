# Tasks: Explore transaction-ui

All tasks below were completed by the Ralph exploration loop.

- [x] Remove dedicated Pending column from transaction table; fold pending status
      into an inline yellow dot indicator in the Date cell with title="Pending"
      tooltip for accessibility
- [x] Make active sort column visually distinct — changed active sort link from
      barely-perceptible `text-gray-700` to `text-indigo-600 font-semibold`,
      consistent with the app's indigo accent system

## Loop Metadata

- Iterations: 2 completed (3rd slot consumed by a ToolSearch hang during testing)
- Branch: explore/transaction-ui-2026-03-06
- Commits: 4 total (2 exploration + 1 setup + 1 meta/skill-fix)
- Files changed: `finance/web/templates/transactions.html`
