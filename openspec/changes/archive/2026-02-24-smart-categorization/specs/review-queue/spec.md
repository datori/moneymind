## ADDED Requirements

### Requirement: get_review_queue analysis function
The system SHALL provide `get_review_queue(conn)` in `finance/analysis/review.py`. This function returns a list of dicts for all transactions where `needs_review=1`, ordered by `date` DESC. Each dict SHALL include at minimum: `id`, `date`, `amount`, `description`, `merchant_name`, `merchant_normalized`, `category`, `review_reason`, `account_id`.

#### Scenario: Flagged transactions returned
- **WHEN** three transactions have `needs_review=1`
- **THEN** `get_review_queue(conn)` returns exactly three dicts, most recent date first

#### Scenario: Empty queue
- **WHEN** no transactions have `needs_review=1`
- **THEN** `get_review_queue(conn)` returns an empty list

#### Scenario: Non-flagged transactions excluded
- **WHEN** a transaction has `needs_review=0`
- **THEN** it does not appear in the result of `get_review_queue(conn)`

---

### Requirement: finance review --list CLI command
The system SHALL provide `finance review --list` as a CLI command that prints all flagged transactions as a plain-text table without interactive prompts. Columns: Date, Amount, Merchant, Category, Reason.

#### Scenario: Table printed when flags exist
- **WHEN** `finance review --list` is run and flagged transactions exist
- **THEN** a table is printed to stdout with one row per flagged transaction

#### Scenario: Empty message when no flags
- **WHEN** `finance review --list` is run and no transactions are flagged
- **THEN** stdout shows "No transactions flagged for review."

---

### Requirement: finance review interactive triage
The system SHALL provide `finance review` (no `--list` flag) as an interactive CLI command. For each flagged transaction (ordered by date DESC), the command SHALL display: description, merchant_normalized, amount, date, category, and review_reason. It SHALL then prompt: `[a]ccept / [r]eclassify / [s]kip`.

- **accept**: sets `needs_review=0`, commits, moves to next.
- **reclassify**: prompts for new category name, validates against CATEGORIES, sets `needs_review=0` and updates `category`, commits, moves to next.
- **skip**: moves to next without writing anything.

After all items are processed (or if queue is empty), the command exits with a summary: "Reviewed N transaction(s). Accepted: X. Reclassified: Y. Skipped: Z."

#### Scenario: Accept clears flag
- **WHEN** user presses `a` for a flagged transaction
- **THEN** `needs_review` is set to 0 for that transaction
- **AND** `category` and `review_reason` are unchanged

#### Scenario: Reclassify updates category and clears flag
- **WHEN** user presses `r` and enters a valid category
- **THEN** `needs_review` is set to 0 and `category` is updated to the entered value

#### Scenario: Invalid category on reclassify re-prompts
- **WHEN** user enters an unrecognized category name during reclassify
- **THEN** an error is shown and the category prompt is repeated

#### Scenario: Skip leaves transaction unchanged
- **WHEN** user presses `s` for a flagged transaction
- **THEN** `needs_review` remains 1 and no DB write occurs for that transaction

#### Scenario: Empty queue exits immediately
- **WHEN** `finance review` is run and no transactions are flagged
- **THEN** stdout shows "No transactions flagged for review." and the command exits

---

### Requirement: GET /review web route
The system SHALL provide a `GET /review` route in `finance/web/app.py` that renders a Jinja2 template showing a table of all flagged transactions. Each row SHALL include: date, amount, description, merchant_normalized, current category (as a dropdown of all valid categories), review_reason, and an "Approve" button.

Submitting the Approve button for a row SHALL send `POST /review/{id}/approve` with the selected category. The POST handler SHALL set `needs_review=0`, update `category` if changed, commit, and redirect back to `GET /review`.

#### Scenario: Review page loads
- **WHEN** `GET /review` is requested
- **THEN** an HTML table is returned with one row per flagged transaction

#### Scenario: Approve clears flag
- **WHEN** `POST /review/{id}/approve` is submitted for a valid transaction ID
- **THEN** `needs_review=0` is set and `category` is updated to the submitted value
- **AND** the response redirects to `GET /review`

#### Scenario: Empty review page
- **WHEN** `GET /review` is requested and no transactions are flagged
- **THEN** the page renders a message: "No transactions flagged for review."

---

### Requirement: Modified transaction-categorization post-categorize hook
The `transaction-categorization` capability's automatic post-sync/post-categorize trigger SHALL be extended to also call `enrich_transactions(conn)` after categorization completes, when `ANTHROPIC_API_KEY` is set.

#### Scenario: Enrichment runs after categorize
- **WHEN** `finance categorize` finishes categorizing transactions and `ANTHROPIC_API_KEY` is set
- **THEN** `enrich_transactions(conn)` is called
- **AND** enrichment failure does not cause `finance categorize` to exit non-zero
