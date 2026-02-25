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
- **THEN** the page displays a global summary bar reading "X accounts · Y transactions · YYYY-MM-DD – YYYY-MM-DD" followed by a single table with columns: Account Name, Institution, Type, Balance, Txn Count, Date Range, Last Synced, Actions

#### Scenario: Accounts with no transactions shown in unified table
- **WHEN** an active account has zero stored transactions
- **THEN** its row shows "0" for Txn Count, "—" for Date Range, and "Never" (or "—") for Last Synced

#### Scenario: Balance column shows value or dash
- **WHEN** an account has a current balance recorded
- **THEN** the Balance column shows "$X.XX" (negative balances in red); when no balance is recorded it shows "—"

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
The `GET /spending` route SHALL display a spending breakdown chart with period selector. When `group_by=category`, the label column in the breakdown table SHALL render each category as a color-coded pill badge using the `category_badge` macro. For `group_by=merchant` and `group_by=account`, labels render as plain text.

#### Scenario: Spending chart renders (current month default)
- **WHEN** a browser navigates to `/spending`
- **THEN** a Chart.js bar or doughnut chart shows spending by category for the current month

#### Scenario: Period filter applied
- **WHEN** the user selects a different month/period and submits
- **THEN** the chart updates to show spending for the selected period

#### Scenario: Category badges in spending table
- **WHEN** the spending page is viewed with `group_by=category`
- **THEN** each label in the breakdown table renders as a colored pill badge

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
All data tables in the dashboard SHALL be wrapped in an `overflow-x-auto` container so that on narrow viewports the table can be scrolled horizontally rather than clipping or overflowing the page layout. No table columns SHALL be hidden or removed. All existing data remains accessible.

#### Scenario: Transaction table on mobile
- **WHEN** the `/transactions` page is viewed on a viewport narrower than 768px
- **THEN** the full 7-column table is accessible via horizontal scroll; no columns are hidden

#### Scenario: Pipeline run history table on mobile
- **WHEN** the `/pipeline` page is viewed on a viewport narrower than 768px
- **THEN** the full 8-column run history table is accessible via horizontal scroll

#### Scenario: Accounts table on mobile
- **WHEN** the `/accounts` page is viewed on a viewport narrower than 768px
- **THEN** the accounts table is accessible via horizontal scroll

#### Scenario: Review and recurring tables on mobile
- **WHEN** `/review` or `/recurring` is viewed on a narrow viewport
- **THEN** any data table on those pages is accessible via horizontal scroll

---

### Requirement: Spending chart is responsive
The spending doughnut chart on the dashboard home page (`GET /`) SHALL scale with its container. The chart container SHALL NOT have a fixed inline `width` style. The Chart.js configuration SHALL use `responsive: true` so the chart redraws to fill available space when the viewport changes.

#### Scenario: Chart renders at full container width on desktop
- **WHEN** the dashboard home page is loaded on a desktop viewport
- **THEN** the spending chart fills the width of its container card

#### Scenario: Chart renders correctly on narrow viewport
- **WHEN** the dashboard home page is loaded on a viewport narrower than 768px
- **THEN** the spending chart renders without clipping or horizontal overflow, fitting within the screen width
