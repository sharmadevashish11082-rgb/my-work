"""SQLite storage for expenses, budgets, settings and cards."""

import csv
import os
import sqlite3
from contextlib import closing

from expense import Expense

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _execute(sql, params=()):
    with closing(get_conn()) as c, c:
        return c.execute(sql, params)


def _fetchall(sql, params=()):
    with closing(get_conn()) as c:
        return c.execute(sql, params).fetchall()


def _fetchone(sql, params=()):
    with closing(get_conn()) as c:
        return c.execute(sql, params).fetchone()


def _migrate(c):
    """Add any columns missing from an older expenses.db."""
    existing = {row[1] for row in c.execute("PRAGMA table_info(expenses)")}
    additions = {
        "currency": "TEXT DEFAULT '\u20b9'",
        "receipt_path": "TEXT DEFAULT ''",
        "receipt_confidence": "REAL",
    }
    for name, ddl in additions.items():
        if name not in existing:
            c.execute(f"ALTER TABLE expenses ADD COLUMN {name} {ddl}")


def init():
    with closing(get_conn()) as c, c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS expenses ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " shop TEXT NOT NULL,"
            " category TEXT NOT NULL,"
            " amount REAL NOT NULL,"
            " date TEXT NOT NULL,"
            " notes TEXT DEFAULT '',"
            " currency TEXT DEFAULT '\u20b9',"
            " receipt_path TEXT DEFAULT '',"
            " receipt_confidence REAL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS budgets ("
            " category TEXT PRIMARY KEY,"
            " amount REAL NOT NULL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS settings ("
            " key TEXT PRIMARY KEY,"
            " value TEXT NOT NULL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS cards ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " brand TEXT NOT NULL,"
            " last4 TEXT NOT NULL,"
            " holder TEXT NOT NULL,"
            " expiry TEXT NOT NULL)"
        )
        _migrate(c)
        c.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)")


init()


def _row_to_expense(row):
    if row is None:
        return None
    return Expense(
        expense_id=row["id"],
        shop=row["shop"],
        category=row["category"],
        amount=row["amount"],
        date=row["date"],
        notes=row["notes"] or "",
        currency=row["currency"] or "\u20b9",
        receipt_path=row["receipt_path"] or "",
        receipt_confidence=row["receipt_confidence"],
    )


def add_expense(expense):
    """Insert an Expense; returns its new automatic id."""
    cur = _execute(
        "INSERT INTO expenses (shop, category, amount, date, notes, currency,"
        " receipt_path, receipt_confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (expense.shop, expense.category, expense.amount, expense.date,
         expense.notes, expense.currency, expense.receipt_path,
         expense.receipt_confidence),
    )
    return cur.lastrowid


def update_expense(expense):
    _execute(
        "UPDATE expenses SET shop=?, category=?, amount=?, date=?, notes=?, currency=?,"
        " receipt_path=?, receipt_confidence=? WHERE id=?",
        (expense.shop, expense.category, expense.amount, expense.date,
         expense.notes, expense.currency, expense.receipt_path,
         expense.receipt_confidence, expense.id),
    )


def delete_expense(expense_id):
    _execute("DELETE FROM expenses WHERE id=?", (expense_id,))


def get_expense(expense_id):
    return _row_to_expense(
        _fetchone("SELECT * FROM expenses WHERE id=?", (expense_id,)))


def get_all_expenses():
    rows = _fetchall("SELECT * FROM expenses ORDER BY date DESC, id DESC")
    return [_row_to_expense(r) for r in rows]


def search_expenses(query="", category="", month="", amount_min=None, amount_max=None,
                    date_from=None, date_to=None, shop="", notes=""):
    """Filter expenses. Empty values are ignored."""
    sql = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if query:
        sql += " AND (shop LIKE ? OR notes LIKE ? OR category LIKE ?"
        sql += " OR CAST(amount AS TEXT) LIKE ?)"
        like = f"%{query}%"
        params += [like, like, like, like]
    if category:
        sql += " AND category = ?"
        params.append(category)
    if month:
        sql += " AND substr(date, 1, 7) = ?"
        params.append(month)
    if amount_min is not None:
        sql += " AND amount >= ?"
        params.append(amount_min)
    if amount_max is not None:
        sql += " AND amount <= ?"
        params.append(amount_max)
    if date_from:
        sql += " AND date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND date <= ?"
        params.append(date_to)
    if shop:
        sql += " AND shop LIKE ?"
        params.append(f"%{shop}%")
    if notes:
        sql += " AND notes LIKE ?"
        params.append(f"%{notes}%")
    sql += " ORDER BY date DESC, id DESC"
    return [_row_to_expense(r) for r in _fetchall(sql, params)]


def set_budget(category, amount):
    """Set (or update) a monthly budget for a category. 'Overall' is the
    overall monthly budget. Returns the stored amount."""
    amount = round(float(amount), 2)
    _execute(
        "INSERT INTO budgets (category, amount) VALUES (?, ?)"
        " ON CONFLICT(category) DO UPDATE SET amount = excluded.amount",
        (category, amount),
    )
    return amount


def delete_budget(category):
    _execute("DELETE FROM budgets WHERE category = ?", (category,))


def get_budget(category):
    row = _fetchone("SELECT amount FROM budgets WHERE category = ?", (category,))
    return row["amount"] if row else None


def get_budgets():
    """All budgets as {category: amount}."""
    return {r["category"]: r["amount"]
            for r in _fetchall("SELECT category, amount FROM budgets")}


def get_setting(key, default=None):
    """Read a settings value (as text), or ``default`` when unset."""
    row = _fetchone("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else default


def set_setting(key, value):
    _execute(
        "INSERT INTO settings (key, value) VALUES (?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, str(value)),
    )


def add_card(brand, last4, holder, expiry):
    """Insert a credit card; returns its new id."""
    cur = _execute(
        "INSERT INTO cards (brand, last4, holder, expiry) VALUES (?, ?, ?, ?)",
        (brand, last4, holder, expiry),
    )
    return cur.lastrowid


def get_cards():
    """All saved cards as a list of dicts."""
    return [dict(r) for r in _fetchall("SELECT * FROM cards ORDER BY id")]


def delete_card(card_id):
    _execute("DELETE FROM cards WHERE id = ?", (card_id,))


def export_csv(path, expenses):
    """Write expenses to a CSV file; returns the number of rows written."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "date", "shop", "category", "amount",
                         "currency", "notes", "receipt_path"])
        for e in expenses:
            writer.writerow([e.id, e.date, e.shop, e.category, e.amount,
                             e.currency, e.notes, e.receipt_path])
    return len(expenses)
