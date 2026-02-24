## Context

SimpleFIN coverage for brokerage/fintech accounts is uncertain. CSV export is the universal fallback and also the mechanism for historical backfill. Each institution uses a different column format. This change builds a normalizer pipeline that maps institution-specific CSV formats to the canonical transaction schema.

This change builds on `project-foundation` (DB schema) and is compatible with `simplefin-sync` (same dedup logic, same amount sign convention).

## Goals / Non-Goals

**Goals:**
- CSV ingestion pipeline with per-institution normalizers
- Support Chase, Discover, Citi, Amex (credit cards) and Discover Cashback Debit (bank)
- Best-effort support for Robinhood and M1 (investment)
- Hash-based transaction IDs for deduplication
- `finance import <file> --institution <name>` CLI command
- `finance institutions` command listing supported institution names

**Non-Goals:**
- Auto-detecting institution from file contents
- OFX/QFX/QIF format support
- Full coverage of every edge case on every institution format (iterative)
- Categorization (that's `ai-categorize`)

## Decisions

### D1: Explicit `--institution` flag, no auto-detection

**Decision:** The institution name must be explicitly specified. No attempt to detect from file contents, column names, or filename.

**Rationale:** Auto-detection is fragile and creates silent misclassification bugs. For a personal tool where the user knows which file came from where, explicit is safer and simpler. The `finance institutions` command lists valid names.

---

### D2: Transaction ID = sha256(account_id|date|amount|description)[:16]

**Decision:** CSV transactions are given a deterministic hash-based ID:
```python
sha256(f"{account_id}|{date}|{amount}|{description}".encode()).hexdigest()[:16]
```

**Rationale:** CSV rows have no stable IDs. This hash is deterministic — importing the same file twice won't create duplicates. It uses the same `INSERT OR IGNORE` dedup path as SimpleFIN transactions.

**Alternatives considered:** Row number hash (not deterministic across re-exports), UUID (not deterministic, would create duplicates on re-import).

---

### D3: Each institution normalizer is a standalone function

**Decision:**
```python
NORMALIZERS: dict[str, Callable[[dict], Transaction | None]] = {
    "chase": normalize_chase,
    "discover": normalize_discover,
    "discover-debit": normalize_discover_debit,
    "citi": normalize_citi,
    "amex": normalize_amex,
    "robinhood": normalize_robinhood,
    "m1": normalize_m1,
}
```

Each function takes a CSV row dict (from `csv.DictReader`) and returns a `Transaction` dataclass (or `None` to skip the row). Normalizers handle sign conventions, date parsing, and column mapping.

**Rationale:** One function per institution is easy to add to, easy to test, and easy to debug when a specific format breaks.

---

### D4: Account auto-creation on first import

**Decision:** If no `--account` flag is given, `finance import` creates a new account record with `source='csv'` and prompts the user to confirm the account name. If `--account <id>` is given, that account must exist.

**Rationale:** On first use of CSV import for a non-SimpleFIN account, the account doesn't yet exist in the DB. Auto-creation with confirmation avoids requiring a manual `finance add-account` step before importing.

---

### D5: Citi separate Debit/Credit columns merged into signed amount

**Decision:** Citi exports use separate `Debit` and `Credit` columns. Normalizer: `amount = -float(debit) if debit else float(credit)`.

**Rationale:** Matches the canonical negative=debit convention across all sources.

---

### D6: Investment CSV rows treated as regular transactions

**Decision:** Robinhood and M1 buy/sell/dividend rows are mapped to regular transactions. Buy = debit (negative amount), sell/dividend = credit (positive).

**Rationale:** Keeping a single `transactions` table for all account types avoids schema complexity. The `category` field (later populated by AI) will distinguish investment activity.

## Risks / Trade-offs

- **Hash-based IDs are not globally unique** → Extremely unlikely collision for personal finance data, but not theoretically impossible. Acceptable risk.
- **Institution format drift** → Banks occasionally change their CSV column names. Normalizers will break and need updating. The error should be clear (missing column key).
- **Investment CSV complexity** → Robinhood/M1 formats may have multiple row types (buy, sell, dividend, transfer). Initial normalizer handles common cases; edge cases may need iterative fixes.

## Open Questions

None — all decisions resolved.
