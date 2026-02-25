## ADDED Requirements

### Requirement: Dashboard web server starts
The system SHALL provide a `finance-dashboard` entry point that starts a web server.

#### Scenario: Server starts on default port
- **WHEN** `uv run finance-dashboard` is executed
- **THEN** a web server starts on `localhost:8080` and is accessible in a browser

#### Scenario: Custom port and host
- **WHEN** `uv run finance-dashboard --port 9090 --host 0.0.0.0` is executed
- **THEN** the server starts on the specified host and port

---

### Requirement: Dashboard home page
The `GET /` route SHALL display a summary dashboard with net worth, spending, and utilization.

#### Scenario: Home page loads
- **WHEN** a browser navigates to `/`
- **THEN** the page displays: current net worth, spending summary for current month (by category), credit utilization for all configured cards

---

### Requirement: Accounts page
The `GET /accounts` route SHALL display all active accounts with current balances AND a "Data Coverage" section below the balance table.

#### Scenario: Accounts page loads
- **WHEN** a browser navigates to `/accounts`
- **THEN** a table of accounts is shown with columns: name, type, institution, balance, last updated; followed by a "Data Coverage" section showing per-account transaction count, date range (formatted as "Mon YY – Mon YY"), and last sync time

#### Scenario: Accounts page global summary
- **WHEN** a browser navigates to `/accounts`
- **THEN** the "Data Coverage" section includes a header line reading "X transactions across Y accounts, covering Z months"

#### Scenario: Accounts page coverage for account with no transactions
- **WHEN** an active account has zero stored transactions
- **THEN** its row in the Data Coverage section shows "0" for transaction count and "—" for date range

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

### Requirement: Data page shows full data coverage overview
The `GET /data` route SHALL display a dedicated "Data" page with a global summary header and a per-account coverage table.

#### Scenario: Data page loads with transaction data
- **WHEN** a browser navigates to `/data`
- **THEN** the page displays a global summary header reading "X transactions across Y accounts, covering Z months" and a table listing each active account with columns: name, institution, transaction count, date range (formatted as "Mon YY – Mon YY"), and last sync time

#### Scenario: Data page with an account that has no transactions
- **WHEN** an active account has zero stored transactions
- **THEN** that account row shows "0" for transaction count, "—" for date range, and either the last sync time or "Never"

#### Scenario: Data page with no data at all
- **WHEN** the database has no active accounts
- **THEN** the page displays the global summary header with zeroes and an empty table (or a "No accounts configured" message)

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
