## MODIFIED Requirements

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
