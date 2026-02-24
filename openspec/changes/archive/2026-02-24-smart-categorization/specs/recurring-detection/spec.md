## ADDED Requirements

### Requirement: get_recurring analysis function
The system SHALL provide `get_recurring(conn)` in `finance/analysis/review.py`. This function returns a list of dicts for distinct `merchant_normalized` values where at least one transaction has `is_recurring=1`. Each dict SHALL include: `merchant_normalized`, `count` (total transactions with that merchant_normalized and is_recurring=1), and `typical_amount` (median or most-common absolute amount for that merchant). Results SHALL be ordered by `count` DESC.

#### Scenario: Recurring merchants returned
- **WHEN** three transactions share `merchant_normalized="Netflix"` with `is_recurring=1`
- **THEN** `get_recurring(conn)` includes an entry `{merchant_normalized: "Netflix", count: 3, typical_amount: <amount>}`

#### Scenario: Non-recurring merchants excluded
- **WHEN** a merchant has `is_recurring=0` for all its transactions
- **THEN** it does not appear in the result of `get_recurring(conn)`

#### Scenario: Empty result
- **WHEN** no transactions have `is_recurring=1`
- **THEN** `get_recurring(conn)` returns an empty list

#### Scenario: Ordered by count descending
- **WHEN** "Netflix" has 12 recurring transactions and "Spotify" has 3
- **THEN** "Netflix" appears before "Spotify" in the result list

---

### Requirement: finance recurring CLI command
The system SHALL provide a `finance recurring` CLI command that prints a plain-text summary table of detected recurring charges. Columns: Merchant, Count, Typical Amount.

#### Scenario: Table printed when recurring charges exist
- **WHEN** `finance recurring` is run and recurring merchants exist
- **THEN** a table is printed with one row per recurring merchant, ordered by count DESC

#### Scenario: Empty message when none detected
- **WHEN** `finance recurring` is run and no recurring charges have been detected
- **THEN** stdout shows "No recurring charges detected. Run `finance sync` to enrich transactions."

---

### Requirement: GET /recurring web route
The system SHALL provide a `GET /recurring` route in `finance/web/app.py` that renders a Jinja2 template showing a summary table of detected recurring merchants. Columns: Merchant, Occurrences, Typical Amount.

#### Scenario: Recurring page loads with data
- **WHEN** `GET /recurring` is requested and recurring merchants exist
- **THEN** an HTML table is returned with one row per recurring merchant

#### Scenario: Empty recurring page
- **WHEN** `GET /recurring` is requested and no recurring charges exist
- **THEN** the page renders a message: "No recurring charges detected."
