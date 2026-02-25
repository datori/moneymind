## MODIFIED Requirements

### Requirement: Unified accounts page replaces separate /accounts and /data pages
`GET /accounts` SHALL display a unified page with a global summary bar at the top and a single rich per-account table. The separate `/data` route is deprecated.

#### Scenario: Unified accounts page loads
- **WHEN** a browser navigates to `/accounts`
- **THEN** the page displays a global summary bar reading "X accounts · Y transactions · YYYY-MM-DD – YYYY-MM-DD" (or equivalent compact format) followed by a single table with columns: Account Name, Institution, Type, Balance, Txn Count, Date Range, Last Synced, Actions

#### Scenario: Accounts with no transactions shown in unified table
- **WHEN** an active account has zero stored transactions
- **THEN** its row in the table shows "0" for Txn Count, "—" for Date Range, and "Never" (or "—") for Last Synced

#### Scenario: Balance column shows value or dash
- **WHEN** an account has a current balance recorded
- **THEN** the Balance column shows "$X.XX" (negative balances in red); when no balance is recorded it shows "—"

---

### Requirement: /data redirects to /accounts
`GET /data` SHALL return HTTP 301 to `/accounts`.

#### Scenario: /data redirect
- **WHEN** a browser or HTTP client issues `GET /data`
- **THEN** the response is HTTP 301 with `Location: /accounts`

---

### Requirement: Nav "Data" link removed
The navigation bar SHALL NOT contain a "Data" link. The "Accounts" link SHALL remain and point to `/accounts`.

#### Scenario: Nav does not show Data link
- **WHEN** any page in the dashboard is loaded
- **THEN** the navigation bar shows: Dashboard, Accounts, Transactions, Net Worth, Spending, Review, Recurring — with no "Data" entry

---

### Requirement: Spending page include_financial toggle
`GET /spending` SHALL accept an `include_financial` query parameter (value `"1"` = include, absent or `"0"` = exclude). When absent or `"0"`, transactions in categories Financial, Income, and Investment are excluded from the spending query. The page SHALL render a visible toggle (checkbox labeled "Include Financial Activity") that reflects the current state and resubmits the form when changed.

#### Scenario: Default spending excludes financial categories
- **WHEN** a browser navigates to `/spending` with no `include_financial` param
- **THEN** the spending results exclude transactions whose category is Financial, Income, or Investment; the "Include Financial Activity" checkbox is unchecked

#### Scenario: include_financial=1 includes all categories
- **WHEN** a browser navigates to `/spending?include_financial=1` (or the user checks the toggle and submits)
- **THEN** the spending results include transactions of all categories, including Financial, Income, and Investment; the "Include Financial Activity" checkbox is checked

#### Scenario: Toggle state preserved in form submission
- **WHEN** the user selects a date range and checks "Include Financial Activity" and clicks Apply
- **THEN** the resulting URL contains both the date params and `include_financial=1`

#### Scenario: Spending summary chart updates with toggle
- **WHEN** the toggle is switched from OFF to ON
- **THEN** the Chart.js bar chart re-renders showing the updated (larger) spending totals that now include financial activity

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

### Requirement: Existing web-dashboard requirements remain satisfied
All previously specified requirements for GET /, GET /accounts (balance table), GET /transactions, GET /net-worth, GET /review, GET /recurring, POST /sync, and Sync Now button continue to be satisfied after this change.

#### Scenario: Home page unaffected
- **WHEN** a browser navigates to `/`
- **THEN** the page continues to display net worth, spending summary, and credit utilization

#### Scenario: Sync Now button works from any page
- **WHEN** the user clicks "Sync Now" on any dashboard page
- **THEN** `POST /sync` is triggered and the user is redirected back to the same page with a result message
