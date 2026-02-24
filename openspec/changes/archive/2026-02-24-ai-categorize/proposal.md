# Proposal: ai-categorize

## Problem / Motivation

Raw transactions have descriptions like "SQ *BLUE BOTTLE COFFEE" or "AMZN Mktp US*2K4LP8". The `get_spending_summary()` tool is only useful if transactions have meaningful categories. LLM-based categorization is the most robust approach — it handles messy merchant names better than regex rules.

## Goals

- Implement `finance/ai/categorize.py` — batch categorization using Claude API
- Auto-categorize new transactions on sync (uncategorized rows only)
- Expose `finance categorize` CLI command for manual re-runs
- Define a consistent category taxonomy stored in config
- Avoid re-categorizing already-categorized transactions (unless forced)

## Non-goals

- User-editable categories via UI (that's `dashboard`, if ever)
- Fine-tuning or training a custom model
- Real-time categorization at query time — categories are pre-stored on transaction rows
- Hierarchical categories (e.g., Food > Restaurants) — flat list is sufficient

## Approach

### Category Taxonomy

A fixed flat list, stored in `finance/ai/categories.py`:

```
Food & Dining
Groceries
Transportation
Shopping
Entertainment
Travel
Health & Fitness
Home & Utilities
Subscriptions
Personal Care
Education
Financial (transfers, payments, fees)
Income (salary, deposits, reimbursements)
Investment (buy/sell/dividend)
Other
```

### Categorization Strategy

Batch transactions into groups of ~50, send to Claude with a structured prompt:
```
Given these transactions, assign each one a category from the list.
Return a JSON array of { id, category } objects.

Transactions:
[{ id, date, amount, description, merchant_name }, ...]
```

Use `claude-haiku-4-5` for cost efficiency (categorization is straightforward, doesn't need Sonnet).

### Integration Points

1. **On sync** (`simplefin-sync`): after upserting new transactions, call `categorize_uncategorized(conn)` automatically
2. **On CSV import** (`csv-import`): same — categorize new rows after import
3. **Manual re-run**: `finance categorize [--all]` to re-categorize everything (useful when taxonomy changes)

### Batching & Cost

~1000 transactions/year for a typical person. At ~500 tokens per batch of 50:
- ~20 API calls/year for new transactions (incremental)
- ~20 API calls for a full re-run
- Haiku pricing: negligible

### Implementation

```python
async def categorize_uncategorized(conn: Connection) -> int:
    """Categorize all transactions with category IS NULL. Returns count updated."""

async def categorize_all(conn: Connection) -> int:
    """Re-categorize all transactions. Returns count updated."""

async def categorize_batch(transactions: list[dict]) -> list[dict]:
    """Send batch to Claude, return [{ id, category }]."""
```

## Open Questions

- Should we store a `categorized_at` timestamp on each transaction? Useful for knowing when re-categorization was last run. Worth adding a column.
- What about transactions the LLM misclassifies? For now, accept it — manual correction can be added later (update the row directly in SQLite). A `finance fix-category <txn_id> <category>` CLI command would be trivial to add.
- Should the category list be user-configurable (in `.env` or a config file) or hardcoded? Hardcoded list in `categories.py` is simplest. User can edit the file if needed.
