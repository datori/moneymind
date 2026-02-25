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
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from finance.ai.categories import CATEGORIES
from finance.analysis.accounts import get_accounts, get_credit_utilization, get_transaction_timeline
from finance.analysis.overview import get_data_overview
from finance.analysis.net_worth import get_balance_history, get_net_worth
from finance.analysis.review import get_recurring, get_review_queue
from finance.analysis.spending import get_spending_summary, get_transactions
from finance.ai.pipeline import run_pipeline
from finance.ingestion.sync import sync_all

# ---------------------------------------------------------------------------
# LLM pricing constants (claude-haiku-4-5-20251001)
# ---------------------------------------------------------------------------

HAIKU_INPUT_COST_PER_M = 0.80   # $ per 1,000,000 input tokens
HAIKU_OUTPUT_COST_PER_M = 4.00  # $ per 1,000,000 output tokens

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
    spending = get_spending_summary(
        conn,
        start_date=start,
        end_date=end,
        exclude_categories=["Financial", "Income", "Investment"],
    )
    utilization = get_credit_utilization(conn)

    # Recent pipeline runs (gracefully handles missing table on first boot)
    try:
        recent_runs = conn.execute(
            "SELECT * FROM run_log ORDER BY started_at DESC LIMIT 5"
        ).fetchall()
        recent_runs = [dict(r) for r in recent_runs]
    except sqlite3.OperationalError:
        recent_runs = []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "net_worth": net_worth,
            "spending": spending,
            "spending_start": start,
            "spending_end": end,
            "utilization": utilization,
            "recent_runs": recent_runs,
            "msg": msg,
            "error": error,
        },
    )


@app.get("/accounts", response_class=HTMLResponse)
async def accounts_page(
    request: Request,
    account_id: str | None = None,
    msg: str | None = None,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Unified account list: balances, data coverage, delete actions, and timeline chart."""
    accounts = get_accounts(conn)
    overview = get_data_overview(conn)

    # Build per-account balance count lookup
    balance_rows = conn.execute(
        "SELECT account_id, COUNT(*) as cnt FROM balances GROUP BY account_id"
    ).fetchall()
    balance_counts = {r["account_id"]: r["cnt"] for r in balance_rows}

    # Build overview lookup by account_id
    ov_lookup = {ov["account_id"]: ov for ov in overview["per_account"]}

    # Merge all three sources into a single list
    merged_accounts = []
    for acct in accounts:
        ov = ov_lookup.get(acct["id"], {})
        merged_accounts.append({
            **dict(acct),
            "txn_count": ov.get("txn_count", 0),
            "earliest_txn": ov.get("earliest_txn"),
            "latest_txn": ov.get("latest_txn"),
            "last_synced_at": ov.get("last_synced_at"),
            "balance_count": balance_counts.get(acct["id"], 0),
        })

    # Timeline chart data
    from calendar import month_abbr

    timeline = get_transaction_timeline(conn, account_id=account_id)

    def _fmt_month(ym: str) -> str:
        y, m = ym.split("-")
        return f"{month_abbr[int(m)]} '{y[2:]}"

    _palette = [
        "#6366f1", "#f59e0b", "#10b981", "#ef4444", "#3b82f6",
        "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#84cc16",
    ]
    datasets = [
        {
            "label": acct["name"],
            "data": acct["counts"],
            "backgroundColor": _palette[i % len(_palette)],
            "borderRadius": 2,
        }
        for i, acct in enumerate(timeline["accounts"])
    ]
    chart_data_json = json.dumps({
        "labels": [_fmt_month(m) for m in timeline["months"]],
        "datasets": datasets,
    })
    has_chart_data = any(
        sum(acct["counts"]) > 0 for acct in timeline["accounts"]
    )

    return templates.TemplateResponse(
        "accounts.html",
        {
            "request": request,
            "accounts": merged_accounts,
            "overview": overview,
            "msg": msg,
            "chart_data_json": chart_data_json,
            "has_chart_data": has_chart_data,
            "selected_account_id": account_id,
        },
    )


@app.post("/accounts/{account_id}/delete")
async def delete_account(
    account_id: str,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Delete an account and all its dependent rows; redirect to /accounts."""
    # Look up the account — 404 if not found
    row = conn.execute("SELECT name FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Account not found")
    account_name = row["name"]

    # Capture counts before deletion for the flash message
    txn_count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE account_id = ?", (account_id,)
    ).fetchone()[0]
    bal_count = conn.execute(
        "SELECT COUNT(*) FROM balances WHERE account_id = ?", (account_id,)
    ).fetchone()[0]

    # Cascade delete in a single transaction
    conn.execute("BEGIN")
    conn.execute("DELETE FROM credit_limits WHERE account_id = ?", (account_id,))
    conn.execute("DELETE FROM sync_state WHERE account_id = ?", (account_id,))
    conn.execute("DELETE FROM transactions WHERE account_id = ?", (account_id,))
    conn.execute("DELETE FROM balances WHERE account_id = ?", (account_id,))
    conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()

    msg = (
        f"Deleted '{account_name}' ({txn_count} transactions, {bal_count} balances removed)."
    )
    return RedirectResponse(f"/accounts?msg={msg}", status_code=303)


