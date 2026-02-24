"""Analysis functions for data coverage overview."""

import sqlite3


def get_data_overview(conn: sqlite3.Connection) -> dict:
    """Return global and per-account transaction coverage stats.

    Queries active accounts LEFT JOIN transactions, sync_state, balances, and
    institutions in a single round-trip. Accounts with no transactions are
    included with null date fields and zero counts.

    Args:
        conn: An open SQLite connection with row_factory set.

    Returns:
        Dict with two keys:
            global: {
                total_accounts        -- int, number of active accounts
                total_transactions    -- int, total transactions across all active accounts
                total_balances        -- int, total balance snapshots
                earliest_transaction  -- str YYYY-MM-DD or null
                latest_transaction    -- str YYYY-MM-DD or null
            }
            per_account: list of {
                account_id    -- str
                name          -- str
                institution   -- str or null
                txn_count     -- int
                earliest_txn  -- str YYYY-MM-DD or null
                latest_txn    -- str YYYY-MM-DD or null
                last_balance  -- float or null
                last_synced_at -- int unix-ms or null
            }
    """
    rows = conn.execute(
        """
        SELECT
            a.id                    AS account_id,
            a.name                  AS name,
            i.name                  AS institution,
            COUNT(t.id)             AS txn_count,
            MIN(t.date)             AS earliest_txn,
            MAX(t.date)             AS latest_txn,
            b.balance               AS last_balance,
            ss.last_synced_at       AS last_synced_at
        FROM accounts a
        LEFT JOIN institutions i ON a.institution_id = i.id
        LEFT JOIN transactions t ON t.account_id = a.id
        LEFT JOIN (
            SELECT account_id, balance
            FROM balances
            WHERE (account_id, timestamp) IN (
                SELECT account_id, MAX(timestamp)
                FROM balances
                GROUP BY account_id
            )
        ) b ON b.account_id = a.id
        LEFT JOIN sync_state ss ON ss.account_id = a.id
        WHERE a.active = 1
        GROUP BY a.id, a.name, i.name, b.balance, ss.last_synced_at
        ORDER BY a.name
        """
    ).fetchall()

    per_account = []
    for r in rows:
        per_account.append(
            {
                "account_id": r["account_id"],
                "name": r["name"],
                "institution": r["institution"],
                "txn_count": r["txn_count"] or 0,
                "earliest_txn": r["earliest_txn"],
                "latest_txn": r["latest_txn"],
                "last_balance": r["last_balance"],
                "last_synced_at": r["last_synced_at"],
            }
        )

    # Aggregate global stats from per-account data and one extra query for balances
    total_accounts = len(per_account)
    total_transactions = sum(a["txn_count"] for a in per_account)
    earliest = min((a["earliest_txn"] for a in per_account if a["earliest_txn"]), default=None)
    latest = max((a["latest_txn"] for a in per_account if a["latest_txn"]), default=None)

    total_balances_row = conn.execute("SELECT COUNT(*) AS cnt FROM balances").fetchone()
    total_balances = total_balances_row["cnt"] if total_balances_row else 0

    return {
        "global": {
            "total_accounts": total_accounts,
            "total_transactions": total_transactions,
            "total_balances": total_balances,
            "earliest_transaction": earliest,
            "latest_transaction": latest,
        },
        "per_account": per_account,
    }
