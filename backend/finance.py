# backend/finance.py

import os
import sqlite3
from datetime import date, datetime
from typing import Dict, List, Tuple, Any, Optional

# Try to reuse existing DB connection helper if it exists
try:
    from backend.db import get_connection  # type: ignore
except Exception:
    # Fallback: local SQLite file in /database/hotel.db
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_DIR = os.path.join(BASE_DIR, "database")
    DB_PATH = os.path.join(DB_DIR, "hotel.db")

    os.makedirs(DB_DIR, exist_ok=True)

    def get_connection() -> sqlite3.Connection:  # type: ignore
        con = sqlite3.connect(DB_PATH)
        # We DO NOT rely on row_factory anywhere in this file,
        # so default tuple rows are fine.
        return con


# ---------- TABLE SETUP ----------

def ensure_finance_table() -> None:
    """Create the finance_logs table if it doesn't exist yet."""
    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS finance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,        -- YYYY-MM-DD
                source TEXT NOT NULL,      -- Bar / Restaurant / Hotel / Reception / Other
                category TEXT NOT NULL,    -- Drink / Food / Room / Extra / etc.
                description TEXT NOT NULL, -- e.g. "Table 3 - Bill", "Room 101 checkout"
                amount REAL NOT NULL,
                method TEXT NOT NULL,      -- Cash / Card / Pending / Internal
                pending INTEGER NOT NULL,  -- 0 = no, 1 = yes
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.commit()


ensure_finance_table()


# ---------- BASIC OPERATIONS ----------

def add_finance_log(
    source: str,
    category: str,
    description: str,
    amount: float,
    method: str = "Cash",
    pending: bool = False,
    log_date: Optional[date] = None,
) -> None:
    """Insert a new finance row (used by Restaurant / Reception, etc.)."""
    if log_date is None:
        log_date = date.today()

    ensure_finance_table()

    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO finance_logs
                (date, source, category, description, amount, method, pending)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_date.isoformat(),
                source,
                category,
                description,
                float(amount),
                method,
                1 if pending else 0,
            ),
        )
        con.commit()


# ---------- QUERIES FOR FINANCE UI ----------

def _month_prefix(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}-"


def get_today_total() -> float:
    """Total non-pending revenue for today."""
    today = date.today().isoformat()
    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM finance_logs WHERE date=? AND pending=0",
            (today,),
        )
        row = cur.fetchone()
        if row is None:
            return 0.0
        return float(row[0] or 0.0)


def get_month_totals(year: int, month: int) -> Tuple[float, float]:
    """
    Returns (total_revenue, total_pending) for the given month.
    """
    prefix = _month_prefix(year, month) + "%"
    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN pending=0 THEN amount END), 0) AS total_paid,
                COALESCE(SUM(CASE WHEN pending=1 THEN amount END), 0) AS total_pending
            FROM finance_logs
            WHERE date LIKE ?
            """,
            (prefix,),
        )
        row = cur.fetchone()
        if row is None:
            return 0.0, 0.0
        total_paid = float(row[0] or 0.0)
        total_pending = float(row[1] or 0.0)
        return total_paid, total_pending


def get_month_daily_by_source(
    year: int, month: int
) -> Tuple[Dict[int, Dict[str, float]], Dict[str, float]]:
    """
    Returns:
      - daily: {day -> {source -> total_amount}}
      - source_totals: {source -> total_amount_for_month}
    Only non-pending rows are counted.
    """
    prefix = _month_prefix(year, month) + "%"

    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT
                date,
                source,
                SUM(amount) AS total
            FROM finance_logs
            WHERE date LIKE ? AND pending=0
            GROUP BY date, source
            ORDER BY date
            """,
            (prefix,),
        )

        daily: Dict[int, Dict[str, float]] = {}
        source_totals: Dict[str, float] = {}

        for d_str, source, total_val in cur.fetchall():
            dt = datetime.fromisoformat(d_str)
            day = dt.day
            total = float(total_val or 0.0)

            daily.setdefault(day, {})
            daily[day][source] = total

            source_totals[source] = source_totals.get(source, 0.0) + total

        return daily, source_totals


def get_quick_stats(year: int, month: int) -> Dict[str, Any]:
    """
    Returns:
        {
          "avg_per_day": float,
          "best_day": (day, amount) or None,
          "worst_day": (day, amount) or None
        }
    """
    prefix = _month_prefix(year, month) + "%"

    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT date, SUM(amount) AS total
            FROM finance_logs
            WHERE date LIKE ? AND pending=0
            GROUP BY date
            ORDER BY date
            """,
            (prefix,),
        )

        rows = cur.fetchall()
        if not rows:
            return {
                "avg_per_day": 0.0,
                "best_day": None,
                "worst_day": None,
            }

        totals: List[Tuple[int, float]] = []
        sum_total = 0.0

        for d_str, total_val in rows:
            dt = datetime.fromisoformat(d_str)
            day = dt.day
            total = float(total_val or 0.0)
            totals.append((day, total))
            sum_total += total

        avg = sum_total / len(totals)

        best = max(totals, key=lambda x: x[1])
        worst = min(totals, key=lambda x: x[1])

        return {
            "avg_per_day": avg,
            "best_day": best,
            "worst_day": worst,
        }


def get_outstanding_payments(limit: int = 10) -> List[tuple]:
    """Rows with pending=1."""
    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT date, source, description, amount
            FROM finance_logs
            WHERE pending=1
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


def get_recent_transactions(limit: int = 10) -> List[tuple]:
    """Latest transactions (for table at bottom)."""
    with get_connection() as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT date, source, category, description, amount, method
            FROM finance_logs
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


# ---------- CONVENIENCE HELPERS FOR OTHER MODULES ----------

def log_restaurant_bill(
    table_number: int,
    items: List[Dict[str, Any]],
    total: float,
    waiter: str,
    method: str = "Cash",
    log_date: Optional[date] = None,
) -> None:
    """
    One log entry per restaurant bill.
    (Your choice: total only, not item-by-item.)
    """
    description = f"Table {table_number} – {waiter or 'Waiter'}"
    category = "Food & Drink"
    add_finance_log(
        source="Restaurant",
        category=category,
        description=description,
        amount=total,
        method=method,
        pending=False,
        log_date=log_date,
    )


def log_room_payment(
    room_number: int,
    guest_name: Optional[str],
    amount: float,
    method: str = "Cash",
    log_date: Optional[date] = None,
) -> None:
    """
    Single combined payment per checkout.
    """
    desc_guest = guest_name or "Guest"
    description = f"Room {room_number} – {desc_guest}"
    add_finance_log(
        source="Hotel",
        category="Room",
        description=description,
        amount=amount,
        method=method,
        pending=False,
        log_date=log_date,
    )


def log_pending_payment(description: str, amount: float, source: str = "Hotel") -> None:
    """
    Generic helper if later you want pending (unpaid) items.
    Not currently used because you chose only Cash & Card.
    """
    add_finance_log(
        source=source,
        category="Pending",
        description=description,
        amount=amount,
        method="Pending",
        pending=True,
    )
