"""Two-pass LLM enrichment: merchant normalization, recurring detection, review flagging.

Pass 1 (categorization) lives in finance/ai/categorize.py — unchanged.
Pass 2 (this module) builds merchant clusters from all transactions, sends them
to claude-haiku in batches, and writes back canonical merchant names, recurring
flags, and review flags to the transactions table.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from statistics import median

import anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 4096
_CLUSTER_BATCH_SIZE = 40

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 2.1  Merchant normalization
# ---------------------------------------------------------------------------


def _normalize_merchant_key(
    merchant_name: str | None, description: str | None
) -> str:
    """Return a normalized, lowercase merchant key for clustering.

    Applies, in order:
    1. Use ``merchant_name`` if non-empty, otherwise fall back to ``description``.
    2. Lowercase.
    3. Strip ``*SUFFIX`` patterns (e.g. ``NETFLIX*AB1234`` → ``netflix``).
    4. Strip common TLDs: ``.com``, ``.net``, ``.org``.
    5. Collapse whitespace and strip leading/trailing punctuation.
    """
    raw: str = (merchant_name or description or "").strip()
    if not raw:
        return "unknown"

    # Lowercase
    key = raw.lower()

    # Strip *ANYTHING (trailing asterisk with optional suffix)
    key = re.sub(r"\*.*", "", key)

    # Strip .com / .net / .org (with optional trailing content)
    key = re.sub(r"\.(com|net|org)\b.*", "", key)

    # Collapse any remaining whitespace
    key = " ".join(key.split())

    # Strip leading/trailing punctuation
    key = key.strip(".-_/#&")

    return key or "unknown"


# ---------------------------------------------------------------------------
# 3.1 / 3.2  Cluster builder
# ---------------------------------------------------------------------------


def _build_clusters(conn: sqlite3.Connection) -> list[dict]:
    """Group all transactions by normalized merchant key.

    Returns a list of cluster dicts::

        {
            "merchant_key": str,
            "raw_samples": list[str],   # up to 5 distinct descriptions seen
            "transaction_ids": list[str],
            "amounts": list[float],
        }

    Clusters with only a single transaction are included — single-occurrence
    merchants can still be recurring (first sync) or deserve review.
    """
    rows = conn.execute(
        "SELECT id, merchant_name, description, amount FROM transactions"
    ).fetchall()

    clusters: dict[str, dict] = {}
    for row in rows:
        key = _normalize_merchant_key(row["merchant_name"], row["description"])
        if key not in clusters:
            clusters[key] = {
                "merchant_key": key,
                "raw_samples": [],
                "_raw_set": set(),
                "transaction_ids": [],
                "amounts": [],
            }
        c = clusters[key]
        raw = (row["merchant_name"] or row["description"] or "").strip()
        if raw and raw not in c["_raw_set"] and len(c["raw_samples"]) < 5:
            c["raw_samples"].append(raw)
            c["_raw_set"].add(raw)
        c["transaction_ids"].append(row["id"])
        c["amounts"].append(row["amount"])

    # Drop the internal dedup set before returning
    result = []
    for c in clusters.values():
        del c["_raw_set"]
        result.append(c)

    return result


# ---------------------------------------------------------------------------
# 4.1 / 4.2 / 4.3  LLM enrichment batch
# ---------------------------------------------------------------------------


def _strip_fences(text: str) -> str:
    """Strip markdown code fences from model output (mirrors categorize.py)."""
    if text.startswith("```"):
        lines = text.splitlines()
        inner = []
        in_fence = False
        for line in lines:
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            inner.append(line)
        return "\n".join(inner).strip()
    return text


def _enrich_batch(clusters: list[dict]) -> list[dict]:
    """Send up to 40 merchant clusters to the model and return enrichment results.

    Each cluster in ``clusters`` is a dict with keys: ``merchant_key``,
    ``raw_samples``, ``transaction_ids``, ``amounts``.

    Returns a list of result dicts::

        {
            "merchant_key": str,
            "canonical_name": str,
            "is_recurring": 0 | 1,
            "transactions": [
                {"id": str, "needs_review": 0 | 1, "review_reason": str | null}
            ]
        }

    Raises:
        anthropic.APIError: On API failure (caller wraps in try/except).
        ValueError: On JSON parse failure (caller wraps in try/except).
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build a compact representation of each cluster for the prompt
    cluster_payload = []
    for c in clusters:
        cluster_payload.append(
            {
                "merchant_key": c["merchant_key"],
                "raw_samples": c["raw_samples"],
                "transaction_ids": c["transaction_ids"],
                "amounts": c["amounts"],
            }
        )

    payload_json = json.dumps(cluster_payload, indent=2)

    prompt = (
        "You are a personal finance assistant analyzing merchant transaction clusters.\n\n"
        "For each merchant cluster below, return a JSON array of objects with these fields:\n"
        "  - merchant_key: the key from input (unchanged)\n"
        "  - canonical_name: a clean, human-readable merchant name (e.g. 'Netflix', 'Amazon')\n"
        "  - is_recurring: 1 if this looks like a subscription/recurring charge, 0 otherwise\n"
        "  - transactions: array of objects, one per transaction_id in the cluster:\n"
        "      - id: the transaction id\n"
        "      - needs_review: 1 if this specific transaction should be flagged for human review "
        "(unusual amount, possible duplicate, suspicious description, first appearance of "
        "large charge, etc.), 0 otherwise\n"
        "      - review_reason: short explanation string if needs_review=1, null otherwise\n\n"
        "Return ONLY a JSON array. No explanation, no markdown fences.\n\n"
        f"Merchant clusters:\n{payload_json}"
    )

    message = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()
    raw_text = _strip_fences(raw_text)

    try:
        results = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse enrichment response as JSON: {exc}\nRaw: {raw_text}"
        ) from exc

    if not isinstance(results, list):
        raise ValueError(f"Expected a JSON array from enrichment, got: {type(results)}")

    return results


