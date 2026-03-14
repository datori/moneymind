"""Seed script for demo.db — generates a complex, realistic synthetic scenario.

Scenario: A 30-something professional with a diverse financial picture —
checking + HYSA + two credit cards + taxable brokerage + 401(k). Thirteen
months of history, a mid-year market correction with recovery, active
subscriptions in various states, travel spending, medical bills, and a
handful of transactions flagged for review.

Usage:
    python -m finance.demo.seed

Overwrites data/demo.db on each run (idempotent).
"""

from __future__ import annotations

import datetime as _dt
import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from finance.db import init_db

DEMO_DB_PATH = Path("data/demo.db")
TODAY = date(2026, 3, 14)  # fixed seed date for reproducibility

# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

_INSTITUTIONS = [
    ("inst-chase",   "Chase Bank",                 "https://chase.com",           "simplefin"),
    ("inst-marcus",  "Marcus by Goldman Sachs",     "https://marcus.com",          "simplefin"),
    ("inst-amex",    "American Express",            "https://americanexpress.com", "simplefin"),
    ("inst-schwab",  "Charles Schwab",              "https://schwab.com",          "simplefin"),
    ("inst-fidelity","Fidelity Investments",        "https://fidelity.com",        "simplefin"),
]

_ACCOUNTS = [
    # id               inst_id          name                       type         currency  mask    active
    ("acct-checking",  "inst-chase",    "Chase Checking",          "checking",  "USD",    "6491", 1),
    ("acct-savings",   "inst-marcus",   "Marcus HYSA",             "savings",   "USD",    "9820", 1),
    ("acct-amex",      "inst-amex",     "Amex Gold",               "credit",    "USD",    "1005", 1),
    ("acct-csr",       "inst-chase",    "Chase Sapphire Reserve",  "credit",    "USD",    "4521", 1),
    ("acct-schwab",    "inst-schwab",   "Schwab Brokerage",        "investment","USD",    "3872", 1),
    ("acct-401k",      "inst-fidelity", "Fidelity 401(k)",         "investment","USD",    "7731", 1),
]

_CREDIT_LIMITS = [
    ("acct-amex", 25_000.0),
    ("acct-csr",  20_000.0),
]


# ---------------------------------------------------------------------------
# Balance history — 13 monthly end-of-month snapshots
# Months: Feb 2025 → Feb 2026 (index 0 → 12)
# Note: market correction in month 6 (Aug 2025), recovery through month 12.
# ---------------------------------------------------------------------------

_BALANCE_SNAPSHOTS: dict[str, list[float]] = {
    #                Feb    Mar    Apr    May    Jun    Jul    Aug    Sep    Oct    Nov    Dec    Jan    Feb
    #               2025   2025   2025   2025   2025   2025   2025   2025   2025   2025   2025   2026   2026
    "acct-checking": [5200,  5400,  5150,  5600,  4900,  5300,  5800,  5600,  5200,  5800,  6100,  5400,  6200],
    "acct-savings":  [18400, 19000, 19600, 20200, 20800, 21400, 22000, 22500, 23100, 23700, 24300, 24900, 25500],
    "acct-amex":     [-2100, -1900, -2300, -2800, -1750, -2100, -2400, -3200, -1800, -2600, -3800, -2100, -2900],
    "acct-csr":      [-800,  -650,  -920,  -400,  -1100, -700,  -900,  -500,  -1200, -400,  -850,  -600,  -1050],
    "acct-schwab":   [82000, 84200, 86400, 88700, 90900, 93100, 95400, 77800, 80100, 83500, 86900, 90200, 93600],
    "acct-401k":     [132300,134100,135900,137700,139500,141300,143100,118900,122700,127300,132100,137200,142500],
}
# Derived net worth: Feb $235k → peak Aug $263k → dip Sep $219.1k → Feb $263.85k


# ---------------------------------------------------------------------------
# Recurring merchants — each defined with explicit charge dates so the
# get_recurring() interval/status logic produces the desired display state.
# ---------------------------------------------------------------------------

