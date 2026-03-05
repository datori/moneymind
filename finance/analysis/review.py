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

    Status values: "upcoming", "due_soon", "due_any_day", "past_due",
    "likely_cancelled", None.
    Results are sorted by urgency (past_due first, then likely_cancelled,
    due_any_day, due_soon, upcoming, then None).
    """
    rows = conn.execute(
        """
        SELECT
            merchant_normalized,
            date,
            amount,
            category
        FROM transactions
        WHERE is_recurring = 1
          AND amount < 0
          AND merchant_normalized IS NOT NULL
          AND merchant_normalized != ''
        ORDER BY merchant_normalized, date
        """
    ).fetchall()

    if not rows:
        return []

    from collections import defaultdict, Counter

    groups: dict[str, list[tuple[str, float]]] = defaultdict(list)
    categories: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        if row["amount"] is not None and row["date"] is not None:
            groups[row["merchant_normalized"]].append((row["date"], abs(row["amount"])))
            if row["category"]:
                categories[row["merchant_normalized"]][row["category"]] += 1

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
            elif days_until_next <= -interval_days:
                status = "likely_cancelled"
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
                "category": categories[merchant].most_common(1)[0][0] if categories[merchant] else None,
            }
        )

    # Sort by urgency
    def _urgency_key(item: dict) -> tuple:
        s = item["status"]
        d = item["days_until_next"]
        if s == "past_due":
            return (0, d if d is not None else 0)      # most overdue first (smallest d)
        if s == "likely_cancelled":
            return (1, d if d is not None else 0)      # most overdue first
        if s == "due_any_day":
            return (2, d if d is not None else 0)
        if s == "due_soon":
            return (3, d if d is not None else 999)    # fewest days first
        if s == "upcoming":
            return (4, d if d is not None else 999)
        return (5, 0)                                   # None status last

    result.sort(key=_urgency_key)
    return result


def apply_recurring_overrides(conn: sqlite3.Connection) -> int:
    """Deterministically set is_recurring=1 for any merchant+amount seen in 3+ distinct months.

    The LLM enrichment pipeline classifies recurring charges by merchant name
    heuristics, which misses payment-plan charges (e.g. Sweetwater Instruments)
    and subscription fees billed under generic names. This function applies a
    pattern-based override: if the same (merchant_normalized, amount) pair
    appears in 3 or more distinct calendar months it is unambiguously recurring.

    Only transactions with amount < 0 (debits) and a non-null merchant_normalized
    are considered. Transactions already flagged is_recurring=1 are untouched.

    Returns:
        Number of transaction rows updated.
    """
    pairs = conn.execute(
        """
        SELECT merchant_normalized, ROUND(ABS(amount), 2) AS amt
        FROM transactions
        WHERE amount < 0
          AND merchant_normalized IS NOT NULL
        GROUP BY merchant_normalized, ROUND(ABS(amount), 2)
        HAVING COUNT(DISTINCT SUBSTR(date, 1, 7)) >= 3
        """
    ).fetchall()

    updated = 0
    for row in pairs:
        cursor = conn.execute(
            """
            UPDATE transactions
            SET is_recurring = 1
            WHERE merchant_normalized = ?
              AND ROUND(ABS(amount), 2) = ?
              AND amount < 0
              AND is_recurring = 0
            """,
            (row["merchant_normalized"], row["amt"]),
        )
        updated += cursor.rowcount

    conn.commit()
    return updated


def get_recurring_spend_timeline(
    conn: sqlite3.Connection,
    months: int = 13,
    future_months: int = 3,
) -> dict:
    """Return monthly recurring spend per merchant for chart rendering.

    Args:
        conn: An open SQLite connection with row_factory set.
        months: Number of past calendar months to include (ending with current month).
        future_months: Number of future calendar months to project.

    Returns:
        Dict with keys:
            months: list of YYYY-MM strings (past, ascending), length == months
            future_months: list of YYYY-MM strings (future, ascending), length == future_months
            merchants: list of dicts per merchant (only those with 2+ charges), each with:
                name, actual, ghost, projected, status, typical_amount, interval_days
    """
    from collections import defaultdict

    today = date.today()

    # Generate past month list (ending with current month)
    month_list: list[str] = []
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_list.append(f"{y:04d}-{m:02d}")

    # Generate future month list
    future_month_list: list[str] = []
    for i in range(1, future_months + 1):
        m = today.month + i
        y = today.year
        while m > 12:
            m -= 12
            y += 1
        future_month_list.append(f"{y:04d}-{m:02d}")

    rows = conn.execute(
        """
        SELECT merchant_normalized, date, amount
        FROM transactions
        WHERE is_recurring = 1
          AND merchant_normalized IS NOT NULL
          AND merchant_normalized != ''
        ORDER BY merchant_normalized, date
        """
    ).fetchall()

    if not rows:
        return {"months": month_list, "future_months": future_month_list, "merchants": []}

    groups: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in rows:
        if row["amount"] is not None and row["date"] is not None:
            groups[row["merchant_normalized"]].append((row["date"], abs(row["amount"])))

    # Determine window end for projection loop
    end_ym = future_month_list[-1] if future_month_list else month_list[-1]
    end_y, end_m = int(end_ym[:4]), int(end_ym[5:])
    if end_m < 12:
        window_end = date(end_y, end_m + 1, 1) - timedelta(days=1)
    else:
        window_end = date(end_y + 1, 1, 1) - timedelta(days=1)

    past_start_ym = month_list[0]
    past_start = date(int(past_start_ym[:4]), int(past_start_ym[5:]), 1)

    month_set = set(month_list)
    future_month_set = set(future_month_list)

    merchant_list = []
    for merchant, entries in groups.items():
        dates = sorted(e[0] for e in entries)
        amounts = [e[1] for e in entries]

        # Need at least 2 charges to compute an interval
        if len(dates) < 2:
            continue

        # Typical amount (median)
        sorted_amounts = sorted(amounts)
        mid = len(sorted_amounts) // 2
        if len(sorted_amounts) % 2 == 1:
            typical = sorted_amounts[mid]
        else:
            typical = (sorted_amounts[mid - 1] + sorted_amounts[mid]) / 2.0
        typical = round(typical, 2)

        # Interval (median gap)
        date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
        gaps = [(date_objs[i + 1] - date_objs[i]).days for i in range(len(date_objs) - 1)]
        gaps_sorted = sorted(gaps)
        gmid = len(gaps_sorted) // 2
        if len(gaps_sorted) % 2 == 1:
            median_gap = gaps_sorted[gmid]
        else:
            median_gap = (gaps_sorted[gmid - 1] + gaps_sorted[gmid]) // 2
        interval_days = max(1, median_gap)

        last_date_obj = datetime.strptime(dates[-1], "%Y-%m-%d").date()
        next_due_obj = last_date_obj + timedelta(days=interval_days)
        days_until_next = (next_due_obj - today).days
        tolerance = max(3, int(interval_days * 0.35))

        if days_until_next > 7:
            status = "upcoming"
        elif 1 <= days_until_next <= 7:
            status = "due_soon"
        elif -tolerance <= days_until_next <= 0:
            status = "due_any_day"
        elif days_until_next <= -interval_days:
            status = "likely_cancelled"
        else:
            status = "past_due"

        # Actual spend per past month
        actual_map: dict[str, float] = defaultdict(float)
        for d_str, amt in entries:
            ym = d_str[:7]
            if ym in month_set:
                actual_map[ym] += amt

        # Ghost: expected-but-missing past months
        # Step backward from last_date by interval_days
        ghost_map: dict[str, float] = defaultdict(float)
        cutoff = today - timedelta(days=tolerance)
        k = 0
        while True:
            exp_date = last_date_obj + timedelta(days=k * interval_days)
            if exp_date < past_start:
                break
            ym = exp_date.strftime("%Y-%m")
            if ym in month_set and exp_date <= cutoff:
                if actual_map.get(ym, 0.0) == 0.0:
                    ghost_map[ym] += typical
            k -= 1

        # Projected: future months (skip if likely_cancelled)
        projected_map: dict[str, float] = defaultdict(float)
        if status != "likely_cancelled":
            k = 1
            while True:
                exp_date = last_date_obj + timedelta(days=k * interval_days)
                if exp_date > window_end:
                    break
                ym = exp_date.strftime("%Y-%m")
                if ym in future_month_set:
                    projected_map[ym] += typical
                k += 1

        actual = [round(actual_map.get(m, 0.0), 2) for m in month_list]
        ghost = [round(ghost_map.get(m, 0.0), 2) for m in month_list]
        projected = [round(projected_map.get(m, 0.0), 2) for m in future_month_list]

        merchant_list.append({
            "name": merchant,
            "actual": actual,
            "ghost": ghost,
            "projected": projected,
            "status": status,
            "typical_amount": typical,
            "interval_days": interval_days,
        })

    return {
        "months": month_list,
        "future_months": future_month_list,
        "merchants": merchant_list,
    }
