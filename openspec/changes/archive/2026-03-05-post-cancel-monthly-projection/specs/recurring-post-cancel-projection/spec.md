## ADDED Requirements

### Requirement: post_cancel_monthly route computation
The `/recurring` route SHALL compute two additional values and pass them to the template:

- `post_cancel_monthly` (float): `summary_monthly_total` minus the sum of `monthly_equiv` for all merchants in `non_cancelled` that have an unresolved cancel attempt (`cancel_attempt is not None AND cancel_attempt["resolved_at"] is None`). This represents the projected monthly spend if all pending cancellations succeed. Shall be clamped to a minimum of `0.0`.
- `pending_cancel_count` (int): Count of merchants in `non_cancelled` with an unresolved cancel attempt.

Merchants with `status == "likely_cancelled"` (already in the `cancelled` list, not in `non_cancelled`) SHALL NOT be included in the savings computation.

#### Scenario: Post-cancel monthly computed correctly
- **WHEN** two merchants have unresolved cancel attempts with monthly-equivalent costs of $10/mo and $20/mo, and `summary_monthly_total` is $100
- **THEN** `post_cancel_monthly` is `70.0` and `pending_cancel_count` is `2`

#### Scenario: Zero pending cancels
- **WHEN** no merchants have unresolved cancel attempts
- **THEN** `pending_cancel_count` is `0` and `post_cancel_monthly` equals `summary_monthly_total`

#### Scenario: Zombie included in savings estimate
- **WHEN** a merchant is a zombie (cancel_attempt.is_zombie=True, resolved_at=None)
- **THEN** its monthly-equivalent cost is included in the savings computation

#### Scenario: Resolved cancel not included
- **WHEN** a merchant has `cancel_attempt.resolved_at` set
- **THEN** its cost is NOT subtracted from `summary_monthly_total`

#### Scenario: post_cancel_monthly never negative
- **WHEN** the savings computation would produce a negative result
- **THEN** `post_cancel_monthly` is clamped to `0.0`

---

### Requirement: Monthly card post-cancel projection display
The Monthly summary card on the `/recurring` page SHALL display a secondary projection line when `pending_cancel_count > 0`. The line SHALL show `"→ ~$X if N cancel(s) work"` where X is `post_cancel_monthly` (rounded to nearest dollar) and N is `pending_cancel_count`. When `pending_cancel_count == 0`, the secondary line SHALL be hidden.

#### Scenario: Projection shown when pending cancels exist
- **WHEN** `pending_cancel_count` is 2 and `post_cancel_monthly` is 580
- **THEN** the Monthly card shows a secondary line containing "→ ~$580 if 2 cancel(s) work"

#### Scenario: Projection hidden when no pending cancels
- **WHEN** `pending_cancel_count` is 0
- **THEN** no projection line is shown in the Monthly card

#### Scenario: Projection uses filtered merchant set
- **WHEN** the housing toggle is off (Home & Utilities excluded)
- **THEN** the projection reflects only the visible merchants (housing excluded from both totals)
