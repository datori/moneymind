## Context

The CSV import pipeline uses content-hash IDs (`sha256(account_id|date|amount|description)[:16]`) while SimpleFIN uses bank-assigned opaque IDs. These two namespaces never collide, so `INSERT OR IGNORE` deduplication works perfectly *within* a single source but cannot detect cross-source duplicates for the same real-world transaction.

When a user does a one-time historical backfill (full bank CSV export covering years of data), the recent ~90 days already covered by SimpleFIN will produce duplicate rows unless we filter by date.

## Goals / Non-Goals

**Goals:**
- Allow safe historical CSV import into SimpleFIN-linked accounts without creating duplicates
- Auto-detect the safe cutoff date from existing data (zero config for typical case)
- Give users explicit override via `--before DATE` flag when needed
- Surface cutoff behavior clearly in import summary output

**Non-Goals:**
- Retroactive deduplication of already-imported duplicate rows
- Merging/reconciling CSV rows with existing SimpleFIN rows for the same transaction
- Cross-source fuzzy matching (date + amount similarity checks) — too many edge cases with identical-amount same-day transactions

## Decisions

### Decision: Temporal partitioning over fuzzy dedup

**Choice**: Filter rows by date cutoff rather than attempting fuzzy match on `(date, amount)`.

**Rationale**: Fuzzy matching on `(date, amount)` fails silently for legitimate duplicates — e.g., two $4.50 coffee purchases on the same day. A date cutoff is deterministic, auditable, and communicates clearly to the user what was imported and what was excluded.

**Alternative considered**: `(date, amount, description[:N])` match. Rejected because description text often differs between CSV and SimpleFIN (bank abbreviations vs. MX-normalized names).

---

### Decision: Auto-detect cutoff from `MIN(date)` of SimpleFIN transactions

**Choice**: When `--before` is omitted, query `MIN(date) FROM transactions WHERE account_id = ? AND source = 'simplefin'` and use that as the cutoff.

**Rationale**: This is the earliest date SimpleFIN has data for the account — anything on or after that date risks duplication. The user doesn't need to know or remember when they set up SimpleFIN.

**Fallback**: If no SimpleFIN transactions exist for the account (pure CSV account), `before_date` is `None` and all rows are imported — preserving existing behavior exactly.

---

### Decision: Cutoff is exclusive (`date < before_date`)

**Choice**: Skip rows where `date >= before_date` (cutoff date is excluded from import).

**Rationale**: SimpleFIN's initial sync starts from `MIN(date)`, so that date already has SimpleFIN coverage. Using an exclusive cutoff avoids any boundary-day ambiguity.

---

### Decision: `before_date` as `YYYY-MM-DD` string throughout

**Choice**: Pass and compare as ISO date strings rather than converting to timestamps.

**Rationale**: All transaction dates are stored as `YYYY-MM-DD` strings. String comparison is correct and avoids timezone conversion complexity.

## Risks / Trade-offs

- **Gap risk**: If SimpleFIN's initial pull didn't go the full 90 days back (some banks only provide 60), there may be a small unimported gap between CSV cutoff and oldest SimpleFIN transaction. Acceptable — the user can override with `--before` to an earlier date if needed.
- **Pending transactions**: Pending SimpleFIN transactions that later settle may have a slightly different date in the CSV. Very unlikely to fall exactly on the cutoff boundary; not worth special-casing.
- **No retroactive fix**: Users who already imported a full CSV into a SimpleFIN account before this feature existed will have duplicates. Out of scope for this change.

## Migration Plan

No schema changes. No data migration. The change is purely additive:
- New optional parameter in `import_csv()`
- New optional CLI flag `--before`
- Default behavior (no flag, no SimpleFIN data) is identical to current behavior