def _monthly_back(last: date, n: int) -> list[date]:
    """n monthly charges (30-day intervals) ending at last."""
    return [last - timedelta(days=30 * (n - 1 - i)) for i in range(n)]

def _weekly_back(last: date, n: int) -> list[date]:
    return [last - timedelta(days=7 * (n - 1 - i)) for i in range(n)]


# (merchant_normalized, merchant_name, category, amount, charge_dates)
# All amounts are negative (debits).
_RECURRING: list[tuple[str, str, str, float, list[date]]] = [
    # ── Monthly / upcoming ──────────────────────────────────────────────────
    # last charge 2026-03-09 → next 2026-04-08 → +25 days → "upcoming"
    ("Netflix",              "Netflix",               "Subscriptions & Software", -15.49, _monthly_back(date(2026, 3,  9), 13)),
    ("Spotify",              "Spotify",               "Subscriptions & Software", -9.99,  _monthly_back(date(2026, 3,  9), 13)),
    ("iCloud+",              "iCloud+",               "Subscriptions & Software", -2.99,  _monthly_back(date(2026, 3,  9), 13)),
    ("GitHub",               "GitHub",                "Subscriptions & Software", -4.00,  _monthly_back(date(2026, 3,  9), 13)),
    ("Adobe Creative Cloud", "Adobe Creative Cloud",  "Subscriptions & Software", -54.99, _monthly_back(date(2026, 3,  9), 13)),
    ("NY Times Digital",     "NY Times Digital",      "Subscriptions & Software", -17.00, _monthly_back(date(2026, 3,  9), 13)),
    ("Comcast Internet",     "Comcast Internet",      "Home & Utilities",         -89.99, _monthly_back(date(2026, 3,  9), 13)),
    # ── Monthly / due soon ──────────────────────────────────────────────────
    # last charge 2026-02-15 → next 2026-03-17 → +3 days → "due_soon"
    ("AWS",                  "Amazon Web Services",   "Subscriptions & Software", -34.12, _monthly_back(date(2026, 2, 15), 13)),
    # ── Monthly / zombie (cancel attempt unresolved, still billing) ─────────
    # same last charge → "due_soon" status but is_zombie=True → Needs Attention
    ("Hulu",                 "Hulu",                  "Subscriptions & Software", -17.99, _monthly_back(date(2026, 2, 15), 13)),
    # ── Monthly / past due ──────────────────────────────────────────────────
    # last charge 2026-01-23 → next 2026-02-22 → -20 days → "past_due"
    ("LinkedIn Premium",     "LinkedIn Premium",      "Subscriptions & Software", -39.99, _monthly_back(date(2026, 1, 23), 13)),
    # ── Monthly / likely cancelled ──────────────────────────────────────────
    # last charge 2025-12-01 → next 2025-12-31 → -74 days → "likely_cancelled"
    ("Planet Fitness",       "Planet Fitness",        "Health & Fitness",         -24.99, _monthly_back(date(2025, 12, 1), 13)),
    # ── Weekly / due soon ───────────────────────────────────────────────────
    # last charge 2026-03-10 → next 2026-03-17 → +3 days → "due_soon"
    ("ClassPass",            "ClassPass",             "Health & Fitness",         -19.00, _weekly_back(date(2026, 3, 10), 53)),
    # ── Quarterly ───────────────────────────────────────────────────────────
    # 91-day intervals, last 2026-01-14 → next 2026-04-15 → +32 days → "upcoming"
    ("Notion",               "Notion",                "Subscriptions & Software", -48.00, [
        date(2025, 1, 15), date(2025, 4, 16), date(2025, 7, 16), date(2025, 10, 15), date(2026, 1, 14),
    ]),
    # ── Annual ──────────────────────────────────────────────────────────────
    # 365-day gap, last 2025-09-15 → next 2026-09-15 → +185 days → "upcoming"
    ("Amazon Prime",         "Amazon Prime",          "Shopping",                 -139.00, [
        date(2024, 9, 15), date(2025, 9, 15),
    ]),
]

