## ADDED Requirements

### Requirement: `finance accounts delete` command
The system SHALL provide a `finance accounts delete <account-id>` CLI command that permanently deletes an account and all rows dependent on it.

Rows deleted (in order, within a single transaction):
1. `credit_limits` WHERE `account_id = <id>`
2. `sync_state` WHERE `account_id = <id>`
3. `transactions` WHERE `account_id = <id>`
4. `balances` WHERE `account_id = <id>`
5. `accounts` WHERE `id = <id>`

The command SHALL print a confirmation prompt before deleting unless `--confirm` is passed.

#### Scenario: Delete with interactive confirmation accepted
- **WHEN** `finance accounts delete <account-id>` is run and the user types `y` at the prompt
- **THEN** all dependent rows and the account row are deleted, and a success message is printed showing the account name and counts of deleted rows per table

#### Scenario: Delete with interactive confirmation rejected
- **WHEN** `finance accounts delete <account-id>` is run and the user types `n` at the prompt
- **THEN** no rows are deleted and the command exits 0 with the message `"Aborted."`

#### Scenario: Delete with --confirm flag skips prompt
- **WHEN** `finance accounts delete <account-id> --confirm` is run
- **THEN** deletion proceeds immediately without any prompt

#### Scenario: Non-existent account ID
- **WHEN** `finance accounts delete <nonexistent-id>` is run
- **THEN** an error message is printed (`"Error: account '<id>' not found."`) and the command exits non-zero; no rows are deleted

#### Scenario: Success message includes deleted row counts
- **WHEN** an account with N transactions, M balances, and a credit limit is deleted
- **THEN** stdout reports the count of deleted rows for each affected table (transactions, balances, credit_limits, sync_state)

---

### Requirement: Delete button on accounts page
Each row in the accounts table on `GET /accounts` SHALL include a [Delete] button.

#### Scenario: Delete button visible on accounts page
- **WHEN** a browser navigates to `/accounts` and at least one account exists
- **THEN** each account row in the table shows a [Delete] button in an Actions column

---

### Requirement: Inline confirmation with impact counts
Clicking [Delete] SHALL expand the row inline to show the number of transactions and balance snapshots that will be permanently removed, along with [Confirm Delete] and [Cancel] controls. No separate page is required.

#### Scenario: Confirmation shows impact counts
- **WHEN** the user clicks [Delete] on an account row
- **THEN** the row expands (or reveals a sub-row) showing: "This will permanently delete N transactions and M balance snapshots." along with [Confirm Delete] and [Cancel] buttons

#### Scenario: Cancel dismisses the confirmation
- **WHEN** the user clicks [Cancel] after the confirmation expands
- **THEN** the expanded confirmation collapses and no request is sent

---

### Requirement: POST /accounts/{id}/delete handler
The system SHALL accept `POST /accounts/{id}/delete`. The handler SHALL delete all dependent rows in the correct cascade order, then redirect to `/accounts` with a success flash message.

Cascade order (all within a single database transaction):
1. `DELETE FROM credit_limits WHERE account_id = ?`
2. `DELETE FROM sync_state WHERE account_id = ?`
3. `DELETE FROM transactions WHERE account_id = ?`
4. `DELETE FROM balances WHERE account_id = ?`
5. `DELETE FROM accounts WHERE id = ?`

#### Scenario: Successful delete redirects with flash message
- **WHEN** `POST /accounts/{id}/delete` is submitted for a valid account
- **THEN** all dependent rows are deleted in cascade order, the account row is deleted, and the browser is redirected to `/accounts?msg=...` where the message includes the account name, transaction count, and balance count that were deleted

#### Scenario: Flash message includes deleted counts
- **WHEN** an account with 47 transactions and 12 balance snapshots is deleted
- **THEN** the flash message shown on `/accounts` after redirect reads something like "Deleted account 'My Checking' (47 transactions, 12 balances removed)."

#### Scenario: Invalid account ID returns 404
- **WHEN** `POST /accounts/{nonexistent-id}/delete` is submitted
- **THEN** the server responds with HTTP 404; no rows are deleted

#### Scenario: Cascade is atomic
- **WHEN** the deletion handler runs
- **THEN** all five DELETE statements execute inside a single SQLite transaction; if any step fails, all prior steps are rolled back

---

### Requirement: Impact query before confirmation
Before showing the inline confirmation, the template SHALL have access to the per-account transaction count and balance count so the impact text can be rendered without an extra round-trip.

#### Scenario: Impact counts rendered from existing data
- **WHEN** the `/accounts` page renders
- **THEN** each account row's inline confirmation text uses transaction and balance counts already present in the template context (sourced from `get_data_overview()` and a balance count query in the route handler, or equivalent)

---

### Requirement: Flash message rendered in accounts template

The `accounts.html` template SHALL render the `msg` template variable when it is
non-empty. The message SHALL appear as a green (emerald) alert banner immediately
below the page heading and above the summary bar.

#### Scenario: Flash message displays after deletion
- **WHEN** the browser follows the redirect to `/accounts?msg=...` after a successful
  account deletion
- **THEN** an emerald alert banner appears at the top of the page content showing
  the deletion confirmation message

#### Scenario: No banner when msg is absent
- **WHEN** `/accounts` is loaded without a `msg` query parameter
- **THEN** no alert banner is rendered

---

### Requirement: `finance accounts` group preserves existing list behavior
The conversion of `finance accounts` from a plain command to a Click group SHALL preserve backward compatibility: invoking `finance accounts` without a subcommand SHALL still list all accounts.

#### Scenario: `finance accounts` without subcommand lists accounts
- **WHEN** `finance accounts` is run with no subcommand
- **THEN** a formatted table of accounts is printed, identical to the previous behavior

#### Scenario: `finance accounts list` is an explicit alias
- **WHEN** `finance accounts list` is run
- **THEN** the same account listing is printed
