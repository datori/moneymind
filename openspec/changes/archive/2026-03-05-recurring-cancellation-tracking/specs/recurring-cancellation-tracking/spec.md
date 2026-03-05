## ADDED Requirements

### Requirement: recurring_cancel_attempts table
The system SHALL maintain a `recurring_cancel_attempts` table in SQLite with the following columns:
- `merchant_normalized` TEXT PRIMARY KEY — identifies the merchant
- `attempted_at` TEXT NOT NULL — ISO date (`YYYY-MM-DD`) when the user attempted cancellation
- `notes` TEXT — optional free-text user note (nullable)
- `resolved_at` TEXT — ISO date when the user confirmed the subscription stopped (nullable; NULL = still pending)

The table SHALL be created by `init_db()` and be idempotent across multiple calls.

#### Scenario: Table created on init
- **WHEN** `init_db(conn)` is called on a fresh database
- **THEN** the `recurring_cancel_attempts` table exists with the correct schema

#### Scenario: Table creation is idempotent
- **WHEN** `init_db(conn)` is called twice on the same database
- **THEN** no error is raised and the table still exists

---

### Requirement: POST /recurring/cancel endpoint
`POST /recurring/cancel` SHALL upsert a cancel attempt record for the given merchant. The request body SHALL include:
- `merchant_normalized` (str): the merchant key
- `attempted_at` (str): ISO date of the cancel attempt
- `notes` (str, optional): free-text note

If a record already exists for `merchant_normalized`, it SHALL be replaced (upsert). `resolved_at` SHALL be set to NULL on upsert. The endpoint SHALL redirect to `/recurring` (with query params preserved via the `return_to` field if provided) after success.

#### Scenario: New cancel attempt created
- **WHEN** `POST /recurring/cancel` is submitted with a valid `merchant_normalized` and `attempted_at`
- **THEN** a row is inserted in `recurring_cancel_attempts` and the response redirects to `/recurring`

#### Scenario: Existing attempt is overwritten
- **WHEN** `POST /recurring/cancel` is submitted for a merchant that already has a cancel attempt record
- **THEN** the existing record is replaced with the new `attempted_at` and `notes`, and `resolved_at` is cleared to NULL

#### Scenario: Notes field is optional
- **WHEN** `POST /recurring/cancel` is submitted without a `notes` field
- **THEN** the record is created with `notes = NULL` and no error is raised

---

### Requirement: POST /recurring/cancel/resolve endpoint
`POST /recurring/cancel/resolve` SHALL set `resolved_at = today` (ISO date) for the given merchant's cancel attempt. The request body SHALL include `merchant_normalized`. The endpoint SHALL redirect to `/recurring` after success. If no cancel attempt record exists for the merchant, no error is raised.

#### Scenario: Resolve sets resolved_at to today
- **WHEN** `POST /recurring/cancel/resolve` is submitted with a valid `merchant_normalized`
- **THEN** `resolved_at` is set to today's ISO date for that merchant's record

#### Scenario: Resolve on missing record is a no-op
- **WHEN** `POST /recurring/cancel/resolve` is submitted for a merchant with no cancel attempt record
- **THEN** no error is raised

---

### Requirement: POST /recurring/cancel/delete endpoint
`POST /recurring/cancel/delete` SHALL remove the cancel attempt record for the given `merchant_normalized`. The endpoint SHALL redirect to `/recurring` after success. If no record exists, no error is raised.

#### Scenario: Delete removes the record
- **WHEN** `POST /recurring/cancel/delete` is submitted with a valid `merchant_normalized`
- **THEN** the row is removed from `recurring_cancel_attempts`

#### Scenario: Delete on missing record is a no-op
- **WHEN** `POST /recurring/cancel/delete` is submitted for a merchant with no record
- **THEN** no error is raised

---

### Requirement: Recurring page cancel tracking UI
The `/recurring` page SHALL display cancel tracking state for every merchant row. The UI SHALL include:

- **No attempt recorded**: A small "Track Cancel" button that opens an inline form to submit `POST /recurring/cancel` with `merchant_normalized`, `attempted_at` (defaulting to today), and optional `notes`.
- **Pending attempt (not zombie)**: An amber badge showing "Cancel attempted {attempted_at}" with a [Resolve] button (submits `POST /recurring/cancel/resolve`) and a [Remove] button (submits `POST /recurring/cancel/delete`).
- **Zombie**: A red badge "Zombie — still charging!" with [Resolve] and [Remove] buttons. The row SHALL receive prominent visual treatment (e.g., red row tint or red left border).
- **Resolved**: A green badge "Cancelled {resolved_at}" with a [Remove] button.

Zombie merchants SHALL appear in the Needs Attention section regardless of their computed `status`.

#### Scenario: Track Cancel button shown when no attempt recorded
- **WHEN** a merchant has no cancel attempt record
- **THEN** its row shows a "Track Cancel" button

#### Scenario: Amber badge shown for pending attempt
- **WHEN** a merchant has a cancel attempt with `resolved_at = NULL` and `is_zombie = False`
- **THEN** its row shows an amber "Cancel attempted {date}" badge with Resolve and Remove buttons

#### Scenario: Zombie badge shown when charges continued
- **WHEN** a merchant has a cancel attempt and `is_zombie = True`
- **THEN** its row shows a red "Zombie — still charging!" badge with Resolve and Remove buttons

#### Scenario: Green badge shown for resolved attempts
- **WHEN** a merchant has a cancel attempt with `resolved_at` set
- **THEN** its row shows a green "Cancelled {resolved_at}" badge with a Remove button

#### Scenario: Zombie merchant appears in Needs Attention
- **WHEN** a merchant is a zombie (is_zombie=True, resolved_at=NULL)
- **THEN** it appears in the Needs Attention section of the recurring page
