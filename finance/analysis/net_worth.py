"""Analysis functions for net worth and balance history."""

import sqlite3
from datetime import datetime, timezone

_ASSET_TYPES = {"checking", "savings", "investment"}
_LIABILITY_TYPES = {"credit", "loan"}


def get_net_worth(
    conn: sqlite3.Connection,
    as_of_date: str | None = None,
) -> dict:
    """Return net worth broken down by account type.

    For each active account, finds the most recent balance snapshot on or before
    as_of_date (or the absolute latest if as_of_date is None).

    Asset types: checking, savings, investment
    Liability types: credit, loan  (their balances are typically negative;
        abs(balance) is counted as a liability)

    Args:
        conn: An open SQLite connection with row_factory set.
        as_of_date: Optional date string (YYYY-MM-DD). If provided, only balance
            snapshots with timestamp <= midnight UTC of that date are considered.

    Returns:
        Dict with keys:
            total        -- net worth (assets - liabilities)
            assets       -- sum of positive-side balances
            liabilities  -- sum of abs(balance) for liability accounts
            by_type      -- {checking, savings, investment, credit, loan}
                            each value is the sum for that type (raw balance)
            as_of        -- ISO-8601 timestamp of the data point used (or null)
    """
    # Convert as_of_date to a unix-ms upper bound if given
    if as_of_date is not None:
        # End of day in UTC for the given date
        cutoff_dt = datetime.strptime(as_of_date + "T23:59:59", "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=timezone.utc
        )
        cutoff_ms = int(cutoff_dt.timestamp() * 1000)
        timestamp_filter = "AND b.timestamp <= :cutoff"
        params: dict = {"cutoff": cutoff_ms}
    else:
        timestamp_filter = ""
        params = {}

    rows = conn.execute(
        f"""
        SELECT
            a.type,
            b.balance,
            b.timestamp
        FROM accounts a
        JOIN (
            SELECT account_id, balance, timestamp
            FROM balances b_inner
            WHERE b_inner.id = (
                SELECT MAX(b2.id)
                FROM balances b2
                WHERE b2.account_id = b_inner.account_id
                {timestamp_filter}
            )
        ) b ON b.account_id = a.id
        WHERE a.active = 1
        """,
        params,
    ).fetchall()

    by_type: dict[str, float] = {
        "checking": 0.0,
        "savings": 0.0,
        "investment": 0.0,
        "credit": 0.0,
        "loan": 0.0,
    }
    assets = 0.0
    liabilities = 0.0
    latest_ts: int | None = None

    for row in rows:
        acct_type = row["type"] or "other"
        balance = row["balance"] if row["balance"] is not None else 0.0
        ts = row["timestamp"]

        if ts is not None and (latest_ts is None or ts > latest_ts):
            latest_ts = ts

        if acct_type in by_type:
            by_type[acct_type] += balance

        if acct_type in _ASSET_TYPES:
            assets += balance
        elif acct_type in _LIABILITY_TYPES:
            liabilities += abs(balance)
        else:
            # Unknown type: use balance sign as heuristic
            # (SimpleFIN convention: negative = owed/debit, positive = owned/credit)
            if balance >= 0:
                assets += balance
            else:
                liabilities += abs(balance)

    total = assets - liabilities

    # Convert latest_ts (unix ms) to ISO string
    if latest_ts is not None:
        as_of_str = datetime.fromtimestamp(latest_ts / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    else:
        as_of_str = None

    return {
        "total": round(total, 2),
        "assets": round(assets, 2),
        "liabilities": round(liabilities, 2),
        "by_type": {k: round(v, 2) for k, v in by_type.items()},
        "as_of": as_of_str,
    }


def get_balance_history(
    conn: sqlite3.Connection,
    account_id: str | None = None,
) -> list[dict]:
    """Return all balance snapshots, optionally filtered by account.

    Args:
        conn: An open SQLite connection with row_factory set.
        account_id: Optional account to filter to. If None, returns all.

    Returns:
        List of dicts with keys: id, account_id, timestamp, balance, available.
        Ordered by timestamp ASC.
    """
    if account_id is not None:
        rows = conn.execute(
            """
            SELECT id, account_id, timestamp, balance, available
            FROM balances
            WHERE account_id = ?
            ORDER BY timestamp ASC
            """,
            (account_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT id, account_id, timestamp, balance, available
            FROM balances
            ORDER BY timestamp ASC
            """
        ).fetchall()

    return [dict(r) for r in rows]
