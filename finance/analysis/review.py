"""Analysis queries for review queue and recurring charge detection."""

from __future__ import annotations

import sqlite3


def get_review_queue(conn: sqlite3.Connection) -> list[dict]:
    """Return all transactions flagged for human review.

    Returns rows where ``needs_review = 1``, ordered by ``date DESC``.

    Each returned dict has keys:
        id, date, amount, description, merchant_name, merchant_normalized,
        category, review_reason, account_id
    """
    rows = conn.execute(
        """
        SELECT
            id,
            date,
            amount,
            description,
            merchant_name,
            merchant_normalized,
            category,
            review_reason,
            account_id
        FROM transactions
        WHERE needs_review = 1
        ORDER BY date DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_recurring(conn: sqlite3.Connection) -> list[dict]:
    """Return a summary of detected recurring merchant charges.

    Groups transactions by ``merchant_normalized`` where ``is_recurring = 1``.
    Computes ``count`` (number of transactions) and ``typical_amount`` (median
    of absolute amounts).

    Returns rows ordered by ``count DESC``.

    Each returned dict has keys:
        merchant_normalized, count, typical_amount
    """
    rows = conn.execute(
        """
        SELECT
            merchant_normalized,
            amount
        FROM transactions
        WHERE is_recurring = 1
          AND merchant_normalized IS NOT NULL
          AND merchant_normalized != ''
        ORDER BY merchant_normalized
        """
    ).fetchall()

    if not rows:
        return []

    # Group amounts by merchant and compute median
    from collections import defaultdict

    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row["amount"] is not None:
            groups[row["merchant_normalized"]].append(abs(row["amount"]))

    result = []
    for merchant, amounts in groups.items():
        sorted_amounts = sorted(amounts)
        mid = len(sorted_amounts) // 2
        if len(sorted_amounts) % 2 == 1:
            typical = sorted_amounts[mid]
        else:
            typical = (sorted_amounts[mid - 1] + sorted_amounts[mid]) / 2.0
        result.append(
            {
                "merchant_normalized": merchant,
                "count": len(amounts),
                "typical_amount": round(typical, 2),
            }
        )

    result.sort(key=lambda x: x["count"], reverse=True)
    return result
