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
The `GET /accounts` route SHALL display all active accounts with current balances.

#### Scenario: Accounts page loads
- **WHEN** a browser navigates to `/accounts`
- **THEN** a table of accounts is shown with columns: name, type, institution, balance, last updated

---

### Requirement: Transactions page
The `GET /transactions` route SHALL display a filterable transaction list.

#### Scenario: Transactions page loads with defaults
- **WHEN** a browser navigates to `/transactions`
- **THEN** the last 30 days of transactions are shown (up to 100)

#### Scenario: Date range filter applied
- **WHEN** the user sets start/end date fields and submits the filter form
- **THEN** the page reloads showing only transactions in that range

---

### Requirement: Net worth history page
The `GET /net-worth` route SHALL display a time-series chart of net worth.

#### Scenario: Net worth chart renders
- **WHEN** a browser navigates to `/net-worth`
- **THEN** a Chart.js line chart is displayed showing net worth over time (one data point per sync date)

---

### Requirement: Spending breakdown page
The `GET /spending` route SHALL display a spending breakdown chart with period selector.

#### Scenario: Spending chart renders (current month default)
- **WHEN** a browser navigates to `/spending`
- **THEN** a Chart.js bar or doughnut chart shows spending by category for the current month

#### Scenario: Period filter applied
- **WHEN** the user selects a different month/period and submits
- **THEN** the chart updates to show spending for the selected period

---

### Requirement: Sync now button
The dashboard SHALL include a "Sync Now" button that triggers a SimpleFIN sync.

#### Scenario: Sync triggered from dashboard
- **WHEN** the user clicks "Sync Now" on any dashboard page
- **THEN** a `POST /sync` request is made, sync runs, and the user is redirected back to the same page

#### Scenario: Sync error displayed
- **WHEN** the sync fails (e.g. network error)
- **THEN** an error message is displayed on the redirected page
