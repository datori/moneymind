"""Database upsert helpers for SimpleFIN ingestion."""

import json
import sqlite3
import time
from datetime import date, timezone, datetime


def upsert_institution(conn: sqlite3.Connection, org: dict) -> str:
    """Upsert an institution row from a SimpleFIN org dict.

    The institution id is derived from the org domain (or sfin-url as fallback).

    Args:
        conn: SQLite connection.
        org:  The ``org`` sub-dict from a SimpleFIN account response, e.g.
              ``{"domain": "chase.com", "name": "Chase", "sfin-url": "..."}``.

    Returns:
        The institution id (TEXT primary key).
    """
    institution_id: str = org.get("domain") or org.get("sfin-url", "unknown")
    name: str = org.get("name", institution_id)
    url: str | None = org.get("sfin-url") or org.get("domain")

    conn.execute(
        """
        INSERT OR REPLACE INTO institutions (id, name, url, source)
        VALUES (?, ?, ?, 'simplefin')
        """,
        (institution_id, name, url),
    )
    return institution_id


def upsert_account(
    conn: sqlite3.Connection, account: dict, institution_id: str
) -> str:
    """Upsert an account row from a SimpleFIN account dict.

    Args:
        conn:           SQLite connection.
        account:        A single account entry from the SimpleFIN response.
        institution_id: The id of the already-upserted institution.

    Returns:
        The account id (TEXT primary key).
    """
    account_id: str = account["id"]
    name: str = account.get("name", account_id)
    currency: str = account.get("currency", "USD")

    conn.execute(
        """
        INSERT OR REPLACE INTO accounts
            (id, institution_id, name, currency, active)
        VALUES (?, ?, ?, ?, 1)
        """,
        (account_id, institution_id, name, currency),
    )
    return account_id


def insert_balance_snapshot(
    conn: sqlite3.Connection,
    account_id: str,
    balance: float,
    available: float | None,
    timestamp_s: int,
) -> None:
    """Append a balance snapshot to the balances table.

    Args:
        conn:        SQLite connection.
        account_id:  Account primary key.
        balance:     Current balance (from SimpleFIN ``balance`` field).
        available:   Available balance (may be None).
        timestamp_s: Unix timestamp in *seconds* (SimpleFIN ``balance-date``).
                     Converted to milliseconds before storing.
    """
    timestamp_ms: int = timestamp_s * 1000
    conn.execute(
        """
        INSERT OR IGNORE INTO balances (account_id, timestamp, balance, available)
        VALUES (?, ?, ?, ?)
        """,
        (account_id, timestamp_ms, balance, available),
    )


def upsert_transactions(
    conn: sqlite3.Connection,
    account_id: str,
    transactions: list[dict],
) -> int:
    """Insert new transactions, skipping any that already exist (by id).

    Args:
        conn:         SQLite connection.
        account_id:   Account primary key.
        transactions: List of transaction dicts from the SimpleFIN response.

    Returns:
        The number of newly inserted rows.
    """
    inserted = 0
    for txn in transactions:
        txn_id: str = txn["id"]
        # Convert unix seconds → YYYY-MM-DD
        posted_s: int = txn.get("posted", 0)
        txn_date: str = datetime.fromtimestamp(posted_s, tz=timezone.utc).strftime(
            "%Y-%m-%d"
        )
        amount: float = float(txn.get("amount", 0))
        description: str | None = txn.get("description")
        raw: str = json.dumps(txn)

        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO transactions
                (id, account_id, date, amount, description, source, raw)
            VALUES (?, ?, ?, ?, ?, 'simplefin', ?)
            """,
            (txn_id, account_id, txn_date, amount, description, raw),
        )
        inserted += cursor.rowcount
    return inserted


def update_sync_state(conn: sqlite3.Connection, account_id: str) -> None:
    """Record the current time as the last sync timestamp for an account.

    Args:
        conn:       SQLite connection.
        account_id: Account primary key.
    """
    now_ms: int = int(time.time() * 1000)
    conn.execute(
        """
        INSERT OR REPLACE INTO sync_state (account_id, last_synced_at)
        VALUES (?, ?)
        """,
        (account_id, now_ms),
    )
