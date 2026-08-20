"""Unit tests for the pure-Python logic (utils, expense, database).

Uses only the standard library. The database tests run against a temporary
file so your real expenses.db is never touched.

Run with:  python -m unittest test_core -v
"""

import os
import shutil
import tempfile
import unittest

import database as db
import utils
from expense import Expense, ValidationError


class UtilsTests(unittest.TestCase):
    def test_categorize(self):
        self.assertEqual(utils.categorize("Dmart"), "Groceries")
        self.assertEqual(utils.categorize("Uber"), "Transport")
        self.assertEqual(utils.categorize("Netflix"), "Entertainment")
        self.assertEqual(utils.categorize("Apollo Pharmacy"), "Healthcare")
        self.assertEqual(utils.categorize("Random Shop"), "Other")

    def test_valid_amount(self):
        self.assertEqual(utils.valid_amount("1,248.5"), 1248.5)
        self.assertEqual(utils.valid_amount("50"), 50.0)
        self.assertIsNone(utils.valid_amount("abc"))
        self.assertIsNone(utils.valid_amount("0"))
        self.assertIsNone(utils.valid_amount("-5"))
        self.assertIsNone(utils.valid_amount(""))

    def test_parse_date(self):
        self.assertEqual(utils.parse_date("08/08/2026").isoformat(), "2026-08-08")
        self.assertEqual(utils.parse_date("2026-08-08").isoformat(), "2026-08-08")
        self.assertEqual(utils.parse_date("08-08-26").isoformat(), "2026-08-08")
        self.assertEqual(utils.parse_date("Aug 08 2026").isoformat(), "2026-08-08")
        self.assertIsNone(utils.parse_date("no date here"))

    def test_parse_iso_date(self):
        self.assertEqual(utils.parse_iso_date("2026-08-08").isoformat(), "2026-08-08")
        self.assertIsNone(utils.parse_iso_date("08/08/2026"))
        self.assertIsNone(utils.parse_iso_date(""))

    def test_detect_currency(self):
        self.assertEqual(utils.detect_currency("Total Rs. 100"), "\u20b9")
        self.assertEqual(utils.detect_currency("Total $100.00"), "$")
        self.assertEqual(utils.detect_currency(""), "\u20b9")

    def test_format_money(self):
        self.assertEqual(utils.format_money(1248, "\u20b9"), "\u20b91,248.00")
        self.assertEqual(utils.format_money(5.5, "$"), "$5.50")


class ExpenseTests(unittest.TestCase):
    def test_valid_expense(self):
        e = Expense("DMart", "Groceries", 1248, "2026-08-08", "Weekly shop")
        self.assertEqual(e.amount, 1248.0)
        self.assertEqual(e.category, "Groceries")
        self.assertEqual(e.shop, "DMart")

    def test_invalid_amount(self):
        with self.assertRaises(ValidationError):
            Expense("DMart", "Groceries", "not a number", "2026-08-08")

    def test_invalid_date(self):
        with self.assertRaises(ValidationError):
            Expense("DMart", "Groceries", 100, "08/08/2026")

    def test_missing_shop(self):
        with self.assertRaises(ValidationError):
            Expense("", "Groceries", 100, "2026-08-08")

    def test_unknown_category(self):
        with self.assertRaises(ValidationError):
            Expense("DMart", "NotACategory", 100, "2026-08-08")

    def test_apply_discount_and_category(self):
        e = Expense("Amazon", "Shopping", 499, "2026-08-02")
        e.apply_discount(10)
        self.assertEqual(e.amount, 449.1)
        self.assertTrue(e.is_category("shopping"))
        self.assertFalse(e.is_category("food"))

    def test_to_dictionary(self):
        e = Expense("Uber", "Transport", 245, "2026-08-01")
        d = e.to_dictionary()
        self.assertEqual(d["shop"], "Uber")
        self.assertEqual(d["amount"], 245.0)
        self.assertEqual(d["date"], "2026-08-01")


class DatabaseTests(unittest.TestCase):
    """Runs against a temporary database file."""

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
        db._execute("DELETE FROM budgets")

    def test_add_get_update_delete(self):
        e = Expense("DMart", "Groceries", 1248, "2026-08-08")
        eid = db.add_expense(e)
        got = db.get_expense(eid)
        self.assertEqual(got.shop, "DMart")
        self.assertEqual(got.amount, 1248.0)

        e.id = eid
        e.amount = 1000
        db.update_expense(e)
        self.assertEqual(db.get_expense(eid).amount, 1000.0)

        db.delete_expense(eid)
        self.assertIsNone(db.get_expense(eid))

    def test_search_filters(self):
        db.add_expense(Expense("DMart", "Groceries", 1248, "2026-08-08"))
        db.add_expense(Expense("Uber", "Transport", 245, "2026-08-09"))
        self.assertEqual(len(db.search_expenses(query="dmart")), 1)
        self.assertEqual(len(db.search_expenses(category="Groceries")), 1)
        self.assertEqual(len(db.search_expenses(month="2026-08")), 2)
        self.assertEqual(len(db.search_expenses(amount_min=1000)), 1)
        self.assertEqual(len(db.search_expenses(date_from="2026-08-09")), 1)
        self.assertEqual(len(db.search_expenses(shop="uber")), 1)

    def test_budgets(self):
        db.set_budget("Overall", 30000)
        db.set_budget("Food", 5000)
        self.assertEqual(db.get_budget("Overall"), 30000.0)
        self.assertEqual(db.get_budgets()["Food"], 5000.0)

        db.set_budget("Food", 6000)  # upsert
        self.assertEqual(db.get_budget("Food"), 6000.0)

        db.delete_budget("Food")
        self.assertIsNone(db.get_budget("Food"))
        self.assertNotIn("Food", db.get_budgets())


if __name__ == "__main__":
    unittest.main()
