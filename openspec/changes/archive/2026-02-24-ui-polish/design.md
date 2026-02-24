## Context

The finance dashboard is a single-user FastAPI/Jinja2 application served with Tailwind CSS via CDN. The three changes in this batch are independent of each other and touch three distinct layers: templates (UI), ingestion (CSV normalizer), and CLI. No new dependencies are required, and the data model is unchanged.

Current state:
- Category values in the `transactions` table are plain strings (e.g., `"Food & Dining"`). Templates render them as unstyled text.
- The `NORMALIZERS` dict in `finance/ingestion/csv_import.py` has 7 entries. Apple Card is absent.
- `finance accounts` is implemented as a flat `@main.command`. There is no accounts group or delete subcommand.

## Goals / Non-Goals

**Goals:**
- Add inline Tailwind badge spans to category cells in `transactions.html` and `spending.html` using a deterministic category→color mapping.
- Add a `normalize_apple` function and register it under key `"apple"` in `NORMALIZERS`.
- Convert `finance accounts` from a plain command to a Click group with `list` (existing behavior) and `delete` subcommands.

**Non-Goals:**
- Dark mode or theme switching.
- Modifying Chart.js colors to match badge colors (separate concern).
- Apple Card Installments or other Apple Pay transaction types beyond standard charges.
- Cascading institution deletion (only account + its dependent rows).
- Soft-delete / archive; this is a hard delete.
- Undo or audit logging of deleted accounts.

## Decisions

### Decision 1: Inline Jinja2 mapping dict vs. server-side template variable

**Options considered:**
- A: Pass a `category_colors` dict from the route handler into each template.
- B: Hardcode the mapping in each template using a Jinja2 `{% set %}` dict literal or an `if/elif` chain.

**Chosen: B (template-side mapping).** The mapping is purely presentational and doesn't belong in business logic. Jinja2 supports dict literals in `{% set %}`, so a single `{% set %}` block at the top of each template keeps the change self-contained to HTML files. The route handlers do not need to change.

Implementation note: Jinja2 does not support dict literals with `{% set color_map = {"key": "val"} %}` in all versions. Use a `{% set %}` with `namespace` or an `if/elif` chain. Given Tailwind's CDN purge limitation (Tailwind CDN includes all classes), an `if/elif` chain is safe and explicit. For maintainability, a Jinja2 macro in a dedicated file is preferred — it centralises the mapping and can be imported by any template.

**Final approach:** Define a `category_badge(cat)` macro in a standalone `finance/web/templates/_macros.html` file. Child templates import it with `{% from "_macros.html" import category_badge %}`. **Do not define the macro in `base.html`** — a child template that does both `{% extends "base.html" %}` and `{% from "base.html" import ... %}` causes Jinja2 to load `base.html` in module mode (without the request context), resulting in `UndefinedError: 'request' is undefined` for any template that uses `request.url.path` in the nav.

### Decision 2: Apple Card amount sign convention

Apple Card CSV exports use **positive = charge (debit)**, opposite to the canonical convention (negative = debit). The normalizer must negate the parsed amount.

Payment rows (Type == "Payments") are card payoffs — not purchases. These SHALL be skipped by returning `None`.

The `Merchant` column contains the clean merchant name; `Description` contains a longer memo. The normalizer uses `Merchant` for `merchant_name` and `Description` for `description`, matching the enriched-data pattern used by SimpleFIN.

### Decision 3: `finance accounts` group conversion

Currently `accounts` is `@main.command("accounts")`. Converting it to `@main.group("accounts")` with `invoke_without_command=True` preserves backwards compatibility: `finance accounts` (no subcommand) continues to list accounts, while `finance accounts delete <id>` runs the new subcommand.

The `list` subcommand is added as an explicit alias so users can also do `finance accounts list`. The original handler logic moves unchanged into the list implementation.

### Decision 4: Deletion cascade order

SQLite enforces FK constraints only if `PRAGMA foreign_keys = ON`, which is not set in `db.py`. Regardless, we delete dependent rows before the account row to be correct by convention:

1. `DELETE FROM credit_limits WHERE account_id = ?`
2. `DELETE FROM sync_state WHERE account_id = ?`
3. `DELETE FROM transactions WHERE account_id = ?`
4. `DELETE FROM balances WHERE account_id = ?`
5. `DELETE FROM accounts WHERE id = ?`

All five statements run inside a single transaction for atomicity.

### Decision 5: Confirmation guard for `accounts delete`

A `--confirm` flag bypasses the interactive prompt (useful for scripting). Without the flag, Click prompts `"Delete account '<name>' and all associated data? [y/N]"`. If the user answers anything other than `y`/`yes`, the command exits 0 with "Aborted." No rows are deleted.

## Risks / Trade-offs

- **Badge macro in `_macros.html`** → If a new category is introduced in `finance/ai/categories.py` without a corresponding badge entry, the badge will fall back to the gray fallback style. This is safe but may be mildly confusing. Mitigation: keep the macro's default branch explicit.
- **Apple Card column name brittleness** → Apple may change CSV column names in future exports. Mitigation: the normalizer logs a warning and returns `None` (skips row) if required columns are missing, consistent with other normalizers.
- **accounts group conversion** → The `--json` flag and help text must be preserved exactly when moving the existing command logic into the `list` subcommand. Risk of subtle breakage in the default-invocation path. Mitigation: cover in task checklist.
- **Hard delete is irreversible** → Accidental deletion of an account removes all history. Mitigation: mandatory confirmation prompt; `--confirm` flag requires deliberate opt-in.

## Migration Plan

No schema changes. No data migrations. Deployment is:
1. Apply template changes → restart `finance-dashboard`.
2. Apply `csv_import.py` change → available immediately on next `finance import`.
3. Apply `cli.py` change → available immediately.

Rollback: revert the three file edits; no DB state was changed by the code changes themselves.
