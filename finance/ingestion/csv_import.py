"""CSV ingestion pipeline with per-institution normalizers.

Supports Chase, Discover, Discover Debit, Citi, Amex, Robinhood, and M1.
Each normalizer maps institution-specific CSV columns to the canonical
transaction schema used by the ``transactions`` table.
"""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Transaction dataclass (mirrors the transactions table)
# ---------------------------------------------------------------------------


@dataclass
class Transaction:
    """Canonical transaction record for CSV-imported data."""

    id: str
    account_id: str
    date: str                  # YYYY-MM-DD
    amount: float              # negative = debit
    description: str | None = None
    merchant_name: str | None = None
    category: str | None = None
    pending: int = 0
    source: str = "csv"
    raw: str | None = None
    categorized_at: int | None = None


# ---------------------------------------------------------------------------
# 1.4  Hash-based deterministic ID
# ---------------------------------------------------------------------------


def generate_csv_id(
    account_id: str, date: str, amount: str, description: str
) -> str:
    """Return a 16-character hex digest used as the transaction primary key.

    The digest is deterministic: importing the same row twice always produces
    the same ID, enabling ``INSERT OR IGNORE`` deduplication.

    Args:
        account_id:  Account primary key string.
        date:        Transaction date string (any format, as parsed from CSV).
        amount:      Amount string (as it appears in the CSV, before conversion).
        description: Description / memo field from the CSV.

    Returns:
        First 16 hex characters of SHA-256 of ``account_id|date|amount|description``.
    """
    payload = f"{account_id}|{date}|{amount}|{description}".encode()
    return sha256(payload).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 2.x  Per-institution normalizers
# ---------------------------------------------------------------------------


def normalize_chase(row: dict, account_id: str) -> Transaction | None:
    """Normalize a Chase credit card / bank CSV row.

    Expected columns: ``Transaction Date``, ``Amount``, ``Description``.
    The ``Amount`` column is already signed (negative = debit).

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key to associate with the transaction.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    date_raw = (row.get("Transaction Date") or "").strip()
    amount_raw = (row.get("Amount") or "").strip()
    description = (row.get("Description") or "").strip() or None

    if not date_raw or not amount_raw:
        return None

    date = _parse_date(date_raw)
    try:
        amount = float(amount_raw.replace(",", ""))
    except ValueError:
        return None

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        raw=json.dumps(dict(row)),
    )


def normalize_discover(row: dict, account_id: str) -> Transaction | None:
    """Normalize a Discover credit card CSV row.

    Expected columns: ``Trans. Date``, ``Amount``, ``Description``.
    Amount sign convention: negative = debit (matches canonical convention).

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    date_raw = (row.get("Trans. Date") or "").strip()
    amount_raw = (row.get("Amount") or "").strip()
    description = (row.get("Description") or "").strip() or None

    if not date_raw or not amount_raw:
        return None

    date = _parse_date(date_raw)
    try:
        amount = float(amount_raw.replace(",", ""))
    except ValueError:
        return None

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        raw=json.dumps(dict(row)),
    )


def normalize_discover_debit(row: dict, account_id: str) -> Transaction | None:
    """Normalize a Discover Cashback Debit (bank account) CSV row.

    Expected columns: ``Date``, ``Amount``, ``Description``.
    Sign convention should be verified against a real export; best-effort
    assumes negative = debit (same as Discover credit).

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    date_raw = (row.get("Date") or "").strip()
    amount_raw = (row.get("Amount") or "").strip()
    description = (row.get("Description") or "").strip() or None

    if not date_raw or not amount_raw:
        return None

    date = _parse_date(date_raw)
    try:
        amount = float(amount_raw.replace(",", ""))
    except ValueError:
        return None

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        raw=json.dumps(dict(row)),
    )


def normalize_citi(row: dict, account_id: str) -> Transaction | None:
    """Normalize a Citi credit card CSV row.

    Expected columns: ``Date``, ``Debit``, ``Credit``, ``Description``.
    Citi uses separate Debit and Credit columns; merged into signed amount:
    ``amount = -abs(debit)`` if Debit is non-empty, else ``+abs(credit)``.

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    date_raw = (row.get("Date") or "").strip()
    debit_raw = (row.get("Debit") or "").strip()
    credit_raw = (row.get("Credit") or "").strip()
    description = (row.get("Description") or "").strip() or None

    if not date_raw:
        return None
    if not debit_raw and not credit_raw:
        return None

    date = _parse_date(date_raw)

    # Determine signed amount: debit → negative, credit → positive
    amount_raw = debit_raw if debit_raw else credit_raw
    try:
        raw_value = float(amount_raw.replace(",", ""))
    except ValueError:
        return None

    if debit_raw:
        amount = -abs(raw_value)
    else:
        amount = abs(raw_value)

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        raw=json.dumps(dict(row)),
    )


