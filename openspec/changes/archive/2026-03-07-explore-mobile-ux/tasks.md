# Tasks: Explore mobile-ux

All tasks below were completed by the Ralph exploration loop.

- [x] Hide Description (sm), Merchant, and Account (md) columns in the transactions
      table so mobile shows Date, Category, Amount; sm adds Description; md+ shows all 6
- [x] Hide Institution, Type, Txns (sm), and Date Range, Last Synced (lg) in the
      accounts table so mobile shows Account Name, Balance, Actions; sm adds 3 more;
      lg adds the metadata columns
- [x] Hide Description, Merchant (md), and Reason (sm) in the review queue table so
      mobile shows Date, Amount, Category select, and Approve — enough to action items
      without breaking the multi-cell form structure
- [x] Hide Interval, Times Seen, and Total Spent (sm) in all three recurring tables
      (Needs Attention, Active Subscriptions, Likely Cancelled) via the shared
      table_header() macro and matching data cells in each section

## Loop Metadata

- Iterations: 4
- Branch: explore/mobile-ux-2026-03-06
- Commits: 5 (1 setup + 4 improvement)
- Files changed: 4 templates