@app.get("/data")
async def data_page():
    """Redirect to the unified accounts page (301 permanent)."""
    return RedirectResponse("/accounts", status_code=301)


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    start: str | None = None,
    end: str | None = None,
    limit: int = 100,
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "date",
    sort_dir: str = "desc",
    conn: sqlite3.Connection = Depends(get_db),
):
    """Transaction browser with date range, category, search, and sort filters."""
    txns = get_transactions(
        conn,
        start_date=start or None,
        end_date=end or None,
        limit=limit,
        category=category or None,
        search=search or None,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return templates.TemplateResponse(
        "transactions.html",
        {
            "request": request,
            "transactions": txns,
            "start": start or "",
            "end": end or "",
            "limit": limit,
            "categories": CATEGORIES,
            "category": category or "",
            "search": search or "",
            "sort_by": sort_by,
            "sort_dir": sort_dir,
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
    include_financial: str = "0",
    conn: sqlite3.Connection = Depends(get_db),
):
    """Spending breakdown chart with period selector and financial toggle."""
    if not start or not end:
        start, end = _current_month_range()

    exclude_cats = None if include_financial == "1" else ["Financial", "Income", "Investment"]

    try:
        spending = get_spending_summary(
            conn,
            start_date=start,
            end_date=end,
            group_by=group_by,
            exclude_categories=exclude_cats,
        )
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
            "include_financial": include_financial,
            "chart_data_json": chart_data_json,
        },
    )


@app.get("/review", response_class=HTMLResponse)
async def review_page(
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Review queue: transactions flagged for human review."""
    transactions = get_review_queue(conn)
    return templates.TemplateResponse(
        "review.html",
        {
            "request": request,
            "transactions": transactions,
            "categories": CATEGORIES,
        },
    )


@app.post("/review/{transaction_id}/approve")
async def review_approve(
    transaction_id: str,
    category: str = Form(None),
    conn: sqlite3.Connection = Depends(get_db),
):
    """Approve a flagged transaction: clear needs_review, optionally update category."""
    if category:
        conn.execute(
            "UPDATE transactions SET needs_review = 0, category = ? WHERE id = ?",
            (category, transaction_id),
        )
    else:
        conn.execute(
            "UPDATE transactions SET needs_review = 0 WHERE id = ?",
            (transaction_id,),
        )
    conn.commit()
    return RedirectResponse(url="/review", status_code=303)


@app.get("/recurring", response_class=HTMLResponse)
async def recurring_page(
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Recurring charges summary."""
    data = get_recurring(conn)
    return templates.TemplateResponse(
        "recurring.html",
        {"request": request, "recurring": data},
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


@app.get("/pipeline", response_class=HTMLResponse)
async def pipeline_page(
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Pipeline run history page with 'Run Pipeline' button."""
    try:
        runs = conn.execute(
            "SELECT * FROM run_log ORDER BY started_at DESC LIMIT 20"
        ).fetchall()
        runs = [dict(r) for r in runs]
        # Parse summary JSON for template access; compute LLM cost
        for run in runs:
            if run.get("summary"):
                try:
                    run["summary"] = json.loads(run["summary"])
                except (json.JSONDecodeError, TypeError):
                    run["summary"] = None
            summary = run.get("summary") or {}
            tokens_in = summary.get("tokens_in")
            tokens_out = summary.get("tokens_out")
            if tokens_in is not None and tokens_out is not None:
                run["computed_cost_usd"] = (
                    tokens_in * HAIKU_INPUT_COST_PER_M
                    + tokens_out * HAIKU_OUTPUT_COST_PER_M
                ) / 1_000_000
            else:
                run["computed_cost_usd"] = None
    except sqlite3.OperationalError:
        runs = []

    # Current transaction state
    try:
        total_txns = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        uncategorized = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE category IS NULL"
        ).fetchone()[0]
        recurring = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE is_recurring = 1"
        ).fetchone()[0]
        needs_review = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE needs_review = 1"
        ).fetchone()[0]
        cat_rows = conn.execute(
            """
            SELECT category, COUNT(*) as cnt
            FROM transactions
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY cnt DESC
            """
        ).fetchall()
        categories = [{"category": r["category"], "count": r["cnt"]} for r in cat_rows]
        current_state = {
            "total": total_txns,
            "uncategorized": uncategorized,
            "recurring": recurring,
            "needs_review": needs_review,
            "categories": categories,
        }
    except sqlite3.OperationalError:
        current_state = {
            "total": 0, "uncategorized": 0, "recurring": 0,
            "needs_review": 0, "categories": [],
        }

    return templates.TemplateResponse(
        "pipeline.html",
        {"request": request, "runs": runs, "current_state": current_state},
    )


@app.get("/pipeline/run/stream")
def pipeline_run_stream(request: Request):
    """Trigger pipeline and stream SSE progress events to the client.

    Opens its own DB connection (not via Depends) because StreamingResponse
    generators exhaust before the dependency finally-block runs. Uses a
    background thread + queue so the generator can yield events as they are
    emitted by run_pipeline rather than buffering them all.
    """
    import queue
    import threading

    from finance.db import DATABASE_PATH, init_db

    def event_generator():
        db_path = Path(DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        init_db(conn)

        try:
            event_queue: queue.Queue = queue.Queue()
            DONE_SENTINEL = object()

            def pipeline_thread():
                try:
                    def thread_emit(event: dict) -> None:
                        event_queue.put(event)

                    run_pipeline(conn, emit=thread_emit, run_sync=True)
                except Exception:
                    pass
                finally:
                    event_queue.put(DONE_SENTINEL)

            t = threading.Thread(target=pipeline_thread, daemon=True)
            t.start()

            while True:
                event = event_queue.get()
                if event is DONE_SENTINEL:
                    break
                yield f"data: {json.dumps(event)}\n\n"

        finally:
            conn.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI args and start the uvicorn server."""
    parser = argparse.ArgumentParser(description="Finance web dashboard")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
