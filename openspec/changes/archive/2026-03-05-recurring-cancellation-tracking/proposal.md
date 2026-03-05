## Why

When a user attempts to cancel a recurring subscription, there is no way to track that intent or detect if the cancellation failed and charges continue. This leads to "zombie" subscriptions — services the user believed were cancelled but that are still billing.

## What Changes

- **New `recurring_cancel_attempts` table** — stores per-merchant cancel attempt metadata: `merchant_normalized`, `attempted_at`, `notes`, `resolved_at`.
- **`get_recurring()` enrichment** — each result dict gains a `cancel_attempt` field containing attempt state and a derived `is_zombie` flag (true when charges exist after `attempted_at`).
- **CRUD API endpoints** — four new routes under `/recurring/cancel/` to upsert, resolve, and delete cancel attempts.
- **Recurring page UI** — each merchant row gains cancel tracking: a "Track Cancel" button when no attempt is recorded, and status badges (pending / zombie / resolved) with action buttons when one exists.
- **Zombie prominence** — zombie merchants are visually distinct and elevated in the Needs Attention section.

## Capabilities

### New Capabilities
- `recurring-cancellation-tracking`: Per-merchant cancel attempt persistence, `get_recurring()` enrichment with zombie detection, CRUD endpoints, and recurring page cancel tracking UI.

### Modified Capabilities
- `recurring-detection`: `get_recurring()` return shape gains a `cancel_attempt` field. `/recurring` page gains cancel action column and zombie display logic.

## Impact

- `finance/db.py` — new `recurring_cancel_attempts` table + migration
- `finance/analysis/review.py` — enrich `get_recurring()` with cancel attempt data
- `finance/web/app.py` — four new API endpoints; pass enriched data to template
- `finance/web/templates/recurring.html` — cancel badges, action buttons, zombie row treatment
