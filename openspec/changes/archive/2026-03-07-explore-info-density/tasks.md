# Tasks: Explore info-density

All tasks below were completed by the Ralph exploration loop.

- [x] Format pipeline run timestamps on dashboard as human-readable relative time
      ("3d ago", "just now") using a `js-rel-time` data attribute pattern and
      inline JavaScript formatter, replacing raw epoch millisecond display
- [x] Add category color badges to the dashboard spending table by importing the
      `category_badge` macro into `index.html` and applying it to the category column
- [x] Add a mini color-coded progress bar to the credit utilization column on the
      dashboard, showing each card's utilization visually (red > 30%, yellow > 20%,
      green otherwise) in addition to the existing percentage label
- [x] Add a summary strip to the transactions page showing transaction count, total
      spent, total income, and net, computed in the Jinja2 template using the
      `namespace()` accumulation pattern — no backend changes required
- [x] Add a summary strip to the net worth page showing current value, period-start
      value, and absolute + percentage change, populated client-side from the
      existing `chart_data_json` variable
- [x] Add category badges to the pipeline breakdown table and fix raw epoch
      timestamps in the pipeline page's own run history table (using the same
      `js-rel-time` pattern)
- [x] Apply thousands separators (`{:,.2f}`) to all dollar amounts on the
      dashboard: net worth total/assets/liabilities, credit utilization
      total balance and limit, and per-card balance and limit
- [x] Apply thousands separators to all amounts in the transactions table and
      summary strip
- [x] Apply thousands separators to all amounts on the recurring charges page:
      monthly/annual/projected totals in summary cards, typical amounts, total
      spent, and group subtotals in all three sections (Needs Attention, Active,
      Likely Cancelled)
- [x] Apply thousands separators to all amounts on the spending breakdown page
      (total spent, avg/day, per-row totals, footer total) and the review queue
      transaction amount column

## Loop Metadata

- Iterations: 10
- Branch: explore/info-density-2026-03-07
- Commits: 10 (plus 1 setup commit)
- Files changed: 7 (6 templates + RALPH_PROMPT.md)
