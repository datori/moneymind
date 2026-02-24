"""Sync orchestration: ties SimpleFIN client to DB upsert helpers."""

import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone

from finance.ingestion.simplefin import SimpleFINClient
from finance.ingestion.store import (
    insert_balance_snapshot,
    update_sync_state,
    upsert_account,
    upsert_institution,
    upsert_transactions,
)

_90_DAYS_S = 90 * 24 * 60 * 60  # 90 days expressed in seconds

logger = logging.getLogger(__name__)


def _get_last_synced_at_s(conn: sqlite3.Connection, account_id: str) -> int | None:
    """Return last_synced_at for *account_id* in unix **seconds**, or None."""
    row = conn.execute(
        "SELECT last_synced_at FROM sync_state WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    if row is None or row["last_synced_at"] is None:
        return None
    # DB stores ms; convert to seconds for SimpleFIN query param
    return row["last_synced_at"] // 1000


def sync_all(conn: sqlite3.Connection) -> dict:
    """Orchestrate a full SimpleFIN sync.

    For each account returned by SimpleFIN:
    - Upserts the institution and account rows.
    - Appends a balance snapshot.
    - Inserts any new transactions (existing IDs are silently skipped).
    - Updates sync_state with the current timestamp.

    The transaction window for each account is determined by its
    ``sync_state.last_synced_at`` value:
    - If present: fetch from that timestamp onwards (subsequent sync).
    - If absent:  fetch from 90 days ago (first sync).

    Accounts that return an empty ``transactions`` list are handled
    gracefully — balance snapshots are still recorded.

    Args:
        conn: An open SQLite connection (with WAL mode and row_factory set).

    Returns:
        A dict with keys:
        - ``accounts_updated``  (int)
        - ``new_transactions``  (int)
        - ``synced_at``         (str, ISO-8601 UTC)
    """
    client = SimpleFINClient()

    now_s = int(time.time())
    default_start_s = now_s - _90_DAYS_S

    accounts_updated = 0
    new_transactions = 0

    # Determine a global start_date covering all accounts: use the earliest
    # last_synced_at across all known accounts so a single API call suffices,
    # then we track per-account dedup via INSERT OR IGNORE on transaction ids.
    # SimpleFIN returns a unified /accounts response, so we pass the minimum
    # start-date across all accounts (or 90 days ago if any account is new).
    #
    # Implementation note: we make one API call with the global minimum
    # start_date and rely on INSERT OR IGNORE for already-seen transactions.
    # This is simpler than making one call per account.

    # First, peek at known accounts to compute global window start.
    known_rows = conn.execute("SELECT account_id, last_synced_at FROM sync_state").fetchall()
    known_synced: dict[str, int | None] = {
        r["account_id"]: (r["last_synced_at"] // 1000 if r["last_synced_at"] else None)
        for r in known_rows
    }

    # If any account has never been synced (or we have no state at all), fall
    # back to the 90-day window for the global request.
    if not known_synced or any(v is None for v in known_synced.values()):
        global_start_s = default_start_s
    else:
        global_start_s = min(known_synced.values())  # type: ignore[type-var]

    data = client.fetch_accounts(start_date=global_start_s)

    for account in data.get("accounts", []):
        org = account.get("org", {})
        institution_id = upsert_institution(conn, org)
        account_id = upsert_account(conn, account, institution_id)

        # Balance snapshot — always append
        balance_raw = account.get("balance")
        available_raw = account.get("available-balance")
        balance_date_s: int = account.get("balance-date", now_s)

        if balance_raw is not None:
            insert_balance_snapshot(
                conn,
                account_id=account_id,
                balance=float(balance_raw),
                available=float(available_raw) if available_raw is not None else None,
                timestamp_s=balance_date_s,
            )

        # Transactions — gracefully handle empty list (balance-only accounts)
        transactions: list[dict] = account.get("transactions") or []
        new_transactions += upsert_transactions(conn, account_id, transactions)

        update_sync_state(conn, account_id)
        accounts_updated += 1

    conn.commit()

    # Auto-categorize new transactions if ANTHROPIC_API_KEY is available.
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from finance.ai.categorize import categorize_uncategorized

            categorize_uncategorized(conn)
        except Exception as exc:
            logger.warning("Auto-categorization after sync failed (sync still succeeded): %s", exc)

    synced_at = datetime.fromtimestamp(now_s, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    return {
        "accounts_updated": accounts_updated,
        "new_transactions": new_transactions,
        "synced_at": synced_at,
    }
