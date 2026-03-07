## ADDED Requirements

### Requirement: Dashboard web server starts
The system SHALL provide a `finance-dashboard` entry point that starts a web server. The default host SHALL be `0.0.0.0` (all interfaces) so the server is reachable from devices on the local network without requiring an explicit flag. The `--host` flag SHALL still be accepted for explicit override.

#### Scenario: Server starts on default host binding to all interfaces
- **WHEN** `uv run finance-dashboard` is executed without a `--host` flag
- **THEN** a web server starts bound to `0.0.0.0:8080` and is accessible from other devices on the local network

#### Scenario: Custom port and host
- **WHEN** `uv run finance-dashboard --port 9090 --host 127.0.0.1` is executed
- **THEN** the server starts on the specified host and port

---

### Requirement: Dashboard home page
The `GET /` route SHALL display a summary dashboard with net worth, spending, and utilization.

#### Scenario: Home page loads
- **WHEN** a browser navigates to `/`
- **THEN** the page displays: current net worth, spending summary for current month (by category), credit utilization for all configured cards

---

### Requirement: Accounts page
The `GET /accounts` route SHALL display a unified page with a global summary bar at the top and a single rich per-account table. The route calls `get_data_overview(conn)` to populate both the summary bar and per-account columns.

#### Scenario: Unified accounts page loads
- **WHEN** a browser navigates to `/accounts`
- **THEN** the page displays a global summary bar reading "X accounts · Y transactions · YYYY-MM-DD – YYYY-MM-DD · Assets $X · Liabilities $Y · Net $Z" followed by a single table with columns: Account Name, Institution, Type, Balance, Txn Count, Date Range, Last Synced, Actions

#### Scenario: Accounts with no transactions shown in unified table
- **WHEN** an active account has zero stored transactions
- **THEN** its row shows "0" for Txn Count, "—" for Date Range, and "Never" (or "—") for Last Synced

#### Scenario: Balance column shows value or dash
- **WHEN** an account has a current balance recorded
- **THEN** the Balance column shows "$X.XX" (negative balances in red); when no balance is recorded it shows "—"

---

### Requirement: Accounts page — credit utilization panel

The `GET /accounts` route SHALL call `get_credit_utilization(conn)` and pass the
result as `credit_util` to the `accounts.html` template.

When `credit_util.cards` is non-empty, the template SHALL render a "Credit Utilization"
panel between the global summary bar and the transaction timeline chart.

The panel SHALL include:
- A header "Credit Utilization" with the aggregate dollar amounts ($X used of $Y)
  and aggregate utilization percentage when `aggregate_pct` is not None
- A full-width progress bar colored by utilization: green (<30%), amber (30–70%), red (≥70%)
- When more than one credit card exists: a responsive grid of per-card tiles, each
  showing card name, balance, limit (if configured), utilization percentage, and a
  mini progress bar; cards without a configured limit show "no limit set"

#### Scenario: Credit utilization panel renders when cards exist
- **WHEN** at least one active credit account exists
- **THEN** the accounts page renders a "Credit Utilization" panel above the timeline chart

#### Scenario: Aggregate progress bar color reflects utilization
- **WHEN** aggregate utilization is below 30%
- **THEN** the progress bar is green
- **WHEN** aggregate utilization is between 30% and 70%
- **THEN** the progress bar is amber
- **WHEN** aggregate utilization is 70% or above
- **THEN** the progress bar is red

#### Scenario: Per-card grid shown for multiple cards
- **WHEN** two or more credit accounts exist
- **THEN** a grid of per-card tiles is rendered below the aggregate bar

#### Scenario: Panel hidden when no credit accounts
- **WHEN** no active credit accounts exist
- **THEN** the credit utilization panel is not rendered

---

### Requirement: Accounts page — balance totals in summary bar

The global summary bar on `GET /accounts` SHALL include total assets (sum of positive
balances), total liabilities (sum of absolute values of negative balances), and net
worth (assets − liabilities).

These values SHALL be computed in the route handler from `merged_accounts` and passed
as `total_assets`, `total_liabilities`, and `net_worth` to the template.

Assets and a positive net worth SHALL be styled emerald; liabilities and a negative
net worth SHALL be styled red. A negative net worth SHALL append the word "deficit".

