## ADDED Requirements

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

## MODIFIED Requirements

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