def normalize_amex(row: dict, account_id: str) -> Transaction | None:
    """Normalize an American Express credit card CSV row.

    Expected columns: ``Date``, ``Amount``, ``Description``.
    Amex exports positive amounts for charges and negative for payments/credits.
    The normalizer negates to match the canonical convention (negative = debit).

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    date_raw = (row.get("Date") or "").strip()
    amount_raw = (row.get("Amount") or "").strip()
    description = (row.get("Description") or "").strip() or None

    if not date_raw or not amount_raw:
        return None

    date = _parse_date(date_raw)
    try:
        amount = -float(amount_raw.replace(",", ""))
    except ValueError:
        return None

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        raw=json.dumps(dict(row)),
    )


def normalize_robinhood(row: dict, account_id: str) -> Transaction | None:
    """Normalize a Robinhood brokerage activity CSV row.

    Expected columns: ``Activity Date``, ``Amount``, ``Description``.
    Buy transactions are negative (debit); sells and dividends are positive.

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    date_raw = (row.get("Activity Date") or "").strip()
    amount_raw = (row.get("Amount") or "").strip()
    description = (row.get("Description") or "").strip() or None

    if not date_raw or not amount_raw:
        return None

    date = _parse_date(date_raw)
    # Robinhood may use "$" prefix; strip currency symbols
    amount_clean = amount_raw.lstrip("$").replace(",", "")
    try:
        amount = float(amount_clean)
    except ValueError:
        return None

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        raw=json.dumps(dict(row)),
    )


def normalize_apple(row: dict, account_id: str) -> Transaction | None:
    """Normalize an Apple Card CSV row.

    Expected columns: ``Transaction Date``, ``Clearing Date``, ``Description``,
    ``Merchant``, ``Category``, ``Type``, ``Amount (USD)``.

    Amount sign convention: Apple exports positive = charge (debit). The
    normalizer negates the amount to match the canonical convention
    (negative = debit).

    Rows where ``Type == "Payments"`` are skipped (card payoff rows).

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    txn_type = (row.get("Type") or "").strip()
    if txn_type == "Payment":
        return None

    date_raw = (row.get("Transaction Date") or "").strip()
    amount_raw = (row.get("Amount (USD)") or "").strip()
    merchant_name = (row.get("Merchant") or "").strip() or None
    description = (row.get("Description") or "").strip() or None

    if not date_raw or not amount_raw:
        return None

    date = _parse_date(date_raw)
    try:
        amount = -float(amount_raw.replace(",", ""))
    except ValueError:
        return None

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        merchant_name=merchant_name,
        raw=json.dumps(dict(row)),
    )


def normalize_capital_one(row: dict, account_id: str) -> Transaction | None:
    """Normalize a Capital One credit card CSV row.

    Expected columns: ``Transaction Date``, ``Posted Date``, ``Card No.``,
    ``Description``, ``Category``, ``Debit``, ``Credit``.
    Capital One uses separate Debit and Credit columns; merged into signed amount:
    ``amount = -abs(debit)`` if Debit is non-empty, else ``+abs(credit)``.
    Dates are in ``YYYY-MM-DD`` format.

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    date_raw = (row.get("Transaction Date") or "").strip()
    debit_raw = (row.get("Debit") or "").strip()
    credit_raw = (row.get("Credit") or "").strip()
    description = (row.get("Description") or "").strip() or None

    if not date_raw:
        return None
    if not debit_raw and not credit_raw:
        return None

    date = _parse_date(date_raw)

    amount_raw = debit_raw if debit_raw else credit_raw
    try:
        raw_value = float(amount_raw.replace(",", ""))
    except ValueError:
        return None

    if debit_raw:
        amount = -abs(raw_value)
    else:
        amount = abs(raw_value)

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        raw=json.dumps(dict(row)),
    )