#### Scenario: Summary bar shows balance totals
- **WHEN** a browser navigates to `/accounts`
- **THEN** the summary bar shows "Assets $X · Liabilities $Y · Net $Z" in addition
  to the account count, transaction count, and date range

#### Scenario: Negative net worth shown with deficit label
- **WHEN** total liabilities exceed total assets
- **THEN** the net amount is rendered in red with the word "deficit" appended

---

### Requirement: Accounts table — account type badges

The Type column in the accounts table on `GET /accounts` SHALL render colored pill
badges rather than plain text.

Badge colors by type:
- checking → blue (bg-blue-100 text-blue-700)
- savings → emerald (bg-emerald-100 text-emerald-700)
- credit → orange (bg-orange-100 text-orange-700)
- investment → purple (bg-purple-100 text-purple-700)
- unknown type → gray, capitalized
- null type → em dash

#### Scenario: Account type rendered as colored badge
- **WHEN** the accounts table renders a checking account
- **THEN** the Type column shows a blue pill badge labeled "Checking"

---

### Requirement: Accounts table — available credit sub-line

For accounts with `type == 'credit'` and a non-null `available` field, the Balance
column SHALL display the available credit as a small muted sub-line below the balance
(format: "$X,XXX avail").

#### Scenario: Available credit shown for credit accounts
- **WHEN** a credit account has a non-null `available` value
- **THEN** the Balance cell shows the balance on the first line and "$X,XXX avail"
  in small muted text below it

#### Scenario: Available credit not shown for non-credit accounts
- **WHEN** a checking or savings account has a non-null `available` value
- **THEN** the available sub-line is NOT rendered in the Balance cell

---

### Requirement: Transactions page
The `GET /transactions` route SHALL display a filterable transaction list. The category column SHALL render each category value as a color-coded pill badge using the `category_badge` Jinja2 macro (see `category-color-badges` spec). All other columns and filter behaviors are unchanged.

#### Scenario: Transactions page loads with defaults
- **WHEN** a browser navigates to `/transactions`
- **THEN** the last 30 days of transactions are shown (up to 100)

#### Scenario: Date range filter applied
- **WHEN** the user sets start/end date fields and submits the filter form
- **THEN** the page reloads showing only transactions in that range

#### Scenario: Category column shows colored badge
- **WHEN** a transaction with a known category is displayed
- **THEN** the category cell renders a color-coded pill badge instead of plain text

---

### Requirement: Net worth history page
The `GET /net-worth` route SHALL display a time-series chart of net worth.

#### Scenario: Net worth chart renders
- **WHEN** a browser navigates to `/net-worth`
- **THEN** a Chart.js line chart is displayed showing net worth over time (one data point per sync date)

---

### Requirement: Spending breakdown page
The `GET /spending` route SHALL display a spending breakdown chart with period selector and month navigation. When `group_by=category`, the label column in the breakdown table SHALL render each category as a color-coded pill badge using the `category_badge` macro. For `group_by=merchant` and `group_by=account`, labels render as plain text.

When `group_by=category`, each row in the spending breakdown table SHALL be a clickable link navigating to `/transactions` pre-filtered by that category and the current date range, sorted by amount descending. The link URL SHALL be: `/transactions?start={start}&end={end}&category={label}&sort_by=amount&sort_dir=desc`.

When `group_by=merchant`, each row SHALL link to `/transactions?start={start}&end={end}&search={label}&sort_by=amount&sort_dir=desc`. When `group_by=account`, no drill-down link is added.

The filter bar SHALL include prev/next month navigation buttons (‹ and ›) and a month label between them, as specified in the `month-navigation` capability.

#### Scenario: Spending chart renders (current month default)
- **WHEN** a browser navigates to `/spending`
- **THEN** a Chart.js bar chart shows spending by category for the current month

#### Scenario: Period filter applied
- **WHEN** the user selects a different month/period and submits
- **THEN** the chart updates to show spending for the selected period

#### Scenario: Category badges in spending table
- **WHEN** the spending page is viewed with `group_by=category`
- **THEN** each label in the breakdown table renders as a colored pill badge