# Zombie cancel attempt: Hulu attempted 2026-01-05, not resolved, still billing
_CANCEL_ATTEMPTS = [
    ("Hulu", "2026-01-05", "Cancelled via website but still being charged.", None),
]


# ---------------------------------------------------------------------------
# One-off spending patterns
# (merchant, category, amount, account_key, month_indices_to_include)
# month_indices: list of month indices (0=Feb25…12=Feb26) to include, or None=every month
# ---------------------------------------------------------------------------

_SPENDING_PATTERNS: list[tuple[str, str, float, str, list[int] | None]] = [
    # ── Income ──────────────────────────────────────────────────────────────
    ("Employer Payroll",        "Income",               4583.33,  "checking",  None),      # 2x/month (added below)
    ("Employer Payroll",        "Income",               4583.33,  "checking",  None),      # 2nd paycheck
    ("Schwab Auto-Transfer",    "Investment",           -1500.00, "checking",  None),      # monthly brokerage contribution
    ("Amex Autopay",            "Financial",            -2100.00, "checking",  None),      # credit card payment
    ("Chase Sapphire Autopay",  "Financial",            -750.00,  "checking",  None),
    # ── Rent ────────────────────────────────────────────────────────────────
    ("Landlord / Zelle Rent",   "Home & Utilities",     -2800.00, "checking",  None),
    # ── Food & Dining ───────────────────────────────────────────────────────
    ("Chipotle",                "Food & Dining",        -13.50,   "amex",      None),
    ("Starbucks",               "Food & Dining",        -6.75,    "amex",      None),
    ("Sweetgreen",              "Food & Dining",        -17.40,   "amex",      None),
    ("Uber Eats",               "Food & Dining",        -32.80,   "amex",      None),
    ("DoorDash",                "Food & Dining",        -28.90,   "amex",      None),
    ("Local Ramen Bar",         "Food & Dining",        -54.00,   "amex",      None),
    # ── Groceries ───────────────────────────────────────────────────────────
    ("Whole Foods Market",      "Groceries",            -94.30,   "amex",      None),
    ("Trader Joe's",            "Groceries",            -61.80,   "amex",      None),
    ("Instacart",               "Groceries",            -118.40,  "amex",      None),
    # ── Transportation ──────────────────────────────────────────────────────
    ("Uber",                    "Transportation",       -14.25,   "amex",      None),
    ("Shell Gas Station",       "Transportation",       -68.40,   "checking",  None),
    ("EZ Pass",                 "Transportation",       -25.00,   "checking",  None),
    # ── Shopping ────────────────────────────────────────────────────────────
    ("Amazon",                  "Shopping",             -52.99,   "amex",      None),
    ("Target",                  "Shopping",             -74.30,   "amex",      None),
    # ── Entertainment ───────────────────────────────────────────────────────
    ("AMC Theaters",            "Entertainment",        -34.00,   "amex",      None),
    ("Steam",                   "Entertainment",        -19.99,   "amex",      [1,3,5,7,9,11]),  # occasional
    # ── Health ──────────────────────────────────────────────────────────────
    ("CVS Pharmacy",            "Health & Fitness",     -28.40,   "amex",      None),
    # ── Personal Care ───────────────────────────────────────────────────────
    ("Great Clips",             "Personal Care",        -28.00,   "checking",  [1,3,5,7,9,11]),
    ("Sephora",                 "Personal Care",        -68.00,   "amex",      [2,5,8,11]),
    # ── Home ────────────────────────────────────────────────────────────────
    ("Home Depot",              "Home & Utilities",     -147.00,  "checking",  [2,4,7,9]),
    # ── Travel (summer vacation — July/Aug 2025) ────────────────────────────
    ("Airbnb",                  "Travel",               -892.00,  "checking",  [5]),   # Jul 2025
    ("United Airlines",         "Travel",               -428.00,  "csr",       [5]),
    ("Marriott Hotel",          "Travel",               -647.00,  "csr",       [5]),
    ("Lyft to Airport",         "Transportation",       -48.00,   "amex",      [5]),
    ("Delta Airlines",          "Travel",               -312.00,  "csr",       [9]),   # Nov trip
    ("Vrbo",                    "Travel",               -520.00,  "checking",  [9]),
    # ── Medical (Sept 2025) ─────────────────────────────────────────────────
    ("Quest Diagnostics",       "Health & Fitness",     -189.00,  "checking",  [7]),
    ("Urgent Care Center",      "Health & Fitness",     -145.00,  "amex",      [7]),
    # ── Holiday shopping (Dec 2025) ─────────────────────────────────────────
    ("Apple Store",             "Shopping",             -489.00,  "amex",      [10]),
    ("Best Buy",                "Shopping",             -229.00,  "amex",      [10]),
    ("Amazon Holiday",          "Shopping",             -347.00,  "amex",      [10]),
    ("Williams-Sonoma",         "Shopping",             -132.00,  "amex",      [10]),
    # ── Freelance income (sporadic) ─────────────────────────────────────────
    ("Freelance Invoice",       "Income",               2800.00,  "checking",  [2,6,10]),
    # ── 401k employer match (annual true-up in Dec) ─────────────────────────
    ("Employer 401k Match",     "Income",               4200.00,  "checking",  [10]),  # reflected in 401k balance
]