# ---------------------------------------------------------------------------
# 5.1  DB write-back
# ---------------------------------------------------------------------------


def _write_results(conn: sqlite3.Connection, results: list[dict]) -> int:
    """Write enrichment results back to the transactions table.

    Updates ``merchant_normalized``, ``is_recurring``, ``needs_review``, and
    ``review_reason`` for every transaction ID referenced in *results*.

    Returns the number of transaction rows updated.
    """
    updated = 0
    for cluster_result in results:
        canonical_name: str = cluster_result.get("canonical_name", "")
        is_recurring: int = int(bool(cluster_result.get("is_recurring", 0)))
        txn_results: list[dict] = cluster_result.get("transactions", [])

        for txn in txn_results:
            txn_id = txn.get("id")
            if not txn_id:
                continue
            needs_review: int = int(bool(txn.get("needs_review", 0)))
            review_reason: str | None = txn.get("review_reason") or None

            conn.execute(
                """
                UPDATE transactions
                SET merchant_normalized = ?,
                    is_recurring        = ?,
                    needs_review        = ?,
                    review_reason       = ?
                WHERE id = ?
                """,
                (canonical_name, is_recurring, needs_review, review_reason, txn_id),
            )
            updated += 1

    conn.commit()
    return updated


# ---------------------------------------------------------------------------
# 5.2 / 5.3  Public entry point
# ---------------------------------------------------------------------------


def enrich_transactions(conn: sqlite3.Connection) -> int:
    """Run the full enrichment pipeline and return the number of transactions written.

    1. Build merchant clusters from all transactions (Python normalization).
    2. Send clusters in batches of up to 40 to the LLM for canonical naming,
       recurring detection, and review flagging.
    3. Write results back to the DB.

    Every transaction receives a ``merchant_normalized`` value (canonical_name
    from the model).  Failing batches are logged and skipped; the pipeline is
    non-fatal.

    Returns:
        Total number of transaction rows updated across all batches.
    """
    clusters = _build_clusters(conn)
    if not clusters:
        logger.info("enrich_transactions: no transactions found, nothing to do")
        return 0

    total_updated = 0

    for i in range(0, len(clusters), _CLUSTER_BATCH_SIZE):
        batch = clusters[i : i + _CLUSTER_BATCH_SIZE]
        batch_num = i // _CLUSTER_BATCH_SIZE + 1
        try:
            results = _enrich_batch(batch)
        except (anthropic.APIError, ValueError) as exc:
            logger.warning(
                "Enrichment batch %d failed — skipping: %s", batch_num, exc
            )
            continue
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Enrichment batch %d unexpected error — skipping: %s", batch_num, exc
            )
            continue

        try:
            written = _write_results(conn, results)
            total_updated += written
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Enrichment batch %d write failed — skipping: %s", batch_num, exc
            )

    logger.info("enrich_transactions: updated %d transaction(s)", total_updated)
    return total_updated