#### Scenario: Category row links to transactions drill-down
- **WHEN** the spending page shows `group_by=category` and the user clicks the "Food & Dining" row
- **THEN** the browser navigates to `/transactions?start={start}&end={end}&category=Food+%26+Dining&sort_by=amount&sort_dir=desc` showing that category's transactions sorted largest-first

#### Scenario: Merchant row links to transaction search
- **WHEN** the spending page shows `group_by=merchant` and the user clicks a merchant row
- **THEN** the browser navigates to `/transactions?start={start}&end={end}&search={merchant_name}&sort_by=amount&sort_dir=desc`

#### Scenario: Month prev/next navigation on spending page
- **WHEN** the spending page is showing February 2026 and the user clicks ‹
- **THEN** the page reloads for January 2026 with all other filter params (group_by, include_financial) preserved

---

### Requirement: Sync now button
The dashboard SHALL include a "Sync Now" button that triggers a SimpleFIN sync.

#### Scenario: Sync triggered from dashboard
- **WHEN** the user clicks "Sync Now" on any dashboard page
- **THEN** a `POST /sync` request is made, sync runs, and the user is redirected back to the same page

#### Scenario: Sync error displayed
- **WHEN** the sync fails (e.g. network error)
- **THEN** an error message is displayed on the redirected page

---

### Requirement: /data redirects to /accounts
`GET /data` SHALL return HTTP 301 to `/accounts`. The separate data coverage page is subsumed by the unified accounts page.

#### Scenario: /data redirect
- **WHEN** a browser or HTTP client issues `GET /data`
- **THEN** the response is HTTP 301 with `Location: /accounts`

---

### Requirement: Nav "Data" link removed
The navigation bar SHALL NOT contain a "Data" link. The "Accounts" link SHALL remain and point to `/accounts`.

#### Scenario: Nav does not show Data link
- **WHEN** any page in the dashboard is loaded
- **THEN** the navigation bar shows: Dashboard, Accounts, Transactions, Net Worth, Spending, Pipeline, Review, Recurring — with no "Data" entry

---

### Requirement: Spending page include_financial toggle
`GET /spending` SHALL accept an `include_financial` query parameter (value `"1"` = include, absent or `"0"` = exclude). When absent or `"0"`, transactions in categories Financial, Income, and Investment are excluded from the spending query. The page SHALL render a visible "Include Financial Activity" checkbox that reflects the current state and resubmits the form when changed.

#### Scenario: Default spending excludes financial categories
- **WHEN** a browser navigates to `/spending` with no `include_financial` param
- **THEN** the spending results exclude Financial, Income, and Investment; the checkbox is unchecked

#### Scenario: include_financial=1 includes all categories
- **WHEN** a browser navigates to `/spending?include_financial=1`
- **THEN** the spending results include all categories; the checkbox is checked

#### Scenario: Toggle state preserved in form submission
- **WHEN** the user selects a date range and checks "Include Financial Activity" and clicks Apply
- **THEN** the resulting URL contains both the date params and `include_financial=1`

---

### Requirement: Spending breakdown page — summary strip
`GET /spending` SHALL render a summary strip between the filter form and the
chart/table area when spending data exists. The strip SHALL display:
- **Total spent**: sum of all spending rows for the selected period (formatted as `$X.XX`)
- **Transactions**: total transaction count across all groups
- **{Group}s**: count of distinct groups (categories/merchants/accounts) returned
- **Avg/day**: total spent divided by the number of days in the selected range, formatted as `$X.XX`

The route SHALL compute `total_spent`, `total_count`, `avg_per_day`, and pass
them to the template. `avg_per_day` SHALL use `max(1, days)` to avoid
division by zero on same-day ranges.

#### Scenario: Summary strip shows totals for current month
- **WHEN** a browser navigates to `/spending` with the default current-month range
- **THEN** the summary strip is visible above the chart, displaying total spent, transaction count, group count, and avg/day

#### Scenario: Summary strip absent when no data
- **WHEN** the selected period has no spending data
- **THEN** the summary strip is not rendered (it is inside `{% if spending %}`)

---