# ---------------------------------------------------------------------------
# Review queue — 8 transactions that should look interesting
# ---------------------------------------------------------------------------

_REVIEW_ITEMS: list[tuple] = [
    # id              acct_id          date                       amount    description                  merchant              category  needs_r reason               is_rec norm
    ("demo-rev-001", "acct-amex",     TODAY.replace(day=3).isoformat(),   -299.00,  "AMZN Mktp US*2K9XY",     "Amazon",              None,    1, "large_amount",      0, "amazon"),
    ("demo-rev-002", "acct-checking", TODAY.replace(day=7).isoformat(),   -312.50,  "PAYPAL *VBKRJM9",        None,                  None,    1, "unknown_merchant",  0, "paypal-unknown"),
    ("demo-rev-003", "acct-amex",     TODAY.replace(day=2).isoformat(),   -67.00,   "SQ *GARDEN BAR LLC",     "SQ *Garden Bar",      None,    1, "uncategorized",     0, "sq-garden-bar"),
    ("demo-rev-004", "acct-amex",     (TODAY - timedelta(days=4)).isoformat(), -14.28, "FOREIGN TRANSACTION FEE", None,              None,    1, "foreign_fee",       0, "foreign-fee"),
    ("demo-rev-005", "acct-checking", (TODAY - timedelta(days=6)).isoformat(), -750.00, "Zelle Transfer to Alex", None,             None,    1, "large_amount",      0, "zelle-alex"),
    ("demo-rev-006", "acct-checking", (TODAY - timedelta(days=9)).isoformat(),  248.00, "MEDICAL CLAIM REIMB",   None,              "Income",1, "irregular",         0, "medical-reimb"),
    ("demo-rev-007", "acct-amex",     (TODAY - timedelta(days=11)).isoformat(), -523.00, "VENMO PAYMENT",       None,               None,    1, "large_amount",      0, "venmo"),
    ("demo-rev-008", "acct-amex",     (TODAY - timedelta(days=3)).isoformat(),  -15.49, "NETFLIX.COM",         "Netflix",            "Subscriptions & Software", 1, "duplicate_suspected", 0, "Netflix"),
]


# ---------------------------------------------------------------------------
# Pipeline run history — 3 recent runs
# ---------------------------------------------------------------------------

def _ms(d: date, hour: int = 9) -> int:
    epoch = _dt.datetime(1970, 1, 1)
    return int((_dt.datetime(d.year, d.month, d.day, hour, 0, 0) - epoch).total_seconds() * 1000)