def normalize_m1(row: dict, account_id: str) -> Transaction | None:
    """Normalize an M1 Finance CSV row (best-effort).

    Column names are TBD from a real export. This implementation tries common
    column variants: ``Date`` / ``Activity Date``, ``Amount``, ``Description`` /
    ``Type``. Adjust once a real M1 export is available.

    Args:
        row:        A single CSV row dict from ``csv.DictReader``.
        account_id: Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` to skip the row.
    """
    # Try multiple date column names
    date_raw = (
        row.get("Date")
        or row.get("Activity Date")
        or row.get("Transaction Date")
        or ""
    ).strip()
    amount_raw = (row.get("Amount") or "").strip()
    description = (
        row.get("Description") or row.get("Type") or row.get("Activity") or ""
    ).strip() or None

    if not date_raw or not amount_raw:
        return None

    date = _parse_date(date_raw)
    amount_clean = amount_raw.lstrip("$").replace(",", "")
    try:
        amount = float(amount_clean)
    except ValueError:
        return None

    txn_id = generate_csv_id(account_id, date_raw, amount_raw, description or "")
    return Transaction(
        id=txn_id,
        account_id=account_id,
        date=date,
        amount=amount,
        description=description,
        raw=json.dumps(dict(row)),
    )


# ---------------------------------------------------------------------------
# 1.2  NORMALIZERS registry
# ---------------------------------------------------------------------------

NORMALIZERS: dict[str, Callable[[dict, str], Transaction | None]] = {
    "chase": normalize_chase,
    "discover": normalize_discover,
    "discover-debit": normalize_discover_debit,
    "citi": normalize_citi,
    "capital-one": normalize_capital_one,
    "amex": normalize_amex,
    "robinhood": normalize_robinhood,
    "m1": normalize_m1,
    "apple": normalize_apple,
}


# ---------------------------------------------------------------------------
# 1.3  normalize_row dispatch helper
# ---------------------------------------------------------------------------


def normalize_row(
    institution: str, row: dict, account_id: str
) -> Transaction | None:
    """Look up the normalizer for *institution* and apply it to *row*.

    Args:
        institution: Institution key (must exist in :data:`NORMALIZERS`).
        row:         A single CSV row dict from ``csv.DictReader``.
        account_id:  Account primary key.

    Returns:
        A :class:`Transaction` or ``None`` if the row should be skipped.

    Raises:
        ValueError: If *institution* is not a supported key.
    """
    normalizer = NORMALIZERS.get(institution)
    if normalizer is None:
        raise ValueError(
            f"Unsupported institution: '{institution}'. "
            f"Run `finance institutions` to list supported names."
        )
    return normalizer(row, account_id)


# ---------------------------------------------------------------------------
# 3.2  Account auto-creation helper
# ---------------------------------------------------------------------------


