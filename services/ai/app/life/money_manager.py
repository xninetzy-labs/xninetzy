from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect, init_db

_EXPENSE_CATEGORIES = [
    "makan", "transport", "belanja", "hiburan", "kesehatan",
    "pendidikan", "tagihan", "pulsa", "kos", "investasi", "lain-lain",
]


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _today() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).strftime("%Y-%m-%d")


def _default_account_id() -> int | None:
    """Return first account ID, or None if no accounts."""
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT id FROM money_accounts LIMIT 1").fetchone()
    return row["id"] if row else None


def ensure_default_account() -> int:
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT id FROM money_accounts LIMIT 1").fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO money_accounts (name, type, currency, balance, created_at) VALUES (?,?,?,?,?)",
            ("Dompet Utama", "cash", "IDR", 0, _now()),
        )
        return cur.lastrowid


def add_transaction(amount: float, tx_type: str, category: str = "lain-lain",
                    description: str = "", account_id: int | None = None,
                    date: str | None = None) -> dict:
    init_db()
    if account_id is None:
        account_id = ensure_default_account()
    tx_date = date or _today()
    now = _now()
    sign = 1 if tx_type == "income" else -1
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO money_transactions (account_id, amount, type, category, description, transaction_date, source, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (account_id, amount, tx_type, category, description, tx_date, "manual", now),
        )
        # Update account balance
        conn.execute(
            "UPDATE money_accounts SET balance=balance+? WHERE id=?",
            (amount * sign, account_id),
        )
        return {"id": cur.lastrowid, "amount": amount, "type": tx_type, "category": category, "date": tx_date}


def get_summary(period: str = "month") -> dict:
    """period: day | week | month | year"""
    init_db()
    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))
    if period == "day":
        since = now.strftime("%Y-%m-%d")
    elif period == "week":
        from datetime import timedelta
        since = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "year":
        since = now.strftime("%Y-01-01")
    else:  # month
        since = now.strftime("%Y-%m-01")

    with connect() as conn:
        rows = conn.execute(
            "SELECT type, SUM(amount) as total FROM money_transactions WHERE transaction_date >= ? GROUP BY type",
            (since,),
        ).fetchall()
    totals = {r["type"]: r["total"] for r in rows}
    income = totals.get("income", 0)
    expense = totals.get("expense", 0)
    return {
        "period": period,
        "since": since,
        "income": income,
        "expense": expense,
        "net": income - expense,
    }


def category_breakdown(period: str = "month") -> list[dict]:
    init_db()
    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))
    since = now.strftime("%Y-%m-01") if period == "month" else now.strftime("%Y-01-01")
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT category, SUM(amount) as total FROM money_transactions
            WHERE type='expense' AND transaction_date >= ?
            GROUP BY category ORDER BY total DESC
            """,
            (since,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_account_balances() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM money_accounts").fetchall()
    return [dict(r) for r in rows]
