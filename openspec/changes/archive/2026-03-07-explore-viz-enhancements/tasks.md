# Tasks: Explore viz-enhancements

All tasks below were completed by the Ralph exploration loop.

- [x] Add `counts` array to spending `chart_data_json` in `app.py` so the bar chart
      tooltip can show transaction count per group without a separate query
- [x] Enrich spending bar chart tooltip to show `$X.XX (XX.X%) · N txns` instead of
      bare dollar amount, using `total_spent` from template context and `raw.counts`
      from chart data
- [x] Compute daily `chart_assets` and `chart_liabilities` arrays in the
      `net_worth_page` route alongside the existing net worth values
- [x] Add assets (green dashed) and liabilities (red dashed) as two additional datasets
      to the net worth line chart; enable the chart legend
- [x] Add `onClick` and `onHover` (cursor pointer) to the spending bar chart so
      clicking a bar navigates to `/transactions` filtered by category or merchant
      for the current date range
- [x] Add `onClick`, `onHover` (cursor pointer), and formatted dollar+% tooltip to
      the dashboard doughnut chart so slices are interactive and informative
- [x] Add server-side daily spending query in `transactions_page` route that bypasses
      the row limit and returns daily expense totals as `txn_chart_json`
- [x] Render a compact daily spending bar chart (indigo) above the transactions table
      when a date range is set and matching expense data exists

## Loop Metadata

- Iterations: 5
- Branch: explore/viz-enhancements-2026-03-07
- Commits: 6 (1 setup + 5 iterations)
