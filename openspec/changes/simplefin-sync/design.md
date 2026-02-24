## Context

SimpleFIN Bridge is the primary data source. It returns account metadata, current balances, and recent transactions from a single `/accounts` endpoint. The auth flow is a one-time setup (claim a setup token → receive a persistent access URL). After setup, sync is a single authenticated GET request.

This change builds on `project-foundation` (DB schema, `get_connection()` are already in place).

## Goals / Non-Goals

**Goals:**
- Complete SimpleFIN auth flow (claim setup token → store access URL)
- Fetch and upsert accounts, balance snapshots, and transactions
- `finance sync` CLI command for manual and cron-driven execution
- Graceful handling of unsupported/empty accounts

**Non-Goals:**
- CSV import (that's `csv-import`)
- Transaction categorization (that's `ai-categorize`)
- Scheduled/automatic sync — caller's responsibility (cron, launchd, etc.)
- Retry logic for transient network failures

## Decisions

### D1: Raw httpx, not the simplefin Python client library

**Decision:** Implement the SimpleFIN client using `httpx` directly rather than any third-party SimpleFIN wrapper.

**Rationale:** The SimpleFIN API is trivial — one endpoint, HTTP basic auth, JSON response. Adding a dependency for this would be worse than 50 lines of httpx code. Avoids dependency drift.

**Alternatives considered:** `simplefin-python` library — rejected, unnecessary abstraction.

---

### D2: Access URL stored in `.env`, not the database

**Decision:** `SIMPLEFIN_ACCESS_URL` lives in the `.env` file, loaded at runtime via `python-dotenv`.

**Rationale:** The access URL is a credential, not data. It belongs with other credentials (API keys) in `.env`. Storing it in the DB adds complexity and creates a chicken-and-egg problem (need DB to bootstrap the DB sync).

---

### D3: Sync window — `last_synced_at` or 90-day fallback

**Decision:** For each account, fetch transactions starting from `sync_state.last_synced_at` if available, otherwise from 90 days ago (first sync window).

**Rationale:** SimpleFIN accepts `start-date` and `end-date` as query parameters (unix seconds). Using last sync time avoids redundant re-fetching of already-ingested transactions. 90-day default provides useful historical context on first run without fetching too much.

---

### D4: Synchronous HTTP (not async)

**Decision:** Use `httpx` in synchronous mode (not `httpx.AsyncClient`).

**Rationale:** The sync operation runs once per day, touches one endpoint, and takes under a second. There's no concurrency benefit from async here. Synchronous code is simpler to reason about and test.

---

### D5: Balance snapshots always appended, transactions INSERT OR IGNORE

**Decision:**
- Balances: always `INSERT` a new row (append-only time series)
- Transactions: `INSERT OR IGNORE` (primary key deduplication on `id`)

**Rationale:** Balances are a time series — each sync is a new data point, never an update. Transactions are idempotent — re-running sync should never duplicate. The `raw` column preserves the original response for reprocessing.

---

### D6: SimpleFIN timestamps are unix seconds → store as unix ms

**Decision:** Convert SimpleFIN `balance-date` (unix seconds) to unix ms when writing to `balances.timestamp`.

**Rationale:** The DB schema uses unix ms consistently across all timestamp columns. Converting at the boundary keeps the rest of the codebase uniform.

---

### D7: Institution upsert uses `INSERT OR REPLACE`

**Decision:** Upsert institutions with `INSERT OR REPLACE INTO institutions` so institution name/url updates are picked up on re-sync.

**Rationale:** Institution metadata (name, URL) can change. Unlike transactions (which must never change once stored), institutions are safe to overwrite.

## Risks / Trade-offs

- **SimpleFIN coverage uncertainty** → Some accounts may not be supported. The sync will simply not return them. User verifies coverage empirically by running `finance sync` and checking `finance accounts`.
- **90-day first-sync window** → Transactions older than 90 days won't be captured by SimpleFIN sync. Historical data requires CSV import.
- **No retry logic** → A failed sync leaves `last_synced_at` unchanged, so the next manual run will re-fetch the same window. Acceptable for a daily manual/cron operation.

## Open Questions

None — all decisions resolved.