_RUN_LOG = [
    # (run_type, started_ms, finished_ms, status, summary_dict)
    ("full", _ms(TODAY - timedelta(days=42)), _ms(TODAY - timedelta(days=42), hour=9) + 107_000, "success",
     {"categorized": 142, "recurring_detected": 18, "flagged_for_review": 5, "tokens_in": 28400, "tokens_out": 6120}),
    ("full", _ms(TODAY - timedelta(days=14)), _ms(TODAY - timedelta(days=14), hour=9) + 83_000, "success",
     {"categorized": 23, "recurring_detected": 2, "flagged_for_review": 1, "tokens_in": 8100, "tokens_out": 2340}),
    ("full", _ms(TODAY - timedelta(days=3)),  _ms(TODAY - timedelta(days=3),  hour=9) + 94_000, "success",
     {"categorized": 31, "recurring_detected": 4, "flagged_for_review": 2, "tokens_in": 9200, "tokens_out": 2880}),
]


# ---------------------------------------------------------------------------
# Seeding functions
# ---------------------------------------------------------------------------

def seed(db_path: Path = DEMO_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    init_db(conn)

    _seed_institutions(conn)
    _seed_accounts(conn)
    _seed_credit_limits(conn)
    _seed_balances(conn)
    _seed_recurring_transactions(conn)
    _seed_spending_transactions(conn)
    _seed_review_items(conn)
    _seed_cancel_attempts(conn)
    _seed_run_log(conn)
    conn.close()
    print(f"Demo database seeded at {db_path}")


def _seed_institutions(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO institutions (id, name, url, source) VALUES (?, ?, ?, ?)",
        _INSTITUTIONS,
    )
    conn.commit()


def _seed_accounts(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO accounts (id, institution_id, name, type, currency, mask, active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        _ACCOUNTS,
    )
    conn.commit()


def _seed_credit_limits(conn: sqlite3.Connection) -> None:
    import time
    now_ms = int(time.time() * 1000)
    conn.executemany(
        "INSERT OR REPLACE INTO credit_limits (account_id, credit_limit, updated_at) VALUES (?, ?, ?)",
        [(acct, limit, now_ms) for acct, limit in _CREDIT_LIMITS],
    )
    conn.commit()


def _seed_balances(conn: sqlite3.Connection) -> None:
    """Insert one end-of-month balance snapshot per account per month."""
    epoch = _dt.datetime(1970, 1, 1)

    # Generate snapshot dates: end-of-month for Feb 2025 … Feb 2026
    snapshot_months: list[date] = []
    y, m = 2025, 2
    for _ in range(13):
        # last day of month
        if m == 12:
            last_day = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(y, m + 1, 1) - timedelta(days=1)
        snapshot_months.append(last_day)
        m += 1
        if m > 12:
            m = 1
            y += 1

    rows = []
    for acct_id, balances in _BALANCE_SNAPSHOTS.items():
        for i, snap_date in enumerate(snapshot_months):
            snap_dt = _dt.datetime(snap_date.year, snap_date.month, snap_date.day, 23, 59, 0)
            ts_ms = int((snap_dt - epoch).total_seconds() * 1000)
            bal = balances[i]
            available = bal if "credit" not in acct_id else None
            rows.append((acct_id, ts_ms, bal, available))

    conn.executemany(
        "INSERT OR IGNORE INTO balances (account_id, timestamp, balance, available) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def _seed_recurring_transactions(conn: sqlite3.Connection) -> None:
    """Insert one transaction per charge date for each recurring merchant."""
    rng = random.Random(42)
    txns = []
    for i, (norm, merchant, category, base_amount, dates) in enumerate(_RECURRING):
        acct_id = "acct-amex" if norm not in ("Comcast Internet", "Amazon Prime") else "acct-checking"
        for j, charge_date in enumerate(dates):
            # Tiny amount jitter to keep it realistic
            variance = rng.uniform(-0.30, 0.30) if abs(base_amount) > 5 else 0.0
            amount = round(base_amount + variance, 2)
            txn_id = f"demo-rec-{i:02d}-{j:03d}"
            txns.append((
                txn_id, acct_id, charge_date.isoformat(), amount,
                merchant, merchant, category,
                0, "simplefin", None, None,
                0, None, 1, norm,
            ))

    conn.executemany(
        """INSERT OR REPLACE INTO transactions
           (id, account_id, date, amount, description, merchant_name, category,
            pending, source, raw, categorized_at,
            needs_review, review_reason, is_recurring, merchant_normalized)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        txns,
    )
    conn.commit()


def _seed_spending_transactions(conn: sqlite3.Connection) -> None:
    """Insert one-off spending transactions across 13 months."""
    rng = random.Random(99)
    acct_map = {
        "checking": "acct-checking",
        "amex":     "acct-amex",
        "csr":      "acct-csr",
        "savings":  "acct-savings",
    }

    # Month start dates: Feb 2025 … Feb 2026
    month_starts: list[date] = []
    y, m = 2025, 2
    for _ in range(13):
        month_starts.append(date(y, m, 1))
        m += 1
        if m > 12:
            m = 1
            y += 1

    def _days_in_month(d: date) -> list[date]:
        if d.month == 12:
            last = date(d.year + 1, 1, 1) - timedelta(days=1)
        else:
            last = date(d.year, d.month + 1, 1) - timedelta(days=1)
        return [d + timedelta(days=k) for k in range((last - d).days + 1)]

    txns = []
    counter = 0

    for month_idx, month_start in enumerate(month_starts):
        days = _days_in_month(month_start)

        for merchant, category, base_amount, acct_key, month_filter in _SPENDING_PATTERNS:
            if month_filter is not None and month_idx not in month_filter:
                continue

            day = rng.choice(days[1:])  # avoid 1st (too many autopays)
            # Slight variation for variable-amount items
            if category not in ("Income", "Financial", "Investment"):
                amount = round(base_amount * rng.uniform(0.88, 1.12), 2)
            else:
                amount = base_amount

            # Payroll: 1st and 15th
            if merchant == "Employer Payroll":
                if counter % 2 == 0:
                    day = days[0]          # 1st
                else:
                    day = days[min(14, len(days) - 1)]  # 15th

            txn_id = f"demo-txn-{counter:04d}"
            counter += 1
            acct_id = acct_map.get(acct_key, "acct-checking")
            norm = merchant.lower().replace(" ", "-").replace("/", "-").replace("*", "")
            txns.append((
                txn_id, acct_id, day.isoformat(), amount,
                merchant, merchant, category,
                0, "simplefin", None, None,
                0, None, 0, norm,
            ))

    conn.executemany(
        """INSERT OR REPLACE INTO transactions
           (id, account_id, date, amount, description, merchant_name, category,
            pending, source, raw, categorized_at,
            needs_review, review_reason, is_recurring, merchant_normalized)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        txns,
    )
    conn.commit()


def _seed_review_items(conn: sqlite3.Connection) -> None:
    rows = []
    for r in _REVIEW_ITEMS:
        txn_id, acct_id, txn_date, amount, desc, merchant, category, needs_r, reason, is_rec, norm = r
        rows.append((
            txn_id, acct_id, txn_date, amount, desc, merchant, category,
            0, "simplefin", None, None, needs_r, reason, is_rec, norm,
        ))

    conn.executemany(
        """INSERT OR REPLACE INTO transactions
           (id, account_id, date, amount, description, merchant_name, category,
            pending, source, raw, categorized_at,
            needs_review, review_reason, is_recurring, merchant_normalized)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()


def _seed_cancel_attempts(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """INSERT OR REPLACE INTO recurring_cancel_attempts
           (merchant_normalized, attempted_at, notes, resolved_at)
           VALUES (?, ?, ?, ?)""",
        _CANCEL_ATTEMPTS,
    )
    conn.commit()


def _seed_run_log(conn: sqlite3.Connection) -> None:
    rows = [
        (run_type, started_ms, finished_ms, status, json.dumps(summary))
        for run_type, started_ms, finished_ms, status, summary in _RUN_LOG
    ]
    conn.executemany(
        """INSERT INTO run_log (run_type, started_at, finished_at, status, summary)
           VALUES (?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()


if __name__ == "__main__":
    seed()
