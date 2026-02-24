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