### Requirement: Spending breakdown table — % of Total column
The spending breakdown table SHALL include a fourth column "% of Total"
for each data row. The column SHALL display:
- A percentage value (1 decimal place, e.g. "42.3%")
- A mini horizontal progress bar (indigo, `h-1.5 rounded-full`) showing the
  proportion visually, with width set to the percentage value

The percentage is computed as `row.total / total_spent * 100` in the template.

#### Scenario: % column shows proportions
- **WHEN** the spending page renders with category data
- **THEN** each row shows its percentage of total spending and a corresponding mini bar

---

### Requirement: Spending breakdown table — totals footer row
The spending breakdown table SHALL include a `<tfoot>` row below all data rows
showing: "Total" label | grand total amount | total transaction count | "100%".
The footer row SHALL use a visually distinct top border (`border-t-2`) and
semi-bold font.

#### Scenario: Footer row shows grand total
- **WHEN** the spending page renders with data
- **THEN** the table footer row shows the sum of all amounts and the total transaction count

---

### Requirement: Spending page — group_by auto-submit
The "Group by" `<select>` element on the `/spending` page SHALL include
`onchange="this.form.submit()"` so that changing the selected group triggers
an immediate form submission, consistent with the behavior of the
"Include Financial Activity" checkbox.

#### Scenario: Group by change triggers immediate reload
- **WHEN** the user selects a different value in the "Group by" dropdown
- **THEN** the form submits immediately without requiring the user to click Apply

---

### Requirement: get_spending_summary accepts exclude_categories parameter
`get_spending_summary()` in `finance/analysis/spending.py` SHALL accept an optional `exclude_categories` parameter (list of str, default `None`). When provided and non-empty, the SQL query SHALL add a `WHERE t.category NOT IN (...)` clause to exclude those categories.

#### Scenario: exclude_categories filters spending query
- **WHEN** `get_spending_summary(conn, start, end, exclude_categories=['Financial', 'Income', 'Investment'])` is called
- **THEN** the returned list contains no rows with label "Financial", "Income", or "Investment"

#### Scenario: exclude_categories=None includes all categories (backward compat)
- **WHEN** `get_spending_summary(conn, start, end)` is called with no `exclude_categories` argument
- **THEN** all categories are included, matching prior behavior

---

### Requirement: Dashboard index — "Recent Runs" widget

The `GET /` route SHALL pass a `recent_runs` list to the `index.html` template. The list SHALL contain the 5 most recent rows from `run_log`, ordered by `started_at DESC`. `index.html` SHALL render a "Recent Runs" section showing the runs with columns: Run ID, Type, Started, Duration, Status. Status SHALL be color-coded: green for `success`, yellow for `running`, red for `error`. If no runs exist, the section SHALL display "No pipeline runs yet."

#### Scenario: Dashboard loads with no prior runs
- **WHEN** a browser navigates to `/` and `run_log` is empty
- **THEN** the "Recent Runs" section renders with the message "No pipeline runs yet."

#### Scenario: Dashboard loads with recent runs
- **WHEN** `run_log` contains one or more rows
- **THEN** the "Recent Runs" widget shows up to 5 most recent runs with their status, start time, and duration

#### Scenario: Running pipeline appears in widget
- **WHEN** a pipeline run is in progress (`status = 'running'`)
- **THEN** the dashboard shows that run with a yellow "running" status and no duration (since `finished_at` is NULL)

---

### Requirement: /pipeline route — run history page

The application SHALL expose a `GET /pipeline` route that renders `finance/web/templates/pipeline.html`. The route SHALL query `run_log` for all runs (most recent first, limit 50) and join with `run_steps` to provide per-run aggregate token usage. The route SHALL also query the current transaction state (total count, uncategorized count, recurring count, review queue count, and category distribution) from the transactions table to populate a "Current State" panel. The template SHALL display:

- A "Current State" panel at the top showing: total transactions, uncategorized count, recurring count, review queue depth, and top categories by transaction count.
- A "Run Pipeline" button below the Current State panel.
- A streaming progress panel (hidden by default) that becomes visible when the button is clicked.
- A run history table with columns: Run ID, Type, Started, Duration, Status, Txns, Tokens, Error.

