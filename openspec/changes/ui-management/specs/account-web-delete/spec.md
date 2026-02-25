## ADDED Requirements

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
