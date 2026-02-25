"""Analysis functions for accounts and credit utilization."""

import sqlite3
import time


def get_accounts(conn: sqlite3.Connection) -> list[dict]:
    """Return all active accounts with their most recent balance snapshot.

    Uses a LEFT JOIN with a subquery for the MAX timestamp per account so that
    accounts with no balance rows are still returned (balance=None).

    Args:
        conn: An open SQLite connection with row_factory set.

    Returns:
        List of dicts with keys:
            id, name, type, institution, balance, available, currency, mask, last_updated
    """
    rows = conn.execute(
        """
        SELECT
            a.id,
            a.name,
            a.type,
            i.name  AS institution,
            b.balance,
            b.available,
            a.currency,
            a.mask,
            b.timestamp AS last_updated
        FROM accounts a
        LEFT JOIN institutions i ON a.institution_id = i.id
        LEFT JOIN (
            SELECT account_id, balance, available, timestamp
            FROM balances
            WHERE id IN (
                SELECT MAX(id) FROM balances GROUP BY account_id
            )
        ) b ON b.account_id = a.id
        WHERE a.active = 1
        ORDER BY a.name
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_account_by_id(conn: sqlite3.Connection, account_id: str) -> dict | None:
    """Return a single active account with its most recent balance, or None.

    Args:
        conn: An open SQLite connection with row_factory set.
        account_id: The account primary key.

    Returns:
        Dict with account fields, or None if not found.
    """
    row = conn.execute(
        """
        SELECT
            a.id,
            a.name,
            a.type,
            i.name  AS institution,
            b.balance,
            b.available,
            a.currency,
            a.mask,
            b.timestamp AS last_updated
        FROM accounts a
        LEFT JOIN institutions i ON a.institution_id = i.id
        LEFT JOIN (
            SELECT account_id, balance, available, timestamp
            FROM balances
            WHERE id IN (
                SELECT MAX(id) FROM balances GROUP BY account_id
            )
        ) b ON b.account_id = a.id
        WHERE a.active = 1 AND a.id = ?
        """,
        (account_id,),
    ).fetchone()
    return dict(row) if row else None


def get_credit_utilization(conn: sqlite3.Connection) -> dict:
    """Return per-card and aggregate credit utilization.

    Joins active credit accounts with their latest balance snapshot and any
    configured limit from credit_limits. Cards without a configured limit have
    utilization_pct=None.

    Args:
        conn: An open SQLite connection with row_factory set.

    Returns:
        Dict with keys:
            aggregate_pct   -- null if no cards have configured limits
            total_balance   -- sum of abs(balance) for all credit cards
            total_limit     -- sum of configured limits (null if none configured)
            cards           -- list of {account_id, name, balance, limit, utilization_pct}
    """
    rows = conn.execute(
        """
        SELECT
            a.id        AS account_id,
            a.name,
            b.balance,
            cl.credit_limit AS "limit"
        FROM accounts a
        LEFT JOIN (
            SELECT account_id, balance, available, timestamp
            FROM balances
            WHERE id IN (
                SELECT MAX(id) FROM balances GROUP BY account_id
            )
        ) b ON b.account_id = a.id
        LEFT JOIN credit_limits cl ON cl.account_id = a.id
        WHERE a.active = 1 AND a.type = 'credit'
        ORDER BY a.name
        """
    ).fetchall()

    cards = []
    total_balance = 0.0
    total_limit_sum = 0.0
    any_limit = False

    for r in rows:
        balance = r["balance"] if r["balance"] is not None else 0.0
        limit = r["limit"]
        abs_balance = abs(balance)
        total_balance += abs_balance

        if limit is not None:
            utilization_pct = abs_balance / limit * 100
            total_limit_sum += limit
            any_limit = True
        else:
            utilization_pct = None

        cards.append(
            {
                "account_id": r["account_id"],
                "name": r["name"],
                "balance": balance,
                "limit": limit,
                "utilization_pct": utilization_pct,
            }
        )

    total_limit = total_limit_sum if any_limit else None
    if any_limit and total_limit_sum > 0:
        # Only include cards with limits in aggregate calculation
        cards_with_limits = [c for c in cards if c["limit"] is not None]
        bal_sum = sum(abs(c["balance"]) for c in cards_with_limits)
        aggregate_pct = bal_sum / total_limit_sum * 100
    else:
        aggregate_pct = None

    return {
        "aggregate_pct": aggregate_pct,
        "total_balance": total_balance,
        "total_limit": total_limit,
        "cards": cards,
    }