#### Scenario: Pipeline page loads with current state
- **WHEN** a browser navigates to `/pipeline`
- **THEN** the "Current State" panel shows counts for: total transactions, uncategorized, recurring, needs_review; and a list of top categories with their counts
- **THEN** the run history table and "Run Pipeline" button are visible

#### Scenario: Current state reflects zero uncategorized
- **WHEN** all transactions have been categorized
- **THEN** the "Current State" panel shows uncategorized count as 0

#### Scenario: Run history Txns and Tokens columns
- **WHEN** a completed run has a non-null `summary` in `run_log`
- **THEN** the run history row shows `summary.transactions_enriched` in the Txns column and the sum of `tokens_in + tokens_out` from `summary` in the Tokens column

#### Scenario: Run history row with null summary
- **WHEN** a run has no `summary` (failed early or pre-analytics)
- **THEN** the Txns and Tokens cells show "—"

---

### Requirement: /pipeline route — streaming progress panel per-batch categories

The streaming progress panel in `pipeline.html` SHALL display per-batch category breakdowns in addition to token counts. When a `step_done` event arrives for an `enrich-batch` step, the step row SHALL expand to show the top categories assigned in that batch (from `response_summary.categories_assigned`), rendered as compact pill badges.

#### Scenario: Completed batch shows category pills
- **WHEN** an enrich-batch `step_done` event arrives with a `response_summary` containing `categories_assigned`
- **THEN** the step row shows the top 5 categories (by count) as small pills alongside the token count
- **THEN** categories with count > 1 show the count next to the category name (e.g., "Dining ×3")

#### Scenario: Batch with empty categories_assigned
- **WHEN** `response_summary.categories_assigned` is empty
- **THEN** no category pills are rendered for that batch row

---

### Requirement: Mobile-responsive navigation
The navigation bar in `base.html` SHALL be usable on screens as narrow as 390px. On viewports narrower than `md` (768px), the navigation links SHALL be hidden by default and toggled by a hamburger button. On `md` and wider viewports, the navigation SHALL display as a standard horizontal bar with no behaviour change.

#### Scenario: Nav on desktop viewport
- **WHEN** a page is loaded on a viewport 768px wide or wider
- **THEN** all navigation links are visible in a single horizontal row alongside the Sync Now button

#### Scenario: Nav on mobile viewport — links hidden by default
- **WHEN** a page is loaded on a viewport narrower than 768px
- **THEN** the navigation links are hidden and a hamburger icon button is visible

#### Scenario: Nav on mobile viewport — links revealed
- **WHEN** the user taps the hamburger button on a narrow viewport
- **THEN** the navigation links appear in a vertical dropdown panel, each link is tappable, and the sync button is accessible

#### Scenario: Nav link closes mobile menu on navigation
- **WHEN** the user taps a navigation link in the open mobile menu
- **THEN** the browser navigates to that page (the menu closes naturally on page load)

---

### Requirement: Wide tables scroll horizontally on narrow viewports
All data tables in the dashboard SHALL be wrapped in an `overflow-x-auto` container.
Key tables (transactions, accounts, review queue, recurring) SHALL additionally hide
non-essential columns at small breakpoints using Tailwind responsive `hidden {bp}:table-cell`
utilities, so that the most actionable columns remain visible without horizontal scrolling.
All hidden columns become visible on larger viewports.

**Column visibility by page:**

**Transactions table** (`/transactions`):
- xs (< 640px): Date, Category, Amount
- sm (≥ 640px): + Description
- md (≥ 768px): + Merchant, Account (all 6 columns)

**Accounts table** (`/accounts`):
- xs (< 640px): Account Name, Balance, Actions
- sm (≥ 640px): + Institution, Type, Txns
- lg (≥ 1024px): + Date Range, Last Synced (all 8 columns)

**Review queue table** (`/review`):
- xs (< 640px): Date, Amount, Category (select), Action (Approve)
- sm (≥ 640px): + Reason
- md (≥ 768px): + Description, Merchant (all 7 columns)

**Recurring tables** (`/recurring` — Needs Attention, Active, Likely Cancelled):
- xs (< 640px): Merchant, Typical, Next Due, Status, Cancel
- sm (≥ 640px): + Interval, Times Seen, Total Spent (all 8 columns)

