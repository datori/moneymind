## 1. Database Schema

- [x] 1.1 Add `recurring_cancel_attempts` table to `_SCHEMA` in `finance/db.py` with columns: `merchant_normalized` TEXT PRIMARY KEY, `attempted_at` TEXT NOT NULL, `notes` TEXT, `resolved_at` TEXT
- [x] 1.2 Ensure `init_db()` creates the table (idempotent via `CREATE TABLE IF NOT EXISTS`)

## 2. Analysis Layer

- [x] 2.1 In `get_recurring()` (`finance/analysis/review.py`), query `recurring_cancel_attempts` and build a lookup dict keyed by `merchant_normalized`
- [x] 2.2 For each merchant result, attach `cancel_attempt` dict (or `None`) with `attempted_at`, `notes`, `resolved_at`, and derived `is_zombie` bool (`last_date > attempted_at AND resolved_at IS NULL`)
- [x] 2.3 Update sort logic so zombie merchants (unresolved `is_zombie=True`) sort with `past_due` urgency

## 3. API Endpoints

- [x] 3.1 Add `POST /recurring/cancel` to `finance/web/app.py` — accepts form fields `merchant_normalized`, `attempted_at`, `notes`; upserts into `recurring_cancel_attempts` with `resolved_at = NULL`; redirects to `/recurring` (preserving query params if `return_to` provided)
- [x] 3.2 Add `POST /recurring/cancel/resolve` — accepts `merchant_normalized`; sets `resolved_at = today`; redirects to `/recurring`
- [x] 3.3 Add `POST /recurring/cancel/delete` — accepts `merchant_normalized`; deletes the record; redirects to `/recurring`

## 4. Routing / Template Data

- [x] 4.1 In the `/recurring` route, ensure zombie merchants (cancel_attempt.is_zombie=True and resolved_at=None) are included in the `attention` list regardless of their `status`
- [x] 4.2 Pass `include_housing`, `include_education`, `include_health` as query params through the redirect URLs in the new POST endpoints so filters are preserved after form submission

## 5. Template UI

- [x] 5.1 Add a cancel tracking column (or inline action area) to all three table sections in `finance/web/templates/recurring.html`
- [x] 5.2 Render "Track Cancel" inline form (collapsed by default, toggled by button) for merchants with `cancel_attempt = None`; form POSTs to `/recurring/cancel` with hidden `merchant_normalized` + `attempted_at` date input + optional `notes` textarea
- [x] 5.3 Render amber "Cancel attempted {date}" badge + Resolve and Remove buttons for pending non-zombie attempts
- [x] 5.4 Render red "Zombie — still charging!" badge + Resolve and Remove buttons for zombie merchants; apply red row tint / left border
- [x] 5.5 Render green "Cancelled {resolved_at}" badge + Remove button for resolved attempts
- [x] 5.6 Ensure zombie merchants displayed in the Needs Attention section have the zombie badge and distinct row styling
