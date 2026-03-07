### NEW Requirement: Spending bar chart — enriched tooltip

The spending bar chart on `GET /spending` SHALL display an enriched tooltip on
hover showing the dollar amount, percentage of total spending, and transaction count
for the hovered bar.

The `GET /spending` route SHALL include a `counts` array (one integer per group,
matching `labels` and `values` order) in `chart_data_json`. The template SHALL use
`total_spent` (injected from the server context) to compute the percentage.

Tooltip format: `$X,XXX.XX (XX.X%) · N txns` (or `· 1 txn` singular).

#### Scenario: Spending tooltip shows context
- **WHEN** the user hovers a bar on the spending chart
- **THEN** the tooltip shows the dollar amount, its percentage of the total, and the
  number of transactions in that group

---

### NEW Requirement: Spending bar chart — click navigation

The spending bar chart on `GET /spending` SHALL support click-to-drill-down
navigation. Clicking a bar navigates to `/transactions` pre-filtered for the
hovered group and the current date range, sorted by amount descending.

- When `group_by=category`: navigates to `/transactions?start={start}&end={end}&category={label}&sort_by=amount&sort_dir=desc`
- When `group_by=merchant`: navigates to `/transactions?start={start}&end={end}&search={label}&sort_by=amount&sort_dir=desc`
- When `group_by=account`: no navigation (no transactions filter by account name)

The chart canvas SHALL show a pointer cursor on hover when an element is active.

#### Scenario: Click category bar navigates to transactions
- **WHEN** the user clicks a bar on the spending chart with `group_by=category`
- **THEN** the browser navigates to `/transactions` filtered by that category and
  the current date range

#### Scenario: Click merchant bar navigates to transactions
- **WHEN** the user clicks a bar on the spending chart with `group_by=merchant`
- **THEN** the browser navigates to `/transactions` with a search filter for that
  merchant name

---

### UPDATED Requirement: Net worth history page

`GET /net-worth` SHALL display three lines on the chart: net worth (indigo, filled),
assets (green, dashed), and liabilities (red, dashed). All three are rendered from
data computed server-side in the route handler.

The route SHALL compute per-day assets (sum of positive balances in `running`) and
liabilities (absolute sum of negative balances in `running`) alongside net worth,
and include them as `assets` and `liabilities` arrays in `chart_data_json`.

The chart legend SHALL be displayed (position: top) to label the three lines.
Tooltip mode SHALL be `index` (all three values shown on hover). The assets and
liabilities lines SHALL have no point markers and use `borderDash: [4, 3]`.

Previously: a single "Net Worth" line with `legend: { display: false }`.

#### Scenario: Net worth chart renders three lines
- **WHEN** a browser navigates to `/net-worth` and balance history exists
- **THEN** the chart displays net worth (indigo filled), assets (green dashed), and
  liabilities (red dashed) with a legend at the top
- **THEN** hovering shows all three values for that date in the tooltip

---

### NEW Requirement: Dashboard doughnut — enriched tooltip and click navigation

The spending doughnut chart on `GET /` SHALL display an enriched tooltip and support
click-to-navigate behavior.

**Tooltip**: shows `$X,XXX.XX (XX.X%)` — dollar amount and percentage of the total
spending displayed, computed client-side from the sum of all values.

**Click navigation**: clicking a slice navigates to `/transactions?start={spending_start}&end={spending_end}&category={label}&sort_by=amount&sort_dir=desc`.
The chart canvas SHALL show a pointer cursor on hover when an element is active.

Previously: default Chart.js tooltip (category name + raw number); no click behavior.

#### Scenario: Dashboard doughnut tooltip shows dollar and percentage
- **WHEN** the user hovers a slice on the dashboard doughnut chart
- **THEN** the tooltip shows `$X,XXX.XX (XX.X%)` instead of the raw number

#### Scenario: Dashboard doughnut click navigates to filtered transactions
- **WHEN** the user clicks a doughnut slice on the dashboard
- **THEN** the browser navigates to `/transactions` filtered by that category for
  the current month's date range

---

### NEW Requirement: Transactions page — daily spending chart

`GET /transactions` SHALL render a compact daily spending bar chart above the
transactions table when a date range (`start` and `end`) is provided and matching
expense transactions exist.

The route SHALL query the daily expense totals (all transactions with `amount < 0`,
grouped by date, with the same category/search filters as the main query but without
the row limit) and pass the result as `txn_chart_json` to the template.

When `txn_chart_json` is non-null, the template SHALL render a Chart.js bar chart
(indigo, height 80px canvas) between the summary strip and the transactions table.
The chart uses compact y-axis labels (`$X.X k`) and limits x-axis tick count to 14.
No legend is displayed.

When no date range is set, or when no matching expense transactions exist,
`txn_chart_json` is the string `"null"` and no chart is rendered.

#### Scenario: Daily chart renders when date range is set
- **WHEN** a browser navigates to `/transactions?start=2026-03-01&end=2026-03-31`
  and expense transactions exist in that range
- **THEN** a compact bar chart appears above the table showing daily spending totals

#### Scenario: Daily chart reflects active filters
- **WHEN** the user filters by category on the transactions page
- **THEN** the daily chart shows spending for only that category, matching the table

#### Scenario: Daily chart absent without date range
- **WHEN** a browser navigates to `/transactions` with no start/end params
- **THEN** no chart is rendered above the table