**All other tables** (pipeline, spending, dashboard) remain full-width with
`overflow-x-auto` scroll only.

#### Scenario: Transaction table on mobile (xs)
- **WHEN** the `/transactions` page is viewed on a viewport narrower than 640px
- **THEN** the table shows 3 columns: Date, Category, Amount; Description, Merchant,
  and Account columns are hidden

#### Scenario: Transaction table on sm viewport
- **WHEN** the `/transactions` page is viewed on a viewport between 640px and 767px
- **THEN** Description is visible; Merchant and Account remain hidden

#### Scenario: Transaction table on md+ viewport
- **WHEN** the `/transactions` page is viewed on a viewport 768px or wider
- **THEN** all 6 columns (Date, Description, Merchant, Category, Account, Amount)
  are visible

#### Scenario: Accounts table on mobile
- **WHEN** the `/accounts` page is viewed on a viewport narrower than 640px
- **THEN** the table shows: Account Name, Balance, Actions; all other columns hidden

#### Scenario: Review queue on mobile
- **WHEN** the `/review` page is viewed on a viewport narrower than 640px
- **THEN** the table shows Date, Amount, Category select, and Approve button;
  the form remains fully functional to approve transactions

#### Scenario: Recurring tables on mobile
- **WHEN** `/recurring` is viewed on a viewport narrower than 640px
- **THEN** each recurring table shows Merchant, Typical, Next Due, Status, Cancel;
  Interval, Times Seen, and Total Spent are hidden

#### Scenario: Pipeline run history table on mobile
- **WHEN** the `/pipeline` page is viewed on a narrow viewport
- **THEN** the full run history table is accessible via horizontal scroll (no column hiding)

---

### Requirement: Spending chart is responsive
The spending doughnut chart on the dashboard home page (`GET /`) SHALL scale with its container. The chart container SHALL NOT have a fixed inline `width` style. The Chart.js configuration SHALL use `responsive: true` so the chart redraws to fill available space when the viewport changes.

#### Scenario: Chart renders at full container width on desktop
- **WHEN** the dashboard home page is loaded on a desktop viewport
- **THEN** the spending chart fills the width of its container card

#### Scenario: Chart renders correctly on narrow viewport
- **WHEN** the dashboard home page is loaded on a viewport narrower than 768px
- **THEN** the spending chart renders without clipping or horizontal overflow, fitting within the screen width

---

### Requirement: Spending page summary strip wraps on mobile
The summary strip on `GET /spending` SHALL use a wrapping flex layout
(`flex flex-wrap`) so that on narrow viewports the four stats (Total spent,
Transactions, Groups, Avg/day) can flow onto multiple lines rather than
overflowing or squeezing to illegible widths. The pipe separator dividers
between stats SHALL be hidden on xs viewports (`hidden sm:block`) to avoid
orphaned separators when items wrap.

#### Scenario: Summary strip on mobile viewport
- **WHEN** the `/spending` page is viewed on a viewport narrower than 640px
- **THEN** the four summary stats wrap onto multiple lines without horizontal overflow; pipe dividers are not visible

#### Scenario: Summary strip on tablet/desktop viewport
- **WHEN** the `/spending` page is viewed on a viewport 640px or wider
- **THEN** all four stats appear in a single horizontal row separated by pipe dividers

---

### Requirement: Spending page chart and table stack on mobile
On `GET /spending`, the bar chart and breakdown table SHALL be arranged in a
vertical stack on mobile (`flex-col`) and side-by-side on large viewports
(`lg:flex-row`). Each panel SHALL be full-width below the `lg` breakpoint.

#### Scenario: Spending layout on mobile
- **WHEN** the `/spending` page is viewed on a viewport narrower than 1024px
- **THEN** the bar chart appears above the breakdown table, each taking full width; no horizontal overflow occurs

#### Scenario: Spending layout on large viewport
- **WHEN** the `/spending` page is viewed on a viewport 1024px or wider
- **THEN** the chart and table appear side-by-side in a two-column flex row

---

### Requirement: Dashboard home spending section stacks on mobile
On `GET /`, the spending category table and doughnut chart SHALL be arranged
vertically on mobile (`flex-col`) and side-by-side on medium viewports
(`md:flex-row`). The table SHALL be full-width below `md`; the chart retains
its fixed `md:w-80` width on medium and larger viewports.

