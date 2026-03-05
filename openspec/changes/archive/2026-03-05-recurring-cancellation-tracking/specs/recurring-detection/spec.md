## MODIFIED Requirements

### Requirement: get_recurring analysis function
`get_recurring(conn)` in `finance/analysis/review.py` SHALL return a list of enriched dicts for distinct `merchant_normalized` values where at least one transaction has `is_recurring=1`. Each dict SHALL include:

- `merchant_normalized` (str): The normalized merchant name.
- `count` (int): Number of transactions with `is_recurring=1` for this merchant.
- `typical_amount` (float): Median absolute amount across all recurring charges.
- `total_spent` (float): Sum of absolute amounts across all recurring charges.
- `last_date` (str | None): ISO date string (`YYYY-MM-DD`) of the most recent charge, or `None` if no dates available.
- `interval_days` (int | None): Median gap in days between consecutive charges, or `None` if fewer than 2 charges.
- `interval_label` (str | None): Human-readable label derived from `interval_days` using this mapping: 5–9 → `"Weekly"`, 13–17 → `"Bi-weekly"`, 25–35 → `"Monthly"`, 85–95 → `"Quarterly"`, 175–190 → `"Semi-annual"`, 355–375 → `"Annual"`, else `"Every ~{interval_days}d"`. `None` if `interval_days` is `None`.
- `next_due_date` (str | None): ISO date string of `last_date + timedelta(days=interval_days)`, or `None` if `interval_days` is `None`.
- `days_until_next` (int | None): `(next_due_date - today).days`, or `None` if `next_due_date` is `None`.
- `status` (str | None): One of `"upcoming"`, `"due_soon"`, `"due_any_day"`, `"past_due"`, `"likely_cancelled"`, or `None` (when interval cannot be computed). Derived as:
  - `days_until_next > 7` → `"upcoming"`
  - `1 <= days_until_next <= 7` → `"due_soon"`
  - `-tolerance <= days_until_next <= 0` → `"due_any_day"` where `tolerance = max(3, int(interval_days * 0.35))`
  - `-interval_days < days_until_next < -tolerance` → `"past_due"`
  - `days_until_next <= -interval_days` → `"likely_cancelled"`
- `cancel_attempt` (dict | None): Cancel attempt metadata if a record exists in `recurring_cancel_attempts` for this merchant, otherwise `None`. When present, the dict SHALL include:
  - `attempted_at` (str): ISO date of the cancel attempt.
  - `notes` (str | None): Free-text note.
  - `resolved_at` (str | None): ISO date of resolution, or `None` if unresolved.
  - `is_zombie` (bool): `True` when `last_date > attempted_at` AND `resolved_at IS NULL`.

Results SHALL be sorted by urgency: `"past_due"` first (most overdue first), then `"likely_cancelled"` (most overdue first), then `"due_any_day"`, then `"due_soon"` (fewest days first), then `"upcoming"` (fewest days first), then `None` status last. Zombie merchants (unresolved cancel attempt with `is_zombie=True`) SHALL sort into the urgency tier equivalent to `"past_due"` regardless of their computed `status`.

#### Scenario: cancel_attempt is None when no attempt recorded
- **WHEN** a merchant has no row in `recurring_cancel_attempts`
- **THEN** its dict has `cancel_attempt = None`

#### Scenario: cancel_attempt populated when attempt exists
- **WHEN** a merchant has a row in `recurring_cancel_attempts` with `attempted_at = "2026-03-01"` and `resolved_at = NULL`
- **THEN** its dict has `cancel_attempt` with `attempted_at = "2026-03-01"`, `resolved_at = None`

#### Scenario: is_zombie True when charges exist after attempt
- **WHEN** a merchant's `last_date` is `"2026-03-10"` and `attempted_at` is `"2026-03-01"` and `resolved_at` is NULL
- **THEN** `cancel_attempt["is_zombie"]` is `True`

#### Scenario: is_zombie False when no charges after attempt
- **WHEN** a merchant's `last_date` is `"2026-02-28"` and `attempted_at` is `"2026-03-01"`
- **THEN** `cancel_attempt["is_zombie"]` is `False`

#### Scenario: is_zombie False when attempt is resolved
- **WHEN** a merchant has `last_date > attempted_at` but `resolved_at` is set
- **THEN** `cancel_attempt["is_zombie"]` is `False`

#### Scenario: Zombie merchant sorts with past_due urgency
- **WHEN** a zombie merchant exists alongside an `"upcoming"` merchant
- **THEN** the zombie merchant appears before the upcoming merchant in results
