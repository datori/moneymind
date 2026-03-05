## ADDED Requirements

### Requirement: Recurring page post-cancel summary stats
The `/recurring` route in `finance/web/app.py` SHALL compute and pass to the template:

- `post_cancel_monthly` (float): Projected monthly spend after all unresolved cancel attempts succeed. Clamped to `0.0`.
- `pending_cancel_count` (int): Number of merchants in the active/attention lists with unresolved cancel attempts.

#### Scenario: Values passed to template
- **WHEN** the `/recurring` route renders
- **THEN** the template context includes `post_cancel_monthly` (float) and `pending_cancel_count` (int)
