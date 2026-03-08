"""Two-pass LLM enrichment: merchant normalization, recurring detection, review flagging.

Pass 1 (categorization) lives in finance/ai/categorize.py — unchanged.
Pass 2 (this module) builds merchant clusters from all transactions, sends them
to claude-haiku in batches, and writes back canonical merchant names, recurring
flags, and review flags to the transactions table.

DEPRECATED: Use run_pipeline() from finance.ai.pipeline instead.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import warnings
from statistics import median

import anthropic
from dotenv import load_dotenv

# Import shared helpers from pipeline.py (these were moved there)
from finance.ai.pipeline import _normalize_merchant_key, _build_clusters

load_dotenv()

ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 4096
_CLUSTER_BATCH_SIZE = 40

logger = logging.getLogger(__name__)

ENRICH_MERCHANTS_TOOL = {
    "name": "enrich_merchants",
    "description": "Enrich merchant clusters with canonical names, recurring flags, and review flags",
    "input_schema": {
        "type": "object",
        "properties": {
            "merchants": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "merchant_key": {"type": "string"},
                        "canonical_name": {"type": "string"},
                        "is_recurring": {"type": "integer", "enum": [0, 1]},
                        "transactions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "needs_review": {"type": "integer", "enum": [0, 1]},
                                    "review_reason": {"type": ["string", "null"]},
                                },
                                "required": ["id", "needs_review"],
                            },
                        },
                    },
                    "required": ["merchant_key", "canonical_name", "is_recurring", "transactions"],
                },
            }
        },
        "required": ["merchants"],
    },
}


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
        tools=[ENRICH_MERCHANTS_TOOL],
        tool_choice={"type": "tool", "name": "enrich_merchants"},
    )

    tool_block = next(b for b in message.content if b.type == "tool_use")
    results = tool_block.input["merchants"]

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

    .. deprecated::
        Use run_pipeline() from finance.ai.pipeline instead.

    Returns:
        Total number of transaction rows updated across all batches.
    """
    warnings.warn(
        "enrich_transactions() is deprecated; use run_pipeline() from finance.ai.pipeline instead.",
        DeprecationWarning,
        stacklevel=2,
    )
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
