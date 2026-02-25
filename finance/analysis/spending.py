"""Analysis functions for transactions and spending summaries."""

import sqlite3
from datetime import date, timedelta


def get_transactions(
    conn: sqlite3.Connection,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    account_id: str | None = None,
    category: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    search: str | None = None,
    sort_by: str = "date",
    sort_dir: str = "desc",
    limit: int = 100,
) -> list[dict]:
    """Return transactions matching the given filters.

    Defaults start_date to 30 days ago if not provided.

    Args:
        conn: An open SQLite connection with row_factory set.
        start_date: Inclusive lower bound (YYYY-MM-DD). Defaults to 30 days ago.
        end_date: Inclusive upper bound (YYYY-MM-DD). No default (all up to today).
        account_id: Filter to a specific account.
        category: Filter to a specific category (exact match).
        min_amount: Inclusive lower bound on amount.
        max_amount: Inclusive upper bound on amount.
        search: Substring match against description, merchant_name, merchant_normalized.
        sort_by: Column to sort by: "date" (default) or "amount".
        sort_dir: Sort direction: "desc" (default) or "asc".
        limit: Maximum number of rows to return (default 100).

    Returns:
        List of dicts with keys:
            id, date, amount, description, merchant_name, category,
            account_id, account_name, pending
    """
    if start_date is None:
        start_date = (date.today() - timedelta(days=30)).isoformat()

    sql = """
        SELECT
            t.id,
            t.date,
            t.amount,
            t.description,
            t.merchant_name,
            t.category,
            t.account_id,
            a.name  AS account_name,
            t.pending
        FROM transactions t
        LEFT JOIN accounts a ON a.id = t.account_id
        WHERE t.date >= ?
    """
    params: list = [start_date]

    if end_date is not None:
        sql += " AND t.date <= ?"
        params.append(end_date)
    if account_id is not None:
        sql += " AND t.account_id = ?"
        params.append(account_id)
    if category is not None:
        sql += " AND t.category = ?"
        params.append(category)
    if min_amount is not None:
        sql += " AND t.amount >= ?"
        params.append(min_amount)
    if max_amount is not None:
        sql += " AND t.amount <= ?"
        params.append(max_amount)
    if search:
        sql += " AND (t.description LIKE ? OR t.merchant_name LIKE ? OR t.merchant_normalized LIKE ?)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])

    # Safe allowlist for ORDER BY — never interpolate user input directly
    _dir = "ASC" if sort_dir == "asc" else "DESC"
    if sort_by == "amount":
        sql += f" ORDER BY ABS(t.amount) {_dir}, t.date DESC"
    else:
        sql += f" ORDER BY t.date {_dir}, t.id"

    sql += " LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_spending_summary(
    conn: sqlite3.Connection,
    start_date: str,
    end_date: str,
    group_by: str = "category",
    exclude_categories: list[str] | None = None,
) -> list[dict]:
    """Return aggregate spending (debit transactions only) for the given period.

    Only transactions with amount < 0 are included (debits/expenses).
    Credits and refunds are excluded.

    Args:
        conn: An open SQLite connection with row_factory set.
        start_date: Inclusive start date (YYYY-MM-DD).
        end_date: Inclusive end date (YYYY-MM-DD).
        group_by: Dimension to group by: "category", "merchant", or "account".
                  Default "category".
        exclude_categories: Optional list of category names to exclude from
                            results. When None (default), all categories are
                            included (backward-compatible behavior).

    Returns:
        List of dicts with keys: label, total, count.
        Sorted by total descending (highest spend first).

    Raises:
        ValueError: if group_by is not one of the accepted values.
    """
    valid = {"category", "merchant", "account"}
    if group_by not in valid:
        raise ValueError(f"group_by must be one of {valid}, got {group_by!r}")

    if group_by == "category":
        label_expr = "COALESCE(t.category, 'Uncategorized')"
    elif group_by == "merchant":
        label_expr = "COALESCE(t.merchant_name, t.description, 'Unknown')"
    else:  # account
        label_expr = "COALESCE(a.name, t.account_id)"

    sql = f"""
        SELECT
            {label_expr} AS label,
            SUM(ABS(t.amount)) AS total,
            COUNT(*) AS count
        FROM transactions t
        LEFT JOIN accounts a ON a.id = t.account_id
        WHERE t.amount < 0
          AND t.date >= ?
          AND t.date <= ?
    """
    params: list = [start_date, end_date]

    if exclude_categories:
        placeholders = ", ".join("?" * len(exclude_categories))
        sql += f" AND t.category NOT IN ({placeholders})"
        params.extend(exclude_categories)

    sql += f"""
        GROUP BY {label_expr}
        ORDER BY total DESC
    """

    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
