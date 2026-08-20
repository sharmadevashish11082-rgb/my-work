"""Seed the database with realistic sample expenses and budgets so the
dashboard, charts and budgets have data to show immediately.

Usage:
    python demo_data.py           # seed only if the database is empty
    python demo_data.py --reset   # clear expenses/budgets first, then seed
"""

import random
import sys
from datetime import date, timedelta

import database as db
from expense import Expense
from utils import valid_amount

# (shop, category, amount, notes)
SAMPLES = [
    ("DMart", "Groceries", 1248, "Weekly groceries"),
    ("Uber", "Transport", 245, "Cab to office"),
    ("Netflix", "Entertainment", 649, "Monthly subscription"),
    ("Zomato", "Food", 420, "Dinner order"),
    ("Amazon", "Shopping", 1999, "USB hub"),
    ("Apollo Pharmacy", "Healthcare", 350, "Medicine"),
    ("Indian Oil", "Transport", 1000, "Petrol"),
    ("Jio Recharge", "Bills", 299, "Mobile recharge"),
    ("Udemy", "Education", 820, "Python course"),
    ("MakeMyTrip", "Travel", 4500, "Flight tickets"),
    ("Big Bazaar", "Groceries", 760, "Monthly shopping"),
    ("Starbucks", "Food", 380, "Coffee"),
    ("Myntra", "Shopping", 1299, "T-shirt"),
    ("Electricity Board", "Bills", 1450, "Electricity bill"),
    ("BookMyShow", "Entertainment", 600, "Movie tickets"),
    ("MedPlus", "Healthcare", 265, "Vitamins"),
    ("Rapido", "Transport", 85, "Bike ride"),
    ("DMart", "Groceries", 950, "Fruits and veggies"),
    ("Swiggy", "Food", 310, "Lunch"),
    ("Flipkart", "Shopping", 850, "Books"),
]

BUDGETS = {
    "Overall": 30000,
    "Groceries": 8000,
    "Food": 5000,
    "Transport": 4000,
    "Shopping": 5000,
    "Bills": 3000,
    "Education": 2000,
    "Entertainment": 2000,
    "Healthcare": 2000,
    "Travel": 10000,
}


def seed(reset=False):
    if reset:
        for e in db.get_all_expenses():
            db.delete_expense(e.id)
        for cat in set(list(db.get_budgets()) + list(BUDGETS)):
            db.delete_budget(cat)
        for card in db.get_cards():
            db.delete_card(card["id"])

    if db.get_all_expenses():
        print("Database already has expenses - nothing added.")
        print("Use:  python demo_data.py --reset   to clear and reseed.")
        return False

    random.seed(42)
    today = date.today()
    count = 0
    for shop, category, amount, notes in SAMPLES:
        if not valid_amount(amount):
            continue
        # spread the sample over the last ~4 months
        day = today - timedelta(days=random.randint(0, 120))
        exp = Expense(shop=shop, category=category, amount=amount,
                      date=day.isoformat(), notes=notes)
        db.add_expense(exp)
        count += 1

    for cat, amount in BUDGETS.items():
        db.set_budget(cat, amount)

    db.set_setting("monthly_income", "2200")
    if not db.get_cards():
        db.add_card("VISA", "5491", "James Smith", "12/2030")

    print(f"Added {count} sample expenses + budgets, spread over the last 4 months.")
    print("Seeded monthly income + a sample VISA card for the dashboard.")
    print("Open the app with:  python main.py")
    return True


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
