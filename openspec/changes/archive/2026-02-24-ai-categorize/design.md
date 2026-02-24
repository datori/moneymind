## Context

Transactions from SimpleFIN and CSV import arrive with raw descriptions ("SQ *BLUE BOTTLE", "AMZN Mktp US*2K4LP8"). Without categories, `get_spending_summary(group_by="category")` returns mostly null/Other. This change adds LLM-based categorization, run automatically after each sync/import and available as a manual CLI command.

This change builds on `project-foundation` (schema, `categorized_at` column), `simplefin-sync`, and `csv-import`.

## Goals / Non-Goals

**Goals:**
- Batch categorization using Claude API
- Auto-run after `finance sync` and `finance import`
- Manual `finance categorize` CLI command
- Stable category taxonomy in `finance/ai/categories.py`
- `categorized_at` timestamp tracking

**Non-Goals:**
- User-editable category UI (dashboard, if ever)
- Custom ML model training or fine-tuning
- Sub-categories or hierarchical taxonomy
- Real-time categorization at query time
- Handling categorization failures as blocking errors

## Decisions

### D1: claude-haiku-4-5 for cost efficiency

**Decision:** Use `claude-haiku-4-5-20251001` for categorization tasks.

**Rationale:** Categorization is a straightforward classification task — pick one label from a fixed list given a description. Haiku is perfectly capable and costs ~30x less than Sonnet. At ~1000 new transactions/year, this is negligible cost regardless.

**Alternatives considered:** Sonnet (overkill for classification), local model (complex setup, offline dependency).

---

### D2: Batch size of 50 transactions per API call

**Decision:** Send at most 50 transactions per Claude API call. Process all uncategorized transactions in batches.

**Rationale:** Batching amortizes API call overhead. 50 is large enough to be efficient (~500-800 input tokens) but small enough to keep response size manageable and reduce retry blast radius.

---

### D3: Flat category taxonomy — hardcoded in `categories.py`

**Decision:** Fixed list of 15 categories defined in `finance/ai/categories.py`. Not user-configurable at runtime (user can edit the file directly).

Categories:
- Food & Dining, Groceries, Transportation, Shopping, Entertainment, Travel,
  Health & Fitness, Home & Utilities, Subscriptions & Software, Personal Care,
  Education, Financial, Income, Investment, Other

**Rationale:** A fixed taxonomy provides consistent grouping for trend analysis. User can modify the file if their needs differ. A configuration mechanism adds complexity for a marginal benefit.

---

### D4: Categorization failures are non-blocking

**Decision:** If a Claude API call fails (network error, API error), the batch is logged and skipped. `category` and `categorized_at` remain NULL for those transactions. Sync/import still reports success.

**Rationale:** Categorization is a best-effort enrichment, not core data integrity. Failing sync because categorization failed would be wrong. The user can re-run `finance categorize` manually.

---

### D5: `categorized_at` column tracks when categorization ran

**Decision:** After successfully categorizing a transaction, set `categorized_at = now()` (unix ms) alongside `category`.

**Rationale:** Enables incremental categorization (WHERE `categorized_at IS NULL`), tracking when the taxonomy was last applied, and knowing which transactions survived a re-run.

---

### D6: `finance categorize --all` force re-categorizes everything

**Decision:** By default, `finance categorize` only processes `WHERE categorized_at IS NULL`. With `--all`, it re-categorizes all transactions regardless of `categorized_at`.

**Rationale:** Useful when the taxonomy changes or when past categorization results were poor. Without `--all`, incremental runs are fast and cheap.

---

### D7: Structured JSON response from Claude

**Decision:** The prompt instructs Claude to return a JSON array: `[{"id": "<txn_id>", "category": "<category>"}]`. Parse with `json.loads()`.

**Rationale:** JSON is reliable and easy to parse. The prompt constrains output to a fixed schema, reducing hallucination of free-form text.

## Risks / Trade-offs

- **Haiku misclassification** → Some merchant names are ambiguous. Acceptable for personal use; manual correction via direct SQL or a future `finance fix-category` command.
- **API key required** → `ANTHROPIC_API_KEY` must be set. Users without it can't categorize. `finance categorize` should give a clear error message.
- **Prompt injection risk** → Merchant descriptions could contain text that manipulates the prompt. Mitigated by: (a) the response is only JSON parsed for known fields, (b) this is personal data the user controls.

## Open Questions

None — all decisions resolved.
