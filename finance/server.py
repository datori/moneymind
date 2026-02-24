"""MCP server exposing personal finance tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from finance.analysis.accounts import get_accounts as _get_accounts
from finance.analysis.accounts import get_credit_utilization as _get_credit_utilization
from finance.analysis.net_worth import get_net_worth as _get_net_worth
from finance.analysis.spending import get_spending_summary as _get_spending_summary
from finance.analysis.spending import get_transactions as _get_transactions
from finance.db import get_connection, init_db

mcp = FastMCP("finance")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _conn():
    """Open, initialise, and return a DB connection."""
    conn = get_connection()
    init_db(conn)
    return conn


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def get_accounts() -> list[dict]:
    """Return all active accounts with their most recent balance snapshot.

    Returns a list of account records, each with:
    id, name, type, institution, balance, available, currency, mask, last_updated
    """
    conn = _conn()
    return _get_accounts(conn)


@mcp.tool()
def get_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
    account_id: str | None = None,
    category: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return transactions matching the given filters.

    All parameters are optional. Defaults to the last 30 days, up to 100 results.

    Args:
        start_date: Inclusive start date (YYYY-MM-DD). Default: 30 days ago.
        end_date: Inclusive end date (YYYY-MM-DD).
        account_id: Filter to a specific account ID.
        category: Filter to a specific category (exact match).
        min_amount: Inclusive lower bound on amount.
        max_amount: Inclusive upper bound on amount.
        limit: Maximum number of transactions to return (default 100).
    """
    conn = _conn()
    return _get_transactions(
        conn,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        category=category,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=limit,
    )


@mcp.tool()
def get_net_worth(as_of_date: str | None = None) -> dict:
    """Return net worth broken down by account type.

    Uses the most recent balance snapshot per account (or the most recent on/before
    as_of_date if provided).

    Args:
        as_of_date: Optional date string (YYYY-MM-DD) to compute historical net worth.

    Returns a dict with: total, assets, liabilities, by_type, as_of
    """
    conn = _conn()
    return _get_net_worth(conn, as_of_date=as_of_date)


@mcp.tool()
def get_spending_summary(
    start_date: str,
    end_date: str,
    group_by: str = "category",
) -> list[dict]:
    """Return aggregate spending for the given date range.

    Only debit (negative-amount) transactions are included.

    Args:
        start_date: Inclusive start date (YYYY-MM-DD).
        end_date: Inclusive end date (YYYY-MM-DD).
        group_by: Dimension to group by: "category", "merchant", or "account".
                  Default "category".

    Returns a list of {label, total, count} sorted by total descending.
    """
    conn = _conn()
    return _get_spending_summary(conn, start_date, end_date, group_by=group_by)


@mcp.tool()
def get_credit_utilization() -> dict:
    """Return per-card and aggregate credit utilization.

    Cards without a configured limit in the credit_limits table will have
    limit=null and utilization_pct=null.

    Returns a dict with: aggregate_pct, total_balance, total_limit, cards
    """
    conn = _conn()
    return _get_credit_utilization(conn)


@mcp.tool()
def sync() -> dict:
    """Trigger a SimpleFIN sync and return a summary.

    Fetches latest account and transaction data from SimpleFIN and stores it
    in the local database.

    Returns a dict with: accounts_updated, new_transactions, synced_at
    """
    from finance.ingestion.sync import sync_all

    conn = _conn()
    return sync_all(conn)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the MCP server (stdio transport)."""
    mcp.run()
