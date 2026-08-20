"""Tests for the fintech dashboard helpers and the newer database
functions (settings, cards, CSV export).

Pure standard library (no third-party packages needed - the matplotlib
import inside dashboard.py is guarded):

    python -m unittest test_dashboard -v
"""

import os
import shutil
import tempfile
import unittest
from datetime import date

import database as db
import dashboard
from expense import Expense


class MoneyFormatTests(unittest.TestCase):
    def test_fmt(self):
        self.assertEqual(dashboard._fmt(2200.0, "$"), "$2,200")
        self.assertEqual(dashboard._fmt(4430.5, "\u20b9"), "\u20b94,430.50")
        self.assertEqual(dashboard._fmt(0, "\u20b9"), "\u20b90")

    def test_compact(self):
        self.assertEqual(dashboard._compact(25000, "\u20b9"), "\u20b925.0k")
        self.assertEqual(dashboard._compact(1248, "\u20b9"), "\u20b91,248")
        self.assertEqual(dashboard._compact(1600000, "$"), "$1.6M")
        self.assertEqual(dashboard._compact(-500, "\u20b9"), "-\u20b9500")
        self.assertEqual(dashboard._compact(0, "\u20b9"), "\u20b90")


class ComputeStatsTests(unittest.TestCase):
    def test_empty(self):
        today = date.today()
        stats = dashboard.compute_stats([], today, today)
        self.assertEqual(stats["count"], 0)
        self.assertEqual(stats["total"], 0.0)
        self.assertEqual(stats["top_category"], "\u2014")

    def test_with_expenses(self):
        today = date.today()
        exp = Expense("DMart", "Groceries", 100, today.isoformat())
        stats = dashboard.compute_stats([exp], today, today)
        self.assertEqual(stats["count"], 1)
        self.assertEqual(stats["total"], 100.0)
        self.assertEqual(stats["today"], 100.0)
        self.assertEqual(stats["week"], 100.0)
        self.assertEqual(stats["month"], 100.0)
        self.assertEqual(stats["avg_daily"], 100.0)
        self.assertEqual(stats["top_category"], "Groceries")

    def test_average_over_period_length(self):
        start = date(2026, 8, 1)
        end = date(2026, 8, 10)
        exp = Expense("Uber", "Transport", 500, "2026-08-01")
        stats = dashboard.compute_stats([exp], start, end)
        self.assertEqual(stats["avg_daily"], 50.0)


class DatabaseExtrasTests(unittest.TestCase):
    """Settings, cards and CSV export against a temporary database."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.mkdtemp()
        cls._old_db = db.DB
        db.DB = os.path.join(cls._tmp, "test.db")
        db.init()

    @classmethod
    def tearDownClass(cls):
        db.DB = cls._old_db
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def setUp(self):
        db._execute("DELETE FROM expenses")
        db._execute("DELETE FROM settings")
        db._execute("DELETE FROM cards")

    def test_settings(self):
        self.assertIsNone(db.get_setting("monthly_income"))
        db.set_setting("monthly_income", "2200")
        self.assertEqual(db.get_setting("monthly_income"), "2200")
        db.set_setting("monthly_income", "3000")  # upsert
        self.assertEqual(db.get_setting("monthly_income"), "3000")
        self.assertEqual(db.get_setting("missing", "fallback"), "fallback")

    def test_cards(self):
        self.assertEqual(db.get_cards(), [])
        cid = db.add_card("VISA", "5491", "James Smith", "12/2030")
        cards = db.get_cards()
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["id"], cid)
        self.assertEqual(cards[0]["brand"], "VISA")
        self.assertEqual(cards[0]["last4"], "5491")
        self.assertEqual(cards[0]["holder"], "James Smith")
        db.delete_card(cid)
        self.assertEqual(db.get_cards(), [])

    def test_export_csv(self):
        db.add_expense(Expense("DMart", "Groceries", 1248, "2026-08-08"))
        db.add_expense(Expense("Uber", "Transport", 245, "2026-08-09"))
        path = os.path.join(self._tmp, "out.csv")
        n = db.export_csv(path, db.get_all_expenses())
        self.assertEqual(n, 2)
        with open(path, encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        self.assertEqual(len(lines), 3)  # header + 2 rows
        self.assertTrue(lines[0].startswith("id,date"))
        self.assertIn("DMart", lines[1])


if __name__ == "__main__":
    unittest.main()
