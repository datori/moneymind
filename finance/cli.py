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


@main.command("accounts")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def accounts(as_json: bool) -> None:
    """List all active accounts with their current balance."""
    from finance.analysis.accounts import get_accounts

    conn = _open_db()
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
# finance categorize
# ---------------------------------------------------------------------------


@main.command("categorize")
@click.option("--all", "recategorize_all", is_flag=True, help="Re-categorize all transactions, not just uncategorized ones.")
def categorize(recategorize_all: bool) -> None:
    """Categorize transactions using AI.

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

    from finance.ai.categorize import categorize_all, categorize_uncategorized

    conn = _open_db()
    if recategorize_all:
        count = categorize_all(conn)
    else:
        count = categorize_uncategorized(conn)

    click.echo(f"Categorized {count} transaction(s).")


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
