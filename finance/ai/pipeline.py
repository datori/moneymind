"""Single-pass cluster-first AI pipeline for transaction enrichment.

Replaces the two-pass categorize + enrich system. A single LLM call per batch
returns category, canonical_name, is_recurring, and per-transaction
needs_review/review_reason for all transactions in a merchant cluster.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import time
from statistics import median

import anthropic
from dotenv import load_dotenv

from finance.ai.categories import CATEGORIES, CATEGORIES_STR

load_dotenv()

ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 8096
_CLUSTER_BATCH_SIZE = 40

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Time helper
# ---------------------------------------------------------------------------


def now_ms() -> int:
    """Return current time as unix milliseconds."""
    return int(time.time() * 1000)


# ---------------------------------------------------------------------------
# Merchant normalization (moved from enrich.py)
# ---------------------------------------------------------------------------


def _normalize_merchant_key(
    merchant_name: str | None, description: str | None
) -> str:
    """Return a normalized, lowercase merchant key for clustering.

    Applies, in order:
    1. Use ``merchant_name`` if non-empty, otherwise fall back to ``description``.
    2. Lowercase.
    3. Strip ``*SUFFIX`` patterns (e.g. ``NETFLIX*AB1234`` -> ``netflix``).
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
# Cluster builder (moved from enrich.py)
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
# Markdown fence stripping (moved from enrich.py)
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


# ---------------------------------------------------------------------------
# LLM pipeline batch
# ---------------------------------------------------------------------------