#### Scenario: Dashboard spending section on mobile
- **WHEN** the `/` page is viewed on a viewport narrower than 768px
- **THEN** the spending category table appears above the doughnut chart, each at full width

#### Scenario: Dashboard spending section on desktop
- **WHEN** the `/` page is viewed on a viewport 768px or wider
- **THEN** the spending table and doughnut chart appear side-by-side

---

### Requirement: Recurring page header wraps on mobile
The recurring page header SHALL use a wrapping flex layout so that the filter
chips (Housing, Education, Health) wrap below the page heading on narrow
viewports instead of overflowing or colliding with the heading text.

#### Scenario: Recurring header on mobile viewport
- **WHEN** the `/recurring` page is viewed on a viewport too narrow to fit the heading and all three chips in one row
- **THEN** the chip group wraps to a new line below the heading; no overflow occurs

---

### Requirement: Recurring page summary strip stacks on mobile
The recurring summary strip (Monthly, Annual, Due Soon cards) SHALL use a
responsive grid that collapses to a single column on mobile
(`grid-cols-1 sm:grid-cols-3`).

#### Scenario: Recurring summary on mobile
- **WHEN** the `/recurring` page is viewed on a viewport narrower than 640px
- **THEN** the Monthly, Annual, and Due Soon cards stack vertically

#### Scenario: Recurring summary on tablet/desktop
- **WHEN** the `/recurring` page is viewed on a viewport 640px or wider
- **THEN** the three summary cards appear in a single horizontal row

---

### Requirement: Report detail page — reduced mobile padding
The narrative card on `GET /reports/{month}` SHALL use responsive padding:
`p-4` on mobile and `p-8` on `sm` and wider viewports.

#### Scenario: Report detail padding on mobile
- **WHEN** a report detail page is viewed on a viewport narrower than 640px
- **THEN** the narrative card has 1rem (16px) padding on all sides

#### Scenario: Report detail padding on larger viewports
- **WHEN** a report detail page is viewed on a viewport 640px or wider
- **THEN** the narrative card has 2rem (32px) padding on all sides

---

### Requirement: Report detail page — markdown tables scroll horizontally
On `GET /reports/{month}`, markdown tables rendered from the narrative SHALL be
individually wrapped in a scrollable container so that wide tables do not cause
the entire page to overflow. Wrapping is applied via JavaScript post-render
after marked.js processes the narrative source.

#### Scenario: Wide markdown table on mobile
- **WHEN** the narrative contains a table wider than the viewport
- **THEN** the table scrolls horizontally within its container; the rest of the page does not scroll horizontally

---

### Requirement: Accounts page — transaction timeline chart
The `GET /accounts` route SHALL display a stacked bar chart above the accounts table showing monthly transaction counts per account for the past 13 calendar months. Each account SHALL be rendered as a distinct color-coded dataset. The chart SHALL use Chart.js (already loaded via CDN) with `type: 'bar'` and `stacked: true` on both axes.

The route SHALL accept an optional `account_id` query parameter. When present, the chart SHALL display only the matching account's data as a single (non-stacked) bar series. When absent, all accounts are shown stacked.

An account selector `<select>` element SHALL be rendered above the chart, with an "All accounts" option and one option per active account. The selector SHALL submit via a GET form to `/accounts?account_id=<id>` (or `/accounts` for all accounts). The currently selected account SHALL be pre-selected in the dropdown.

The route SHALL pass `chart_data_json` (JSON string) and `selected_account_id` to the `accounts.html` template.

#### Scenario: Chart renders all accounts by default
- **WHEN** a browser navigates to `/accounts` with no `account_id` param
- **THEN** a stacked bar chart is displayed with one dataset per active account, covering the past 13 months
- **THEN** the "All accounts" option is selected in the dropdown

#### Scenario: Account filter changes chart to single-account view
- **WHEN** the user selects a specific account from the dropdown and submits
- **THEN** the page reloads at `/accounts?account_id=<id>`
- **THEN** the chart shows only that account's monthly transaction counts as a single bar series
- **THEN** the matching account is selected in the dropdown

