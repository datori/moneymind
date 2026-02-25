"""Click CLI for the personal finance tracker."""

from __future__ import annotations

import json
import sys
import time

import click

from finance.db import get_connection, init_db


def _open_db():
    """Open and initialise the database, return connection."""
    conn = get_connection()
    init_db(conn)
    return conn


def _print_table(headers: list[str], rows: list[list]) -> None:
    """Print a plain-text aligned table to stdout."""
    # Compute column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell) if cell is not None else ""))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    separator = "  ".join("-" * w for w in widths)

    click.echo(fmt.format(*headers))
    click.echo(separator)
    for row in rows:
        click.echo(fmt.format(*[str(c) if c is not None else "" for c in row]))


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group()
def main() -> None:
    """Personal finance tracker CLI."""
    pass


# ---------------------------------------------------------------------------
# finance sync
# ---------------------------------------------------------------------------


@main.group(invoke_without_command=True)
@click.pass_context
def sync(ctx: click.Context) -> None:
    """Sync financial data from SimpleFIN.

    When called without a subcommand, runs the full account sync.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(_sync_run)


def _sync_run() -> None:
    """Core sync logic (shared by `finance sync` and `finance sync run`)."""
    import logging
    import os

    from finance.ingestion.sync import sync_all

    conn = _open_db()
    try:
        result = sync_all(conn)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Sync failed: {exc}", err=True)
        sys.exit(1)

    click.echo(
        f"Sync complete — {result['accounts_updated']} account(s) synced, "
        f"{result['new_transactions']} new transaction(s), "
        f"at {result['synced_at']}"
    )

    # Pass 2: enrich transactions (non-fatal)
    if os.getenv("ANTHROPIC_API_KEY"):
        from finance.ai.enrich import enrich_transactions

        try:
            enriched = enrich_transactions(conn)
            click.echo(f"Enrichment complete — {enriched} transaction(s) enriched.")
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).warning("Enrichment failed (non-fatal): %s", exc)


@sync.command("run")
def sync_run() -> None:
    """Sync all accounts from SimpleFIN."""
    _sync_run()


@sync.command("setup")
@click.argument("setup_token_url")
def sync_setup(setup_token_url: str) -> None:
    """Claim a SimpleFIN setup token URL and print the access URL.

    \b
    SETUP_TOKEN_URL  The one-time setup token URL from simplefin.org
    """
    from finance.ingestion.simplefin import claim_setup_token

    try:
        access_url = claim_setup_token(setup_token_url)
    except Exception as exc:
        click.echo(
            f"Error: could not claim setup token — {exc}\n"
            "Make sure the URL is a valid, unclaimed SimpleFIN setup token URL.",
            err=True,
        )
        sys.exit(1)

    click.echo(f"Access URL obtained:\n\n  {access_url}\n")
    click.echo(
        "Add the following line to your .env file:\n\n"
        f"  SIMPLEFIN_ACCESS_URL={access_url}\n"
    )


# ---------------------------------------------------------------------------
# finance accounts
# ---------------------------------------------------------------------------


def _accounts_list(conn, as_json: bool) -> None:
    """Print the accounts table (shared by `accounts` default and `accounts list`)."""
    from finance.analysis.accounts import get_accounts

    data = get_accounts(conn)

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    if not data:
        click.echo("No accounts found.")
        return

    headers = ["Name", "Type", "Institution", "Balance", "Currency", "Mask"]
    rows = [
        [
            a["name"],
            a["type"] or "",
            a["institution"] or "",
            f"{a['balance']:.2f}" if a["balance"] is not None else "",
            a["currency"] or "",
            a["mask"] or "",
        ]
        for a in data
    ]
    _print_table(headers, rows)


@main.group("accounts", invoke_without_command=True)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def accounts(ctx: click.Context, as_json: bool) -> None:
    """Manage accounts: list (default) or delete."""
    if ctx.invoked_subcommand is None:
        conn = _open_db()
        _accounts_list(conn, as_json)


@accounts.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def accounts_list(as_json: bool) -> None:
    """List all active accounts with their current balance."""
    conn = _open_db()
    _accounts_list(conn, as_json)


@accounts.command("delete")
@click.argument("account_id")
@click.option("--confirm", "confirmed", is_flag=True, help="Skip confirmation prompt.")
def accounts_delete(account_id: str, confirmed: bool) -> None:
    """Delete an account and all associated data.

    \b
    ACCOUNT_ID  The account ID to delete (use `finance accounts` to find it).

    Deletes the account and all dependent rows from: transactions, balances,
    sync_state, and credit_limits.  Use --confirm to skip the interactive prompt.
    """
    conn = _open_db()

    # Check account exists
    row = conn.execute(
        "SELECT id, name FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
    if row is None:
        click.echo(f"Error: account '{account_id}' not found.", err=True)
        sys.exit(1)

    account_name = row["name"]

    # Confirmation guard
    if not confirmed:
        answer = click.prompt(
            f"Delete account '{account_name}' and all associated data? [y/N]",
            default="N",
            show_default=False,
        )
        if answer.strip().lower() not in ("y", "yes"):
            click.echo("Aborted.")
            return

    # Cascade delete inside a single transaction
    conn.execute("BEGIN")
    try:
        cl_count = conn.execute(
            "DELETE FROM credit_limits WHERE account_id = ?", (account_id,)
        ).rowcount
        ss_count = conn.execute(
            "DELETE FROM sync_state WHERE account_id = ?", (account_id,)
        ).rowcount
        tx_count = conn.execute(
            "DELETE FROM transactions WHERE account_id = ?", (account_id,)
        ).rowcount
        bal_count = conn.execute(
            "DELETE FROM balances WHERE account_id = ?", (account_id,)
        ).rowcount
        conn.execute(
            "DELETE FROM accounts WHERE id = ?", (account_id,)
        )
        conn.execute("COMMIT")
    except Exception as exc:
        conn.execute("ROLLBACK")
        click.echo(f"Error during deletion: {exc}", err=True)
        sys.exit(1)

    click.echo(
        f"Deleted account '{account_name}' ({account_id}).\n"
        f"  transactions:  {tx_count} row(s)\n"
        f"  balances:      {bal_count} row(s)\n"
        f"  sync_state:    {ss_count} row(s)\n"
        f"  credit_limits: {cl_count} row(s)"
    )


# ---------------------------------------------------------------------------
# finance transactions
# ---------------------------------------------------------------------------


@main.command("transactions")
@click.option("--start", "start_date", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--end", "end_date", default=None, help="End date (YYYY-MM-DD).")
@click.option("--account", "account_id", default=None, help="Filter by account ID.")
@click.option("--category", default=None, help="Filter by category.")
@click.option("--limit", default=100, show_default=True, help="Maximum rows to return.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def transactions(
    start_date: str | None,
    end_date: str | None,
    account_id: str | None,
    category: str | None,
    limit: int,
    as_json: bool,
) -> None:
    """List transactions with optional filters.

    Defaults to the last 30 days, up to 100 results.
    """
    from finance.analysis.spending import get_transactions

    conn = _open_db()
    data = get_transactions(
        conn,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        category=category,
        limit=limit,
    )

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    if not data:
        click.echo("No transactions found.")
        return

    headers = ["Date", "Amount", "Description", "Category", "Account", "Pending"]
    rows = [
        [
            t["date"],
            f"{t['amount']:>10.2f}",
            (t["description"] or "")[:40],
            t["category"] or "",
            t["account_name"] or t["account_id"],
            "yes" if t["pending"] else "no",
        ]
        for t in data
    ]
    _print_table(headers, rows)


# ---------------------------------------------------------------------------
# finance net-worth
# ---------------------------------------------------------------------------


@main.command("net-worth")
@click.option("--as-of", "as_of_date", default=None, help="Date (YYYY-MM-DD) for historical view.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def net_worth(as_of_date: str | None, as_json: bool) -> None:
    """Show current net worth broken down by account type."""
    from finance.analysis.net_worth import get_net_worth

    conn = _open_db()
    data = get_net_worth(conn, as_of_date=as_of_date)

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(f"Net Worth  : ${data['total']:>12,.2f}")
    click.echo(f"Assets     : ${data['assets']:>12,.2f}")
    click.echo(f"Liabilities: ${data['liabilities']:>12,.2f}")
    if data["as_of"]:
        click.echo(f"As of      : {data['as_of']}")
    click.echo("")
    click.echo("Breakdown by type:")
    for acct_type, value in data["by_type"].items():
        if value != 0.0:
            click.echo(f"  {acct_type:<12}: ${value:>12,.2f}")


# ---------------------------------------------------------------------------
# finance spending
# ---------------------------------------------------------------------------


@main.command("spending")
@click.option("--start", "start_date", required=True, help="Start date (YYYY-MM-DD).")
@click.option("--end", "end_date", required=True, help="End date (YYYY-MM-DD).")
@click.option(
    "--group-by",
    "group_by",
    default="category",
    show_default=True,
    type=click.Choice(["category", "merchant", "account"]),
    help="Dimension to group spending by.",
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def spending(start_date: str, end_date: str, group_by: str, as_json: bool) -> None:
    """Show aggregate spending for a date range."""
    from finance.analysis.spending import get_spending_summary

    conn = _open_db()
    data = get_spending_summary(conn, start_date, end_date, group_by=group_by)

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    if not data:
        click.echo("No spending data found for that period.")
        return

    headers = ["Label", "Total", "Count"]
    rows = [[d["label"], f"${d['total']:>10,.2f}", str(d["count"])] for d in data]
    _print_table(headers, rows)


# ---------------------------------------------------------------------------
# finance utilization
# ---------------------------------------------------------------------------


@main.command("utilization")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def utilization(as_json: bool) -> None:
    """Show credit card utilization."""
    from finance.analysis.accounts import get_credit_utilization

    conn = _open_db()
    data = get_credit_utilization(conn)

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    if not data["cards"]:
        click.echo("No credit accounts found.")
        return

    headers = ["Card", "Balance", "Limit", "Utilization"]
    rows = []
    for c in data["cards"]:
        util_str = f"{c['utilization_pct']:.1f}%" if c["utilization_pct"] is not None else "N/A"
        limit_str = f"${c['limit']:,.2f}" if c["limit"] is not None else "N/A"
        rows.append([c["name"], f"${abs(c['balance']):,.2f}", limit_str, util_str])
    _print_table(headers, rows)

    click.echo("")
    total_bal = f"${data['total_balance']:,.2f}"
    total_lim = f"${data['total_limit']:,.2f}" if data["total_limit"] is not None else "N/A"
    agg_pct = f"{data['aggregate_pct']:.1f}%" if data["aggregate_pct"] is not None else "N/A"
    click.echo(f"Total balance: {total_bal}  |  Total limit: {total_lim}  |  Aggregate: {agg_pct}")


# ---------------------------------------------------------------------------
# finance set-limit
# ---------------------------------------------------------------------------


@main.command("set-limit")
@click.argument("account_id")
@click.argument("amount", type=float)
def set_limit(account_id: str, amount: float) -> None:
    """Set or update the credit limit for ACCOUNT_ID.

    \b
    ACCOUNT_ID  The account ID (use `finance accounts` to find it).
    AMOUNT      Credit limit amount (e.g. 5000).
    """
    conn = _open_db()
    now_ms = int(time.time() * 1000)
    conn.execute(
        """
        INSERT INTO credit_limits (account_id, credit_limit, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(account_id) DO UPDATE SET credit_limit = excluded.credit_limit,
                                              updated_at   = excluded.updated_at
        """,
        (account_id, amount, now_ms),
    )
    conn.commit()
    click.echo(f"Credit limit for {account_id} set to ${amount:,.2f}")


# ---------------------------------------------------------------------------
# finance import
# ---------------------------------------------------------------------------


@main.command("import")
@click.argument("file", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option(
    "--institution",
    required=True,
    help="Institution key (e.g. chase, discover, citi). Run `finance institutions` to list.",
)
@click.option(
    "--account",
    "account_id",
    default=None,
    help="Existing account ID to associate transactions with. Omit to auto-create.",
)
def import_csv_cmd(file: str, institution: str, account_id: str | None) -> None:
    """Import transactions from a CSV file exported by a financial institution.

    \b
    FILE          Path to the CSV file to import.
    --institution Institution key (required). Run `finance institutions` to list supported names.
    --account     Existing account ID. If omitted, a new account is created interactively.
    """
    from finance.ingestion.csv_import import import_csv

    conn = _open_db()
    try:
        result = import_csv(conn, file, institution, account_id)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"Import failed: {exc}", err=True)
        sys.exit(1)

    click.echo(
        f"Import complete — {result['rows_read']} row(s) read, "
        f"{result['rows_imported']} imported, "
        f"{result['rows_skipped']} skipped (duplicates or blank)."
    )


# ---------------------------------------------------------------------------
# finance pipeline
# ---------------------------------------------------------------------------


@main.command("pipeline")
@click.option(
    "--enrich-only",
    is_flag=True,
    default=False,
    help="Skip SimpleFIN sync; only run the AI enrichment pass.",
)
def pipeline_cmd(enrich_only: bool) -> None:
    """Run the AI enrichment pipeline (sync + categorize + enrich in one pass).

    Syncs latest transactions from SimpleFIN (unless --enrich-only), then runs
    the cluster-first single-pass pipeline to assign categories, canonical merchant
    names, recurring flags, and review flags to all transactions.

    Use 'finance categorize' or 'finance sync' for the older two-pass approach
    (deprecated).
    """
    import os

    if not os.getenv("ANTHROPIC_API_KEY"):
        click.echo(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Add ANTHROPIC_API_KEY=<your-key> to your .env file or environment.",
            err=True,
        )
        sys.exit(1)

    from finance.ai.pipeline import run_pipeline

    conn = _open_db()
    start_ms = int(time.time() * 1000)

    def cli_emit(event: dict) -> None:
        etype = event.get("type")
        step = event.get("step")
        data = event.get("data", {})

        if etype == "step_start":
            if step == "sync":
                click.echo("[sync] starting...")
            elif step == "cluster-build":
                click.echo("[cluster-build] building clusters...")
            elif step == "enrich-batch":
                bi = data.get("batch_index", "?")
                bt = data.get("batch_total", "?")
                click.echo(f"[enrich-batch {bi}/{bt}] sending to AI...")
        elif etype == "step_done":
            if step == "sync":
                n = data.get("new_transactions", 0)
                click.echo(f"[sync] done — {n} new transactions")
            elif step == "cluster-build":
                cc = data.get("cluster_count", "?")
                tc = data.get("transaction_count", "?")
                click.echo(f"[cluster-build] done — {cc} clusters, {tc} transactions")
            elif step == "enrich-batch":
                bi = data.get("batch_index", "?")
                bt = data.get("batch_total", "?")
                ti = data.get("tokens_in", "?")
                to = data.get("tokens_out", "?")
                click.echo(f"[enrich-batch {bi}/{bt}] done — {ti} tokens in / {to} tokens out")
        elif etype == "error":
            msg = data.get("message", "Unknown error")
            if step:
                click.echo(f"[{step}] error: {msg}", err=True)
            else:
                click.echo(f"[pipeline] error: {msg}", err=True)
        elif etype == "run_done":
            txn = data.get("transactions_updated", 0)
            dur_ms = data.get("duration_ms", 0)
            dur_s = dur_ms / 1000.0
            click.echo(f"\nPipeline complete — {txn} transaction(s) updated in {dur_s:.1f}s")

    try:
        total = run_pipeline(conn, emit=cli_emit, run_sync=not enrich_only)
    except Exception as exc:
        click.echo(f"Pipeline failed: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# finance categorize (deprecated — use 'finance pipeline')
# ---------------------------------------------------------------------------


@main.command("categorize")
@click.option("--all", "recategorize_all", is_flag=True, help="Re-categorize all transactions, not just uncategorized ones.")
def categorize(recategorize_all: bool) -> None:
    """Categorize transactions using AI.

    DEPRECATED: Use 'finance pipeline' instead, which runs a faster single-pass
    cluster-first pipeline that combines categorization and enrichment.

    By default, only processes transactions where category is not yet set.
    Use --all to re-categorize every transaction (e.g. after taxonomy changes).
    """
    import os

    if not os.getenv("ANTHROPIC_API_KEY"):
        click.echo(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Add ANTHROPIC_API_KEY=<your-key> to your .env file or environment.",
            err=True,
        )
        sys.exit(1)

    import logging

    from finance.ai.categorize import categorize_all, categorize_uncategorized

    conn = _open_db()
    if recategorize_all:
        count = categorize_all(conn)
    else:
        count = categorize_uncategorized(conn)

    click.echo(f"Categorized {count} transaction(s).")

    # Pass 2: enrich transactions (non-fatal)
    if os.getenv("ANTHROPIC_API_KEY"):
        from finance.ai.enrich import enrich_transactions

        try:
            enriched = enrich_transactions(conn)
            click.echo(f"Enrichment complete — {enriched} transaction(s) enriched.")
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).warning("Enrichment failed (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# finance fix-category
# ---------------------------------------------------------------------------


@main.command("fix-category")
@click.argument("transaction_id")
@click.argument("category")
def fix_category(transaction_id: str, category: str) -> None:
    """Manually set the category for a transaction.

    \b
    TRANSACTION_ID  The transaction ID (use `finance transactions` to find it).
    CATEGORY        The category to assign. Run `finance categories` to list valid values.
    """
    from finance.ai.categories import CATEGORIES

    if category not in CATEGORIES:
        valid = ", ".join(CATEGORIES)
        click.echo(
            f"Error: '{category}' is not a valid category.\nValid categories: {valid}",
            err=True,
        )
        sys.exit(1)

    conn = _open_db()
    now_ms = int(time.time() * 1000)
    cursor = conn.execute(
        "UPDATE transactions SET category = ?, categorized_at = ? WHERE id = ?",
        (category, now_ms, transaction_id),
    )
    conn.commit()

    if cursor.rowcount == 0:
        click.echo(f"Error: transaction '{transaction_id}' not found.", err=True)
        sys.exit(1)

    click.echo(f"Transaction {transaction_id} category set to '{category}'.")


# ---------------------------------------------------------------------------
# finance categories
# ---------------------------------------------------------------------------


@main.command("categories")
def categories_list() -> None:
    """List all valid category names."""
    from finance.ai.categories import CATEGORIES

    for cat in CATEGORIES:
        click.echo(cat)


# ---------------------------------------------------------------------------
# finance institutions
# ---------------------------------------------------------------------------


@main.command("institutions")
def institutions() -> None:
    """List supported CSV institution keys for use with `finance import`."""
    from finance.ingestion.csv_import import NORMALIZERS

    for key in NORMALIZERS.keys():
        click.echo(key)


# ---------------------------------------------------------------------------
# finance data
# ---------------------------------------------------------------------------


@main.command("data")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def data_overview(as_json: bool) -> None:
    """Show data coverage summary: transaction counts, date ranges, and last sync per account."""
    from finance.analysis.overview import get_data_overview

    conn = _open_db()
    result = get_data_overview(conn)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    per_account = result["per_account"]
    if not per_account:
        click.echo("No accounts found.")
        return

    g = result["global"]
    # Compute months covered from date range
    earliest = g["earliest_transaction"]
    latest = g["latest_transaction"]
    if earliest and latest:
        e_year, e_month = int(earliest[:4]), int(earliest[5:7])
        l_year, l_month = int(latest[:4]), int(latest[5:7])
        months = (l_year - e_year) * 12 + (l_month - e_month) + 1
        months_str = f", covering {months} month{'s' if months != 1 else ''}"
    else:
        months_str = ""

    click.echo(
        f"{g['total_transactions']} transaction{'s' if g['total_transactions'] != 1 else ''} "
        f"across {g['total_accounts']} account{'s' if g['total_accounts'] != 1 else ''}"
        f"{months_str}"
    )
    click.echo("")

    import datetime as _dt

    headers = ["Account", "Institution", "Transactions", "Earliest", "Latest", "Last Synced"]
    rows = []
    for a in per_account:
        if a["last_synced_at"] is not None:
            ts_s = a["last_synced_at"] / 1000
            last_synced = _dt.datetime.fromtimestamp(ts_s).strftime("%Y-%m-%d %H:%M")
        else:
            last_synced = "Never"
        rows.append([
            a["name"],
            a["institution"] or "",
            str(a["txn_count"]),
            a["earliest_txn"] or "—",
            a["latest_txn"] or "—",
            last_synced,
        ])
    _print_table(headers, rows)


# ---------------------------------------------------------------------------
# finance limits
# ---------------------------------------------------------------------------


@main.command("limits")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def limits(as_json: bool) -> None:
    """List all configured credit limits."""
    conn = _open_db()
    rows = conn.execute(
        """
        SELECT cl.account_id, a.name, cl.credit_limit, cl.updated_at
        FROM credit_limits cl
        LEFT JOIN accounts a ON a.id = cl.account_id
        ORDER BY a.name
        """
    ).fetchall()

    data = [dict(r) for r in rows]

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    if not data:
        click.echo("No credit limits configured. Use `finance set-limit` to add one.")
        return

    headers = ["Account ID", "Name", "Limit"]
    table_rows = [
        [r["account_id"], r["name"] or "", f"${r['credit_limit']:,.2f}"]
        for r in data
    ]
    _print_table(headers, table_rows)


# ---------------------------------------------------------------------------
# finance review
# ---------------------------------------------------------------------------


@main.command("review")
@click.option("--list", "list_only", is_flag=True, help="Print table of flagged transactions without interactive triage.")
def review(list_only: bool) -> None:
    """Triage transactions flagged for review.

    Without --list, launches an interactive session to accept, reclassify, or
    skip each flagged transaction one at a time.

    Use --list to print a read-only summary table instead.
    """
    from finance.analysis.review import get_review_queue
    from finance.ai.categories import CATEGORIES

    conn = _open_db()
    queue = get_review_queue(conn)

    if not queue:
        click.echo("No transactions flagged for review.")
        return

    if list_only:
        # --list mode: print table
        headers = ["Date", "Amount", "Merchant", "Category", "Reason"]
        rows = [
            [
                t["date"],
                f"{t['amount']:>10.2f}" if t["amount"] is not None else "",
                (t["merchant_normalized"] or t["merchant_name"] or t["description"] or "")[:30],
                t["category"] or "",
                (t["review_reason"] or "")[:50],
            ]
            for t in queue
        ]
        _print_table(headers, rows)
        return

    # Interactive triage mode
    accepted = 0
    reclassified = 0
    skipped = 0
    total = len(queue)

    for idx, txn in enumerate(queue, start=1):
        click.echo("")
        click.echo(f"--- Transaction {idx}/{total} ---")
        click.echo(f"  ID         : {txn['id']}")
        click.echo(f"  Date       : {txn['date']}")
        click.echo(f"  Amount     : {txn['amount']}")
        click.echo(f"  Description: {txn['description'] or ''}")
        click.echo(f"  Merchant   : {txn['merchant_normalized'] or txn['merchant_name'] or ''}")
        click.echo(f"  Category   : {txn['category'] or ''}")
        click.echo(f"  Reason     : {txn['review_reason'] or ''}")

        while True:
            choice = click.prompt("[a]ccept / [r]eclassify / [s]kip", default="s").strip().lower()
            if choice in ("a", "accept"):
                conn.execute(
                    "UPDATE transactions SET needs_review = 0 WHERE id = ?",
                    (txn["id"],),
                )
                conn.commit()
                accepted += 1
                click.echo("  Accepted.")
                break
            elif choice in ("r", "reclassify"):
                while True:
                    new_cat = click.prompt("Enter new category").strip()
                    if new_cat in CATEGORIES:
                        conn.execute(
                            "UPDATE transactions SET needs_review = 0, category = ? WHERE id = ?",
                            (new_cat, txn["id"]),
                        )
                        conn.commit()
                        reclassified += 1
                        click.echo(f"  Reclassified to '{new_cat}'.")
                        break
                    else:
                        valid = ", ".join(CATEGORIES)
                        click.echo(f"  Invalid category. Valid options: {valid}")
                break
            elif choice in ("s", "skip"):
                skipped += 1
                click.echo("  Skipped.")
                break
            else:
                click.echo("  Please enter 'a', 'r', or 's'.")

    click.echo("")
    click.echo(
        f"Reviewed {total} transaction(s). "
        f"Accepted: {accepted}. "
        f"Reclassified: {reclassified}. "
        f"Skipped: {skipped}."
    )


# ---------------------------------------------------------------------------
# finance recurring
# ---------------------------------------------------------------------------


@main.command("recurring")
def recurring() -> None:
    """Show detected recurring charges grouped by merchant.

    Run `finance sync` or `finance categorize` to populate enrichment data.
    """
    from finance.analysis.review import get_recurring

    conn = _open_db()
    data = get_recurring(conn)

    if not data:
        click.echo(
            "No recurring charges detected. "
            "Run `finance sync` to enrich transactions."
        )
        return

    headers = ["Merchant", "Count", "Typical Amount"]
    rows = [
        [
            d["merchant_normalized"],
            str(d["count"]),
            f"${d['typical_amount']:,.2f}",
        ]
        for d in data
    ]
    _print_table(headers, rows)
