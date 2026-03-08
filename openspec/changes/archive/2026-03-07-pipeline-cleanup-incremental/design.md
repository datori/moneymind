## Context

The pipeline currently has two independent enrichment paths:

1. **Legacy two-pass** (deprecated): `sync_all()` → `categorize_uncategorized()` → `enrich_transactions()`. Still active because `sync_all()` and `import_csv()` both call `categorize_uncategorized()` internally, and the CLI `_sync_run()` calls `enrich_transactions()` after sync.

2. **Modern single-pass**: `run_pipeline()` → builds clusters from ALL transactions → sends ALL clusters to LLM in batches of 40 → writes results. This is the canonical path exposed via `finance pipeline` and the web dashboard.

The problem: running `finance sync` triggers path 1, then running `finance pipeline` triggers path 2, which re-processes every transaction the LLM already saw. Path 1 has no cost tracking. As the database grows, path 2's cost scales linearly with total transaction count even though only a handful of new transactions were added.

## Goals / Non-Goals

**Goals:**
- Make sync and import purely about data ingestion — no LLM calls
- Make `run_pipeline()` incremental by default — only send clusters with new transactions
- Preserve full clustering context so LLM inference quality is unchanged
- Maintain `--full` override for taxonomy changes or model upgrades
- Track all LLM costs in `run_log`/`run_steps`

**Non-Goals:**
- Deleting the deprecated `categorize.py` / `enrich.py` modules (they remain for backward compatibility)
- Changing the LLM prompt format or model (that's the structured-llm-output change)
- Adding concurrent batch processing
- Modifying the web dashboard UI

## Decisions

### Decision 1: Remove auto-categorize from sync and import, not wrap it

**Choice**: Delete the `categorize_uncategorized()` calls from `sync_all()` and `import_csv()` entirely, rather than wrapping them in the modern pipeline.

**Rationale**: Sync and import should be pure data operations. Coupling LLM calls into data ingestion means you can't sync without spending API tokens, and failures in categorization could mask sync issues. The user explicitly runs `finance pipeline` (or the web dashboard "Run Pipeline" button) when they want enrichment.

**Alternative considered**: Auto-run `run_pipeline()` after sync. Rejected because it couples concerns and forces LLM cost on every sync, even when the user just wants fresh data.

### Decision 2: Hybrid incremental — cluster ALL, filter before sending

**Choice**: `_build_clusters()` continues to load ALL transactions for cluster context. A new filtering step removes clusters where every transaction already has `categorized_at IS NOT NULL`. Only filtered clusters go to the LLM.

**Rationale**: The clustering context (all historical amounts, raw samples) is what lets the LLM accurately identify recurring patterns and assign categories. If we only clustered new transactions, a single new Netflix charge would be sent alone without the 12-month history that makes the "recurring subscription" classification obvious.

**Implementation**:
```
_build_clusters(conn)           → all clusters (cheap, Python-only)
_filter_clusters(clusters, conn) → only clusters with ≥1 uncategorized txn
```

The filter checks the `categorized_at` column: if ALL transaction IDs in a cluster have non-null `categorized_at`, the cluster is skipped.

**Alternative considered**: Only loading uncategorized transactions into clusters. Rejected because it loses the historical context that improves LLM accuracy.

### Decision 3: Write-back applies to entire cluster, not just new transactions

**Choice**: When a filtered cluster is processed, results are written back to ALL transactions in the cluster — not just the uncategorized ones.

**Rationale**: This ensures consistency. If a new transaction shifts the LLM's assessment of a merchant (e.g., from "Other" to "Subscriptions"), all transactions for that merchant update. It also handles the case where a previous pipeline run was interrupted — partially-categorized clusters get fully resolved on the next run.

**Trade-off**: Slightly more DB writes than strictly necessary, but SQLite UPDATE on indexed columns is negligible.

### Decision 4: `--full` flag bypasses the filter

**Choice**: `run_pipeline()` accepts a `full: bool = False` parameter. When `True`, no cluster filtering occurs — all clusters go to the LLM. The CLI `finance pipeline --full` maps to this.

**Use cases**: Taxonomy changes, model upgrades, or suspecting the LLM miscategorized merchants on a previous run.

## Risks / Trade-offs

**[Risk: User forgets to run pipeline after sync]** → The CLI `finance sync` output will include a reminder: "Run `finance pipeline` to categorize new transactions." The web dashboard already has a separate "Run Pipeline" button.

**[Risk: Incremental mode misses merchants that need re-evaluation]** → If all transactions in a cluster are categorized, the cluster is skipped even if the categorization was wrong. Mitigation: `--full` flag, and the `fix-category` command for individual corrections.

**[Risk: Breaking change for users who expect auto-categorize after sync]** → This is intentional. The deprecated path was silently consuming tokens without cost tracking. The new behavior is more predictable and transparent.