#### Scenario: Chart shows zero bars for months with no transactions
- **WHEN** an account has no transactions in some months within the 13-month window
- **THEN** those months render as zero-height bars (not absent from the chart)

#### Scenario: Accounts table remains present below chart
- **WHEN** the accounts page is loaded with or without an account_id filter
- **THEN** the existing summary bar and accounts table are still rendered below the chart

#### Scenario: Chart placeholder when no data
- **WHEN** no transactions exist in the database
- **THEN** the chart area renders without error; bars are all zero height or a "No data" message is shown

---

### Requirement: Recurring page — spend timeline chart

The `GET /recurring` route SHALL render a Chart.js stacked bar chart above the recurring charges table showing monthly recurring spend per merchant. The chart SHALL span the past 13 calendar months (ending with the current month) plus 3 projected future months, for 16 total x-axis labels.

The chart SHALL include:
- **Actual spend datasets**: one stacked bar dataset per merchant, colored from the standard 10-color palette, showing total absolute dollars charged per month
- **Ghost dataset**: a single non-stacked outlined bar dataset (gray, dashed border) showing the total expected-but-missing dollar amount per month across all merchants; labeled "Expected (not received)" in the tooltip; not shown in the legend
- **Projected datasets**: one stacked bar dataset per merchant (same colors at 40% opacity) for the 3 future months, showing projected charges based on `typical_amount` and `interval_days`
- **Today divider**: a vertical dashed gray line drawn between the last past month and first future month using a Chart.js `afterDraw` plugin
- **Y axis**: dollar amounts, formatted as `$X.XX` in tooltips; `beginAtZero: true`
- **Legend**: displayed when more than one merchant; legend click toggles merchant visibility client-side

The route SHALL call `get_recurring_spend_timeline(conn)` to build chart data. Chart JSON SHALL be passed to the template as `spend_chart_json` (safe). A boolean `has_spend_data` SHALL be passed; when `False`, a placeholder message SHALL be shown instead of the chart.

Below the chart, the route SHALL render the recurring charges table using three grouped sections (Needs Attention, Active Subscriptions, Likely Cancelled) as specified in the `recurring-detection` capability. The route SHALL pre-group the `get_recurring()` result into `attention`, `active`, and `cancelled` lists before passing to the template.

#### Scenario: Recurring chart renders with active merchants

- **WHEN** `GET /recurring` is requested and multiple active recurring merchants exist
- **THEN** the page renders a stacked bar chart with one colored dataset per merchant and a legend

#### Scenario: Ghost bars visible for cancelled merchant

- **WHEN** a merchant's last charge was more than one interval ago
- **THEN** the ghost dataset has non-zero values in the months where charges were expected but absent, displayed as outlined gray bars

#### Scenario: Projected bars appear in future months

- **WHEN** an active merchant is expected to charge in the next 3 months
- **THEN** lighter-colored bars appear in the future-month columns for that merchant

#### Scenario: Today divider separates past from projected

- **WHEN** the chart renders
- **THEN** a vertical dashed gray line appears between the current month column and the first future month column

#### Scenario: No recurring data shows placeholder

- **WHEN** `has_spend_data` is `False`
- **THEN** a placeholder message is shown instead of the chart canvas

#### Scenario: Table renders in grouped sections below chart

- **WHEN** `GET /recurring` is requested and recurring merchants exist across multiple urgency tiers
- **THEN** the page shows the spend timeline chart at top, followed by the grouped table sections (Needs Attention, Active Subscriptions, Likely Cancelled)

---

### UPDATED Requirement: Dashboard home page — pipeline run timestamps

Pipeline run started-at timestamps in the "Recent Runs" widget SHALL be
rendered as human-readable relative strings (e.g. "3d ago", "2h ago",
"just now") using a `js-rel-time` CSS class pattern with a `data-ts` attribute
holding the raw epoch millisecond value. A small inline JavaScript block
converts these at page load time. The raw epoch value SHALL be preserved in
the `title` attribute for accessibility.

Previously: timestamps were displayed as raw epoch millisecond integers.

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

The old `"%.2f"|format(value)` pattern, which does not produce thousands
separators, is deprecated for financial display.

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

---

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