def _ensure_account(
    conn: sqlite3.Connection,
    account_id: str | None,
    institution: str,
) -> str:
    """Return a valid account_id, creating a new account record if needed.

    If *account_id* is provided it must already exist in the database.
    If it is ``None``, a new account is created with ``source='csv'`` after
    prompting the user for an account name.

    Args:
        conn:        SQLite connection.
        account_id:  Existing account ID, or ``None`` to auto-create.
        institution: Institution key (used to label the auto-created account).

    Returns:
        The resolved account primary key string.

    Raises:
        ValueError: If a provided *account_id* does not exist in the DB.
    """
    if account_id is not None:
        # Verify it exists
        row = conn.execute(
            "SELECT id FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        if row is None:
            raise ValueError(
                f"Account '{account_id}' not found in the database. "
                "Use `finance accounts` to list existing accounts."
            )
        return account_id

    # Auto-create: prompt for a name
    default_name = f"{institution.title()} (CSV)"
    name = input(f"Account name [{default_name}]: ").strip() or default_name

    new_id = str(uuid.uuid4())

    # Ensure an institution stub exists for CSV-only accounts
    institution_id = f"csv:{institution}"
    conn.execute(
        """
        INSERT OR IGNORE INTO institutions (id, name, url, source)
        VALUES (?, ?, NULL, 'csv')
        """,
        (institution_id, institution.title()),
    )
    conn.execute(
        """
        INSERT INTO accounts (id, institution_id, name, currency, active)
        VALUES (?, ?, ?, 'USD', 1)
        """,
        (new_id, institution_id, name),
    )
    conn.commit()
    print(f"Created account '{name}' with id {new_id}")
    return new_id


# ---------------------------------------------------------------------------
# 3.1  import_csv orchestration
# ---------------------------------------------------------------------------


def import_csv(
    conn: sqlite3.Connection,
    filepath: str,
    institution: str,
    account_id: str | None,
    before_date: str | None = None,
) -> dict:
    """Import transactions from a CSV file into the database.

    Opens *filepath* using :class:`csv.DictReader`, normalizes each row via
    the appropriate institution normalizer, and inserts new rows using
    ``INSERT OR IGNORE`` (skipping duplicates based on the hash-based ID).

    Args:
        conn:        Open SQLite connection.
        filepath:    Path to the CSV file.
        institution: Institution key (e.g. ``"chase"``).  Must exist in
                     :data:`NORMALIZERS`.
        account_id:  Account primary key to associate rows with.  If ``None``,
                     the user is prompted and a new account is created.
        before_date: Optional ISO date string (``YYYY-MM-DD``).  Rows with a
                     transaction date on or after this date are skipped.  Used
                     for historical backfill to avoid duplicating transactions
                     already present via SimpleFIN.

    Returns:
        A dict with keys ``rows_read``, ``rows_imported``, ``rows_skipped``,
        ``rows_cutoff``.

    Raises:
        ValueError: If *institution* is not supported or *account_id* is
                    provided but does not exist.
    """
    if institution not in NORMALIZERS:
        raise ValueError(
            f"Unsupported institution: '{institution}'. "
            f"Run `finance institutions` to list supported names."
        )

    resolved_id = _ensure_account(conn, account_id, institution)

    rows_read = 0
    rows_imported = 0
    rows_skipped = 0
    rows_cutoff = 0

    with open(filepath, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows_read += 1
            try:
                txn = normalize_row(institution, row, resolved_id)
            except Exception:
                rows_skipped += 1
                continue

            if txn is None:
                rows_skipped += 1
                continue

            if before_date is not None and txn.date >= before_date:
                rows_cutoff += 1
                continue

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO transactions
                    (id, account_id, date, amount, description,
                     merchant_name, category, pending, source, raw)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    txn.id,
                    txn.account_id,
                    txn.date,
                    txn.amount,
                    txn.description,
                    txn.merchant_name,
                    txn.category,
                    txn.pending,
                    txn.source,
                    txn.raw,
                ),
            )
            if cursor.rowcount:
                rows_imported += 1
            else:
                rows_skipped += 1

    conn.commit()

    return {
        "rows_read": rows_read,
        "rows_imported": rows_imported,
        "rows_skipped": rows_skipped,
        "rows_cutoff": rows_cutoff,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_date(date_str: str) -> str:
    """Convert a date string to YYYY-MM-DD, handling common US formats.

    Supports:
    - ``YYYY-MM-DD`` (ISO, returned as-is)
    - ``MM/DD/YYYY``
    - ``MM/DD/YY``

    Args:
        date_str: Raw date string from a CSV row.

    Returns:
        The date in ``YYYY-MM-DD`` format.

    Raises:
        ValueError: If the format is not recognised.
    """
    date_str = date_str.strip()

    # ISO format — return directly
    if len(date_str) == 10 and date_str[4] == "-":
        return date_str

    # MM/DD/YYYY or MM/DD/YY
    parts = date_str.split("/")
    if len(parts) == 3:
        month, day, year = parts
        if len(year) == 2:
            year = f"20{year}"
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    # Fallback: return as-is and let the DB constraint catch it
    return date_str
