"""LLM-based transaction categorization using the Anthropic API."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import warnings

import anthropic
from dotenv import load_dotenv

from finance.ai.categories import CATEGORIES, CATEGORIES_STR

load_dotenv()

ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

_MODEL = "claude-haiku-4-5-20251001"
_BATCH_SIZE = 25

logger = logging.getLogger(__name__)


def categorize_batch(transactions: list[dict]) -> list[dict]:
    """Send up to 50 transactions to Claude and return categorized results.

    Args:
        transactions: List of transaction dicts with keys: id, date, amount,
            description, merchant_name.

    Returns:
        List of dicts with keys ``id`` and ``category``.

    Raises:
        anthropic.APIError: On API communication failure.
        ValueError: If the response cannot be parsed as a JSON array.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    txn_json = json.dumps(
        [
            {
                "id": t.get("id"),
                "date": t.get("date"),
                "amount": t.get("amount"),
                "description": t.get("description") or "",
                "merchant_name": t.get("merchant_name") or "",
            }
            for t in transactions
        ],
        indent=2,
    )

    prompt = (
        f"Categorize each transaction into exactly one of these categories:\n"
        f"{CATEGORIES_STR}\n\n"
        f"Return ONLY a JSON array of objects with keys \"id\" and \"category\".\n"
        f"Do not include any explanation or extra text — just the JSON array.\n\n"
        f"Transactions:\n{txn_json}"
    )

    message = client.messages.create(
        model=_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        # Drop first and last fence lines
        inner = []
        in_fence = False
        for line in lines:
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            inner.append(line)
        raw_text = "\n".join(inner).strip()

    try:
        results = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse categorization response as JSON: {exc}\nRaw: {raw_text}") from exc

    if not isinstance(results, list):
        raise ValueError(f"Expected a JSON array, got: {type(results)}")

    # Validate and normalise category values (task 2.5)
    validated: list[dict] = []
    for item in results:
        txn_id = item.get("id")
        category = item.get("category", "Other")
        if category not in CATEGORIES:
            logger.warning("Unrecognised category %r for txn %s — falling back to 'Other'", category, txn_id)
            category = "Other"
        validated.append({"id": txn_id, "category": category})

    return validated


def _categorize(conn: sqlite3.Connection, where_clause: str) -> int:
    """Internal helper: categorize transactions matching *where_clause*.

    Args:
        conn: Open SQLite connection.
        where_clause: SQL WHERE clause to select transactions (e.g.
            ``"WHERE categorized_at IS NULL"`` or ``""`` for all).

    Returns:
        Total number of transactions updated.
    """
    rows = conn.execute(
        f"SELECT id, date, amount, description, merchant_name FROM transactions {where_clause}"
    ).fetchall()

    if not rows:
        return 0

    transactions = [dict(r) for r in rows]
    total_updated = 0
    now_ms = int(time.time() * 1000)

    for i in range(0, len(transactions), _BATCH_SIZE):
        batch = transactions[i : i + _BATCH_SIZE]
        try:
            results = categorize_batch(batch)
        except Exception as exc:
            logger.warning("Categorization batch %d failed — skipping: %s", i // _BATCH_SIZE + 1, exc)
            continue

        for item in results:
            txn_id = item["id"]
            category = item["category"]
            conn.execute(
                "UPDATE transactions SET category = ?, categorized_at = ? WHERE id = ?",
                (category, now_ms, txn_id),
            )
            total_updated += 1

        conn.commit()

    return total_updated


def categorize_uncategorized(conn: sqlite3.Connection) -> int:
    """Categorize all transactions where ``categorized_at IS NULL``.

    Processes in batches of 50. Logs and skips any batch that fails.

    .. deprecated::
        Use run_pipeline() from finance.ai.pipeline instead.

    Args:
        conn: Open SQLite connection.

    Returns:
        Total number of transactions updated.
    """
    warnings.warn(
        "categorize_uncategorized() is deprecated; use run_pipeline() from finance.ai.pipeline instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _categorize(conn, "WHERE categorized_at IS NULL")


def categorize_all(conn: sqlite3.Connection) -> int:
    """Re-categorize all transactions regardless of ``categorized_at``.

    Processes in batches of 50. Logs and skips any batch that fails.

    .. deprecated::
        Use run_pipeline() from finance.ai.pipeline instead.

    Args:
        conn: Open SQLite connection.

    Returns:
        Total number of transactions updated.
    """
    warnings.warn(
        "categorize_all() is deprecated; use run_pipeline() from finance.ai.pipeline instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _categorize(conn, "")
