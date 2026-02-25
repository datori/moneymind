## MODIFIED Requirements

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