def _pipeline_batch(clusters: list[dict]) -> tuple[list[dict], int, int]:
    """Send up to 40 merchant clusters to the model, returning category + enrichment.

    Each cluster in ``clusters`` is a dict with keys: ``merchant_key``,
    ``raw_samples``, ``transaction_ids``, ``amounts``.

    Returns:
        A tuple of (results_list, tokens_in, tokens_out) where results_list
        contains dicts with::

            {
                "merchant_key": str,
                "category": str,           # one of CATEGORIES
                "canonical_name": str,
                "is_recurring": 0 | 1,
                "review_ids": [str, ...],  # sparse — only IDs needing review
                "review_reason": str | null
            }

    The response schema uses a sparse ``review_ids`` list rather than echoing
    every transaction ID back — this keeps response tokens bounded even for
    merchants with many transactions.

    Raises:
        anthropic.APIError: On API failure (caller wraps in try/except).
        ValueError: On JSON parse failure (caller wraps in try/except).
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build a compact representation of each cluster for the prompt.
    # Send transaction_ids so the model can return specific IDs in review_ids.
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

    categories_list = CATEGORIES_STR

    prompt = (
        "You are a personal finance assistant analyzing merchant transaction clusters.\n\n"
        "Valid categories (use exactly one per cluster):\n"
        f"{categories_list}\n\n"
        "For each merchant cluster below, return a JSON array of objects with these fields:\n"
        "  - merchant_key: the key from input (unchanged)\n"
        "  - category: exactly one category from the list above\n"
        "  - canonical_name: a clean, human-readable merchant name (e.g. 'Netflix', 'Amazon')\n"
        "  - is_recurring: 1 if this looks like a subscription/recurring charge, 0 otherwise\n"
        "  - review_ids: list of transaction ids (from the input) that need human review due to\n"
        "    unusual amount, possible duplicate, suspicious description, or first large charge.\n"
        "    Use an empty list [] if no transactions need review. DO NOT echo all transaction ids —\n"
        "    only include ids that specifically warrant review.\n"
        "  - review_reason: a single short string explaining the review flag (null if review_ids is empty)\n\n"
        "Return ONLY a JSON array. No explanation, no markdown fences.\n\n"
        f"Merchant clusters:\n{payload_json}"
    )

    message = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )

    tokens_in: int = message.usage.input_tokens
    tokens_out: int = message.usage.output_tokens

    raw_text = message.content[0].text.strip()
    raw_text = _strip_fences(raw_text)

    try:
        results = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse pipeline response as JSON: {exc}\nRaw: {raw_text}"
        ) from exc

    if not isinstance(results, list):
        raise ValueError(f"Expected a JSON array from pipeline batch, got: {type(results)}")

    # Validate category values — fall back to "Other" for unrecognized values
    for item in results:
        category = item.get("category", "Other")
        if category not in CATEGORIES:
            logger.warning(
                "Unrecognised category %r for merchant %r — falling back to 'Other'",
                category,
                item.get("merchant_key"),
            )
            item["category"] = "Other"

    return results, tokens_in, tokens_out


# ---------------------------------------------------------------------------
# DB write-back
# ---------------------------------------------------------------------------


def _apply_results(
    conn: sqlite3.Connection,
    results: list[dict],
    cluster_lookup: dict[str, list[str]],
    run_id: int,
    batch_index: int,
    tokens_in: int,
    tokens_out: int,
    request_summary: str,
    response_summary: str,
) -> int:
    """Write pipeline results back to the transactions table.

    Updates category, categorized_at, merchant_normalized, is_recurring,
    needs_review, and review_reason for every transaction in each cluster.

    Cluster-level fields (category, canonical_name, is_recurring) are applied
    to ALL transaction IDs in the cluster (sourced from ``cluster_lookup``).
    Per-transaction review flags use the sparse ``review_ids`` list from the
    model response — only listed IDs get needs_review=1.

    Also inserts a run_steps row for this write-results operation.

    Returns the number of transaction rows updated.
    """
    step_start = now_ms()
    updated = 0
    categorized_at = now_ms()

    for cluster_result in results:
        merchant_key: str = cluster_result.get("merchant_key", "")
        category: str = cluster_result.get("category", "Other")
        if category not in CATEGORIES:
            category = "Other"
        canonical_name: str = cluster_result.get("canonical_name", "")
        is_recurring: int = int(bool(cluster_result.get("is_recurring", 0)))
        review_ids: set[str] = set(cluster_result.get("review_ids") or [])
        review_reason: str | None = cluster_result.get("review_reason") or None

        # All transaction IDs for this merchant come from our own cluster data,
        # not from the model response — avoids echoing thousands of IDs back.
        all_txn_ids = cluster_lookup.get(merchant_key, [])

        for txn_id in all_txn_ids:
            needs_review: int = 1 if txn_id in review_ids else 0
            txn_review_reason: str | None = review_reason if needs_review else None

            conn.execute(
                """
                UPDATE transactions
                SET category            = ?,
                    categorized_at      = ?,
                    merchant_normalized = ?,
                    is_recurring        = ?,
                    needs_review        = ?,
                    review_reason       = ?
                WHERE id = ?
                """,
                (
                    category,
                    categorized_at,
                    canonical_name,
                    is_recurring,
                    needs_review,
                    txn_review_reason,
                    txn_id,
                ),
            )
            updated += 1

    conn.commit()

    # Record write-results run_steps row
    write_response_summary = json.dumps({"transactions_updated": updated})
    conn.execute(
        """
        INSERT INTO run_steps
            (run_id, step_type, batch_index, batch_total, started_at, finished_at,
             request_summary, response_summary, tokens_in, tokens_out)
        VALUES (?, 'write-results', ?, NULL, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            batch_index,
            step_start,
            now_ms(),
            request_summary,
            write_response_summary,
            tokens_in,
            tokens_out,
        ),
    )
    conn.commit()

    return updated


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_pipeline(
    conn: sqlite3.Connection,
    emit=None,
    run_sync: bool = True,
) -> int:
    """Run the full enrichment pipeline and return the number of transactions written.

    Steps:
    1. (Optional) Sync from SimpleFIN via sync_all().
    2. Build merchant clusters from all transactions.
    3. Send clusters in batches of 40 to Claude Haiku for category + enrichment.
    4. Write results back to the DB.

    Args:
        conn: Open SQLite connection.
        emit: Optional callable(event: dict) -> None for progress reporting.
              If None, pipeline runs silently.
        run_sync: If True (default), perform a SimpleFIN sync as step 1.

    Returns:
        Total number of transaction rows updated across all batches.
    """
    run_type = "full" if run_sync else "enrich-only"
    run_start = now_ms()

    # Insert run_log row
    cursor = conn.execute(
        "INSERT INTO run_log (run_type, started_at, status) VALUES (?, ?, 'running')",
        (run_type, run_start),
    )
    conn.commit()
    run_id: int = cursor.lastrowid

    def _emit(event: dict) -> None:
        if emit is not None:
            emit(event)

    total_updated = 0

    try:
        # -------------------------------------------------------------------
        # Step 1: Sync (optional)
        # -------------------------------------------------------------------
        if run_sync:
            sync_step_start = now_ms()
            _emit({"type": "step_start", "step": "sync", "ts": sync_step_start, "data": {}})

            # Insert run_steps row for sync (started)
            sync_step_cursor = conn.execute(
                "INSERT INTO run_steps (run_id, step_type, started_at) VALUES (?, 'sync', ?)",
                (run_id, sync_step_start),
            )
            conn.commit()
            sync_step_id = sync_step_cursor.lastrowid

            new_transactions = 0
            sync_error = None
            try:
                from finance.ingestion.sync import sync_all

                sync_result = sync_all(conn)
                new_transactions = sync_result.get("new_transactions", 0)
            except Exception as exc:  # noqa: BLE001
                sync_error = str(exc)
                logger.warning("Sync step failed (non-fatal): %s", exc)

            sync_step_end = now_ms()
            conn.execute(
                "UPDATE run_steps SET finished_at = ?, error_msg = ? WHERE id = ?",
                (sync_step_end, sync_error, sync_step_id),
            )
            conn.commit()

            _emit({
                "type": "step_done",
                "step": "sync",
                "ts": sync_step_end,
                "data": {"new_transactions": new_transactions},
            })

        # -------------------------------------------------------------------
        # Step 2: Build clusters
        # -------------------------------------------------------------------
        cluster_step_start = now_ms()
        _emit({"type": "step_start", "step": "cluster-build", "ts": cluster_step_start, "data": {}})

        clusters = _build_clusters(conn)
        cluster_count = len(clusters)
        # Build lookup {merchant_key -> [transaction_ids]} for use in _apply_results
        cluster_lookup: dict[str, list[str]] = {
            c["merchant_key"]: c["transaction_ids"] for c in clusters
        }

        # Count total transactions across clusters
        transaction_count = sum(len(c["transaction_ids"]) for c in clusters)

        cluster_step_end = now_ms()
        cluster_request_summary = json.dumps({
            "transaction_count": transaction_count,
            "cluster_count": cluster_count,
        })
        conn.execute(
            """
            INSERT INTO run_steps
                (run_id, step_type, started_at, finished_at, request_summary)
            VALUES (?, 'cluster-build', ?, ?, ?)
            """,
            (run_id, cluster_step_start, cluster_step_end, cluster_request_summary),
        )
        conn.commit()

        _emit({
            "type": "step_done",
            "step": "cluster-build",
            "ts": cluster_step_end,
            "data": {"cluster_count": cluster_count, "transaction_count": transaction_count},
        })

        if not clusters:
            logger.info("run_pipeline: no transactions found, nothing to do")
            # Mark run as success
            run_end = now_ms()
            conn.execute(
                "UPDATE run_log SET status = 'success', finished_at = ? WHERE id = ?",
                (run_end, run_id),
            )
            conn.commit()
            _emit({
                "type": "run_done",
                "step": None,
                "ts": run_end,
                "data": {
                    "run_id": run_id,
                    "status": "success",
                    "transactions_updated": 0,
                    "duration_ms": run_end - run_start,
                },
            })
            return 0

        # -------------------------------------------------------------------
        # Step 3: Enrich batches
        # -------------------------------------------------------------------
        batch_total = (len(clusters) + _CLUSTER_BATCH_SIZE - 1) // _CLUSTER_BATCH_SIZE

        for batch_num, i in enumerate(range(0, len(clusters), _CLUSTER_BATCH_SIZE), start=1):
            batch = clusters[i : i + _CLUSTER_BATCH_SIZE]
            batch_start = now_ms()

            _emit({
                "type": "step_start",
                "step": "enrich-batch",
                "ts": batch_start,
                "data": {"batch_index": batch_num, "batch_total": batch_total},
            })

            # Build request summary
            merchant_keys = [c["merchant_key"] for c in batch]
            request_summary_dict = {
                "cluster_count": len(batch),
                "merchant_keys": merchant_keys[:5],
            }
            request_summary = json.dumps(request_summary_dict)

            # Insert run_steps row (started)
            batch_step_cursor = conn.execute(
                """
                INSERT INTO run_steps
                    (run_id, step_type, batch_index, batch_total, started_at, request_summary)
                VALUES (?, 'enrich-batch', ?, ?, ?, ?)
                """,
                (run_id, batch_num, batch_total, batch_start, request_summary),
            )
            conn.commit()
            batch_step_id = batch_step_cursor.lastrowid

            try:
                results, tokens_in, tokens_out = _pipeline_batch(batch)
            except (anthropic.APIError, ValueError) as exc:
                batch_end = now_ms()
                error_msg = str(exc)
                logger.warning("Pipeline batch %d failed — skipping: %s", batch_num, exc)

                conn.execute(
                    "UPDATE run_steps SET finished_at = ?, error_msg = ? WHERE id = ?",
                    (batch_end, error_msg, batch_step_id),
                )
                conn.commit()

                _emit({
                    "type": "error",
                    "step": "enrich-batch",
                    "ts": batch_end,
                    "data": {
                        "batch_index": batch_num,
                        "batch_total": batch_total,
                        "message": error_msg,
                    },
                })
                continue
            except Exception as exc:  # noqa: BLE001
                batch_end = now_ms()
                error_msg = str(exc)
                logger.warning(
                    "Pipeline batch %d unexpected error — skipping: %s", batch_num, exc
                )

                conn.execute(
                    "UPDATE run_steps SET finished_at = ?, error_msg = ? WHERE id = ?",
                    (batch_end, error_msg, batch_step_id),
                )
                conn.commit()

                _emit({
                    "type": "error",
                    "step": "enrich-batch",
                    "ts": batch_end,
                    "data": {
                        "batch_index": batch_num,
                        "batch_total": batch_total,
                        "message": error_msg,
                    },
                })
                continue

            batch_end = now_ms()

            # Build response summary
            categories_assigned = [r.get("category", "Other") for r in results]
            recurring_count = sum(1 for r in results if r.get("is_recurring"))
            response_summary_dict = {
                "cluster_count": len(results),
                "categories_assigned": categories_assigned,
                "recurring_count": recurring_count,
            }
            response_summary = json.dumps(response_summary_dict)

            # Update run_steps row for this enrich-batch
            conn.execute(
                """
                UPDATE run_steps
                SET finished_at       = ?,
                    response_summary  = ?,
                    tokens_in         = ?,
                    tokens_out        = ?
                WHERE id = ?
                """,
                (batch_end, response_summary, tokens_in, tokens_out, batch_step_id),
            )
            conn.commit()

            # Write results to transactions table
            try:
                written = _apply_results(
                    conn,
                    results,
                    cluster_lookup,
                    run_id,
                    batch_num,
                    tokens_in,
                    tokens_out,
                    request_summary,
                    response_summary,
                )
                total_updated += written
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Pipeline batch %d write failed — skipping: %s", batch_num, exc
                )

            _emit({
                "type": "step_done",
                "step": "enrich-batch",
                "ts": batch_end,
                "data": {
                    "batch_index": batch_num,
                    "batch_total": batch_total,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "request_summary": request_summary_dict,
                    "response_summary": response_summary_dict,
                },
            })

        # -------------------------------------------------------------------
        # All batches complete — mark run as success
        # -------------------------------------------------------------------
        run_end = now_ms()
        conn.execute(
            "UPDATE run_log SET status = 'success', finished_at = ? WHERE id = ?",
            (run_end, run_id),
        )
        conn.commit()

        logger.info("run_pipeline: updated %d transaction(s)", total_updated)

        _emit({
            "type": "run_done",
            "step": None,
            "ts": run_end,
            "data": {
                "run_id": run_id,
                "status": "success",
                "transactions_updated": total_updated,
                "duration_ms": run_end - run_start,
            },
        })

        return total_updated

    except Exception as exc:
        # Catastrophic failure — mark run as error
        run_end = now_ms()
        error_msg = str(exc)
        try:
            conn.execute(
                "UPDATE run_log SET status = 'error', finished_at = ?, error_msg = ? WHERE id = ?",
                (run_end, error_msg, run_id),
            )
            conn.commit()
        except Exception:  # noqa: BLE001
            pass

        _emit({
            "type": "error",
            "step": None,
            "ts": run_end,
            "data": {"message": error_msg},
        })

        raise
