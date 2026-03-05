## Context

The recurring page currently shows `status = "likely_cancelled"` for merchants that have gone quiet, but there's no way to record *user intent* — that the user actually tried to cancel a subscription. Without this, there's no way to detect zombie subscriptions (services still charging after a supposed cancellation) or to confirm that a cancellation succeeded.

The `category_corrections` table (in-flight change) establishes the pattern: per-merchant metadata stored in a separate table, decoupled from transaction rows, persisting across pipeline runs.

## Goals / Non-Goals

**Goals:**
- Persist a cancel attempt per merchant (date + optional notes) that survives syncs and pipeline re-runs
- Derive zombie status at read time: any charge after `attempted_at` = zombie
- Expose CRUD endpoints for the web UI to create, resolve, and delete cancel attempts
- Surface cancel state per merchant on the recurring page with distinct visual treatment for zombies
- Elevate zombie merchants in the Needs Attention section

**Non-Goals:**
- Cancel attempt history (multiple attempts per merchant — one record is enough)
- Auto-resolve when `likely_cancelled` is detected (user resolves manually)
- "Want to cancel someday" wishlist
- Any interaction with the pipeline or LLM enrichment

## Decisions

### 1. Separate `recurring_cancel_attempts` table, not a column on transactions

**Decision**: New table keyed by `merchant_normalized`.

**Rationale**: Cancel intent is user metadata, not transaction data. It should persist even if all transactions for that merchant are deleted or re-imported. Storing it on the transactions table would scatter intent across many rows and require reconciliation. A single-row-per-merchant table is clean, queryable, and easy to migrate.

**Alternative considered**: A column `cancel_attempted_at` on the transactions table — rejected because it would require updating every transaction for a merchant and is fragile to re-ingestion.

### 2. Zombie detection derived at read time

**Decision**: `is_zombie = (last_date > attempted_at) AND (resolved_at IS NULL)`, computed in `get_recurring()`.

**Rationale**: No grace period needed (any post-cancel charge is a signal). Computing it in Python during `get_recurring()` keeps it with the rest of the enrichment logic and avoids a stored flag that could go stale.

### 3. CRUD via form POSTs (not fetch/XHR)

**Decision**: Standard HTML form submissions with redirect-after-POST (PRG pattern).

**Rationale**: Consistent with the existing web UI (no JS fetch calls elsewhere in the app). Each action is a POST endpoint that redirects back to `/recurring` with query params preserved.

**Endpoints**:
- `POST /recurring/cancel` — body: `merchant_normalized`, `attempted_at`, `notes` → upsert, redirect
- `POST /recurring/cancel/resolve` — body: `merchant_normalized` → set `resolved_at = today`, redirect
- `POST /recurring/cancel/delete` — body: `merchant_normalized` → delete row, redirect

No GET endpoint needed — the form state is rendered inline on the recurring page from the enriched `get_recurring()` data.

### 4. Cancel state embedded in `get_recurring()` output

**Decision**: Add a `cancel_attempt` key to each merchant dict (value: dict or `None`).

```python
"cancel_attempt": {
    "attempted_at": "2026-03-01",
    "notes": "Called support",
    "resolved_at": None,
    "is_zombie": True,   # last_date > attempted_at and resolved_at is None
} | None
```

**Rationale**: The recurring page already consumes `get_recurring()` output. Embedding cancel state there avoids a second query in the route and keeps the data co-located with the merchant's interval/status data.

### 5. Zombie merchants surfaced in Needs Attention

**Decision**: Zombie merchants (is_zombie=True, resolved_at=None) are included in the `attention` list server-side, regardless of their `status` value.

**Rationale**: A zombie is the highest-priority action a user needs to take — a service is charging after they tried to stop it. It belongs in Needs Attention even if the recurring analysis still shows it as "upcoming" (because the charges are still arriving on schedule from the merchant's perspective).

**Row treatment**: Red border (`border-red-500`) + distinct "Zombie" badge in the status cell.

## Risks / Trade-offs

- **`merchant_normalized` instability**: If normalization changes (e.g., after pipeline re-run), a cancel attempt may be orphaned. Low risk — normalization is stable once set; worst case the record just doesn't display.
- **Zombie false positive on final billing cycle**: If the user cancelled mid-cycle, one more charge may arrive. This is intentionally accepted — no grace period was the explicit decision. User can manually mark as resolved.
- **One attempt per merchant**: A user who cancels, re-subscribes, and cancels again will overwrite the first record. Acceptable for personal use.

## Migration Plan

1. Add `recurring_cancel_attempts` table to `_SCHEMA` constant in `db.py`
2. Add a `CREATE TABLE IF NOT EXISTS` migration call in `init_db()` (idempotent — same pattern as existing migrations)
3. No data migration needed — table starts empty
