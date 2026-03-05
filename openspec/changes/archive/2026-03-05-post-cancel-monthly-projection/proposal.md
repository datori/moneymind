## Why

The recurring page shows current monthly spend but gives no indication of what spend would look like after pending cancellations succeed. Users who have tracked multiple cancellation attempts have no way to see the financial impact of those cancellations at a glance.

## What Changes

- **Route computation** — The `/recurring` route computes two new values: `post_cancel_monthly` (projected monthly after all unresolved cancel attempts succeed) and `pending_cancel_count` (number of merchants with unresolved cancel attempts in the displayed data).
- **Monthly card secondary stat** — The Monthly summary card gains a secondary line showing the projection when `pending_cancel_count > 0`: "→ ~$X if N cancel(s) work". Hidden when no pending cancels exist.

## Capabilities

### New Capabilities
- `recurring-post-cancel-projection`: Compute and display projected monthly spend assuming all pending cancellation attempts succeed.

### Modified Capabilities
- `recurring-detection`: The `/recurring` route now passes `post_cancel_monthly` and `pending_cancel_count` to the template as part of the summary strip display.

## Impact

- `finance/web/app.py` — two new computed values in the recurring route
- `finance/web/templates/recurring.html` — conditional secondary line in the Monthly card
