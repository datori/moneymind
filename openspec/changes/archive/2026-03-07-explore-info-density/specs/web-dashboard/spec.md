# Delta Spec: web-dashboard — info-density exploration

Changes from explore/info-density-2026-03-07.

---

### UPDATED Requirement: Dashboard home page — pipeline run timestamps

Pipeline run started-at timestamps in the "Recent Runs" widget SHALL be
rendered as human-readable relative strings (e.g. "3d ago", "2h ago",
"just now") using a `js-rel-time` CSS class pattern with a `data-ts` attribute
holding the raw epoch millisecond value. A small inline JavaScript block
converts these at page load time. The raw epoch value SHALL be preserved in
the `title` attribute for accessibility.

Previously: timestamps were displayed as raw epoch millisecond integers (e.g. "1741234567000").

#### Scenario: Pipeline run timestamp shows relative time on dashboard
- **WHEN** a browser navigates to `/` and there are recent pipeline runs
- **THEN** the Started column in the Recent Runs widget shows a relative string
  ("3d ago", "5h ago", "just now") rather than a raw epoch number
- **THEN** hovering the timestamp shows the raw epoch value in the title tooltip

---

### UPDATED Requirement: Dashboard home page — spending table category badges

The "Spending This Month" table on `GET /` SHALL render category labels as
color-coded pill badges using the `category_badge` Jinja2 macro (imported from
`_macros.html`), consistent with how categories are displayed on the transactions
and spending pages.

Previously: category labels in the dashboard spending table were plain text.

#### Scenario: Category badge rendered in dashboard spending table
- **WHEN** a browser navigates to `/`
- **THEN** the Spending This Month table shows each category as a colored pill
  badge, not plain text

---

### NEW Requirement: Dashboard home page — credit utilization progress bar

The credit utilization table on `GET /` SHALL display a mini horizontal
progress bar alongside each card's utilization percentage. The bar SHALL use
the same color coding as the percentage label: green (≤ 20%), yellow (20–30%),
red (> 30%). Bar width SHALL be capped at 100%. The bar is rendered as a
`w-20 bg-gray-100 rounded-full h-1.5` container with a colored `h-1.5
rounded-full` fill div, width set via inline `style="width: X%"`.

#### Scenario: Utilization bar renders alongside percentage
- **WHEN** a browser navigates to `/` and credit cards are configured
- **THEN** the Utilization column shows both the percentage label and a small
  horizontal bar below it, colored to match the utilization tier

---

### NEW Requirement: Transactions page — summary strip

`GET /transactions` SHALL render a summary strip between the filter form and
the data table when transactions are present. The strip SHALL display:
- Transaction count (e.g. "42 transactions")
- Total spent (sum of negative amounts, shown as positive with red color)
- Total income (sum of positive amounts, shown in green)
- Net (income + spent algebraically, colored green if ≥ 0, red if < 0)

Spent, income, and net sections SHALL be hidden on xs viewports (`hidden
sm:inline`) with dot separators between them. The totals are computed
in the Jinja2 template using the `namespace()` accumulation pattern.

#### Scenario: Summary strip shows totals for current filter
- **WHEN** a browser navigates to `/transactions` and transactions are present
- **THEN** a compact strip above the table shows the transaction count, total
  spent, total income, and net for the displayed transactions

#### Scenario: Summary strip absent when no transactions
- **WHEN** the selected filters return no transactions
- **THEN** the summary strip is not rendered (it is inside `{% if transactions %}`)

---

### NEW Requirement: Net worth history page — summary strip

`GET /net-worth` SHALL render a summary strip above the chart when chart data
is available. The strip SHALL display:
- **Current**: net worth value at the last data point
- **Period start**: net worth value at the first data point
- **Change**: absolute delta and percentage change from period start to current,
  colored green (positive) or red (negative), prefixed with + or -

The strip is populated client-side from the existing `chart_data_json` data
after the chart initializes. It is hidden by default and revealed once data
is confirmed non-empty. All dollar values use `toLocaleString('en-US',
{minimumFractionDigits: 2})` formatting.

#### Scenario: Summary strip shows current value and change
- **WHEN** a browser navigates to `/net-worth` and balance history exists
- **THEN** a strip above the chart shows current net worth, period-start value,
  and the delta with sign and percentage

#### Scenario: Summary strip absent when no data
- **WHEN** no balance history exists
- **THEN** the strip remains hidden and only the "No data" message appears

---

### UPDATED Requirement: /pipeline route — category breakdown badges

The category breakdown table in the "Current State" panel on `GET /pipeline`
SHALL render each category using the `category_badge` macro, consistent with
the transactions and dashboard pages.

Previously: category names in the pipeline breakdown were plain text.

#### Scenario: Category badges in pipeline breakdown
- **WHEN** a browser navigates to `/pipeline`
- **THEN** the Current State category list renders colored pill badges for
  each category, not plain text

---

### UPDATED Requirement: /pipeline route — run history timestamps

Pipeline run timestamps in the run history table on `GET /pipeline` SHALL
be rendered as human-readable relative strings using the same `js-rel-time`
pattern as the dashboard (see "Dashboard home page — pipeline run timestamps").

Previously: timestamps were displayed as raw epoch millisecond integers.

#### Scenario: Run history timestamps show relative time on pipeline page
- **WHEN** a browser navigates to `/pipeline`
- **THEN** the Started column in the run history table shows relative strings
  ("3d ago", "5h ago", etc.) rather than raw epoch numbers

---

### NEW Requirement: Thousands separator formatting for all dollar amounts

All dollar amount displays throughout the dashboard SHALL use Python's
`"{:,.2f}".format(value)` (or `"{:,.0f}".format(value)` for whole-dollar
displays) to produce comma-grouped values (e.g. `$12,345.67`).

This applies to all templates. The old `"%.2f"|format(value)` pattern,
which does not produce thousands separators, is deprecated for financial
display.

Affected pages and fields:
- **Dashboard** (`index.html`): net worth total, assets, liabilities; credit
  utilization total balance, total limit, per-card balance, per-card limit
- **Transactions** (`transactions.html`): per-row amounts; summary strip
  spent/income/net
- **Recurring** (`recurring.html`): monthly total, annual total, post-cancel
  monthly, chart projected total; per-row typical amount, total spent;
  group subtotals (header and footer)
- **Spending** (`spending.html`): total spent, avg/day, per-row amounts,
  footer total
- **Review queue** (`review.html`): per-row transaction amounts

#### Scenario: Large dollar amounts display with commas
- **WHEN** any dashboard page displays a dollar amount ≥ 1000
- **THEN** the amount is formatted with comma grouping (e.g. "$12,345.67")
  rather than without (e.g. "$12345.67")
