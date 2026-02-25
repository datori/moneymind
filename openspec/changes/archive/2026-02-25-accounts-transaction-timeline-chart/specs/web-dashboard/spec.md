## ADDED Requirements

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
