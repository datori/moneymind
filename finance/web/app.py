"""FastAPI web dashboard for personal finance data."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Generator

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from finance.analysis.accounts import get_accounts, get_credit_utilization
from finance.analysis.net_worth import get_balance_history, get_net_worth
from finance.analysis.spending import get_spending_summary, get_transactions
from finance.ingestion.sync import sync_all

# ---------------------------------------------------------------------------
# App and template setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Finance Dashboard")

_TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield an open SQLite connection; close on exit.

    Uses check_same_thread=False so the connection can be used inside FastAPI's
    async request handlers, which may execute on a different thread from the
    dependency resolver.
    """
    from pathlib import Path
    from finance.db import DATABASE_PATH

    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Helper: current-month date range
# ---------------------------------------------------------------------------


def _current_month_range() -> tuple[str, str]:
    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()
    return start, end


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    msg: str | None = None,
    error: str | None = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Dashboard home: net worth summary, monthly spending, credit utilization."""
    net_worth = get_net_worth(conn)
    start, end = _current_month_range()
    spending = get_spending_summary(conn, start_date=start, end_date=end)
    utilization = get_credit_utilization(conn)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "net_worth": net_worth,
            "spending": spending,
            "spending_start": start,
            "spending_end": end,
            "utilization": utilization,
            "msg": msg,
            "error": error,
        },
    )


@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Account list with current balances."""
    accounts = get_accounts(conn)
    return templates.TemplateResponse(
        "accounts.html",
        {"request": request, "accounts": accounts},
    )


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
    limit: int = 100,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Transaction browser with date range filter."""
    txns = get_transactions(
        conn,
        start_date=start,
        end_date=end,
        limit=limit,
    )
    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "transactions": txns,
            "start": start or "",
            "end": end or "",
            "limit": limit,
        },
    )


@app.get("/net-worth", response_class=HTMLResponse)
async def net_worth_page(
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Net worth history chart."""
    history = get_balance_history(conn)

    # Aggregate: sum all balances per calendar date (net worth by day)
    # Balances are unix ms timestamps; group by YYYY-MM-DD
    day_balances: dict[str, dict[str, float]] = defaultdict(dict)
    for row in history:
        ts_ms = row["timestamp"]
        day = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        day_balances[day][row["account_id"]] = row["balance"] or 0.0

    # For each day, compute net worth using the latest known balance per account
    # by carrying forward previous day's values.
    sorted_days = sorted(day_balances.keys())
    running: dict[str, float] = {}
    chart_labels: list[str] = []
    chart_values: list[float] = []

    for day in sorted_days:
        running.update(day_balances[day])
        nw = sum(running.values())
        chart_labels.append(day)
        chart_values.append(round(nw, 2))

    chart_data_json = json.dumps({"labels": chart_labels, "values": chart_values})

    return templates.TemplateResponse(
        "net_worth.html",
        {"request": request, "chart_data_json": chart_data_json},
    )


@app.get("/spending", response_class=HTMLResponse)
async def spending_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
    group_by: str = "category",
    conn: sqlite3.Connection = Depends(get_db),
):
    """Spending breakdown chart with period selector."""
    if not start or not end:
        start, end = _current_month_range()

    try:
        spending = get_spending_summary(conn, start_date=start, end_date=end, group_by=group_by)
    except ValueError:
        spending = []
        group_by = "category"

    labels = [row["label"] for row in spending]
    values = [round(row["total"], 2) for row in spending]
    chart_data_json = json.dumps({"labels": labels, "values": values})

    return templates.TemplateResponse(
        "spending.html",
        {
            "request": request,
            "spending": spending,
            "start": start,
            "end": end,
            "group_by": group_by,
            "chart_data_json": chart_data_json,
        },
    )


@app.post("/sync")
async def sync_now(
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Trigger a SimpleFIN sync and redirect back to referring page."""
    referer = request.headers.get("referer", "/")
    # Strip to path+query only (avoid open-redirect)
    from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

    parsed = urlparse(referer)
    safe_referer = urlunparse(("", "", parsed.path or "/", "", parsed.query, ""))

    try:
        result = sync_all(conn)
        msg = (
            f"Sync complete: {result['accounts_updated']} accounts updated, "
            f"{result['new_transactions']} new transactions."
        )
        # Append msg as query param so it survives the redirect
        sep = "&" if "?" in safe_referer else "?"
        redirect_url = f"{safe_referer}{sep}msg={msg}"
    except Exception as exc:  # noqa: BLE001
        error = f"Sync failed: {exc}"
        sep = "&" if "?" in safe_referer else "?"
        redirect_url = f"{safe_referer}{sep}error={error}"

    return RedirectResponse(url=redirect_url, status_code=303)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI args and start the uvicorn server."""
    parser = argparse.ArgumentParser(description="Finance web dashboard")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
