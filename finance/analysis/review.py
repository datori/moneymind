"""Analysis queries for review queue and recurring charge detection."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta


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
    """Return an enriched summary of detected recurring merchant charges.

    Groups transactions by ``merchant_normalized`` where ``is_recurring = 1``.
    Derives interval, next-due date, status, and total spent from transaction
    history — no schema changes required.

    Each returned dict has keys:
        merchant_normalized, count, typical_amount, total_spent,
        last_date, interval_days, interval_label,
        next_due_date, days_until_next, status

    Status values: "upcoming", "due_soon", "due_any_day", "past_due", None.
    Results are sorted by urgency (past_due first, then due_any_day, due_soon,
    upcoming, then None).
    """
    rows = conn.execute(
        """
        SELECT
            merchant_normalized,
            date,
            amount
        FROM transactions
        WHERE is_recurring = 1
          AND merchant_normalized IS NOT NULL
          AND merchant_normalized != ''
        ORDER BY merchant_normalized, date
        """
    ).fetchall()

    if not rows:
        return []

    from collections import defaultdict

    groups: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in rows:
        if row["amount"] is not None and row["date"] is not None:
            groups[row["merchant_normalized"]].append((row["date"], abs(row["amount"])))

    today = date.today()
    result = []

    for merchant, entries in groups.items():
        dates = sorted(e[0] for e in entries)
        amounts = [e[1] for e in entries]

        # Typical amount: median
        sorted_amounts = sorted(amounts)
        mid = len(sorted_amounts) // 2
        if len(sorted_amounts) % 2 == 1:
            typical = sorted_amounts[mid]
        else:
            typical = (sorted_amounts[mid - 1] + sorted_amounts[mid]) / 2.0

        total_spent = round(sum(amounts), 2)
        last_date = dates[-1]

        # Interval: median gap between consecutive charges
        interval_days: int | None = None
        interval_label: str | None = None
        next_due_date: str | None = None
        days_until_next: int | None = None
        status: str | None = None

        if len(dates) >= 2:
            date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
            gaps = [(date_objs[i + 1] - date_objs[i]).days for i in range(len(date_objs) - 1)]
            gaps_sorted = sorted(gaps)
            gmid = len(gaps_sorted) // 2
            if len(gaps_sorted) % 2 == 1:
                median_gap = gaps_sorted[gmid]
            else:
                median_gap = (gaps_sorted[gmid - 1] + gaps_sorted[gmid]) // 2
            interval_days = max(1, median_gap)

            # Classify interval
            g = interval_days
            if 5 <= g <= 9:
                interval_label = "Weekly"
            elif 13 <= g <= 17:
                interval_label = "Bi-weekly"
            elif 25 <= g <= 35:
                interval_label = "Monthly"
            elif 85 <= g <= 95:
                interval_label = "Quarterly"
            elif 175 <= g <= 190:
                interval_label = "Semi-annual"
            elif 355 <= g <= 375:
                interval_label = "Annual"
            else:
                interval_label = f"Every ~{g}d"

            last_date_obj = datetime.strptime(last_date, "%Y-%m-%d").date()
            next_due_obj = last_date_obj + timedelta(days=interval_days)
            next_due_date = next_due_obj.isoformat()
            days_until_next = (next_due_obj - today).days

            tolerance = max(3, int(interval_days * 0.35))
            if days_until_next > 7:
                status = "upcoming"
            elif 1 <= days_until_next <= 7:
                status = "due_soon"
            elif -tolerance <= days_until_next <= 0:
                status = "due_any_day"
            else:
                status = "past_due"

        result.append(
            {
                "merchant_normalized": merchant,
                "count": len(amounts),
                "typical_amount": round(typical, 2),
                "total_spent": total_spent,
                "last_date": last_date,
                "interval_days": interval_days,
                "interval_label": interval_label,
                "next_due_date": next_due_date,
                "days_until_next": days_until_next,
                "status": status,
            }
        )

    # Sort by urgency
    def _urgency_key(item: dict) -> tuple:
        s = item["status"]
        d = item["days_until_next"]
        if s == "past_due":
            return (0, d if d is not None else 0)      # most overdue first (smallest d)
        if s == "due_any_day":
            return (1, d if d is not None else 0)
        if s == "due_soon":
            return (2, d if d is not None else 999)    # fewest days first
        if s == "upcoming":
            return (3, d if d is not None else 999)
        return (4, 0)                                   # None status last

    result.sort(key=_urgency_key)
    return result
