"""Expense model + validation."""

from datetime import datetime

from utils import CATEGORIES, format_money, valid_amount


class ValidationError(ValueError):
    """Raised when an expense fails validation."""


class Expense:
    def __init__(self, shop, category, amount, date, notes="", currency="\u20b9",
                 receipt_path="", receipt_confidence=None, expense_id=None):
        self.id = expense_id
        self.shop = (shop or "").strip()
        self.category = category or "Other"
        self.amount = amount
        self.date = date
        self.notes = (notes or "").strip()
        self.currency = currency or "\u20b9"
        self.receipt_path = receipt_path or ""
        self.receipt_confidence = receipt_confidence
        self.validate()

    def validate(self):
        if not self.shop:
            raise ValidationError("Shop/merchant is required.")
        if self.category not in CATEGORIES:
            raise ValidationError(
                "Category must be one of: " + ", ".join(CATEGORIES) + ".")
        amount = valid_amount(self.amount)
        if amount is None:
            raise ValidationError("Amount must be a positive number (max 2 decimals).")
        self.amount = amount
        try:
            datetime.strptime(str(self.date), "%Y-%m-%d")
        except (TypeError, ValueError):
            raise ValidationError("Date must be in YYYY-MM-DD format.")

    def to_dictionary(self):
        return {
            "id": self.id,
            "shop": self.shop,
            "category": self.category,
            "amount": self.amount,
            "date": self.date,
            "notes": self.notes,
            "currency": self.currency,
            "receipt_path": self.receipt_path,
            "receipt_confidence": self.receipt_confidence,
        }

    def apply_discount(self, percent):
        """Apply a discount percentage to the amount (keeps it a valid expense)."""
        if not isinstance(percent, (int, float)) or not 0 < percent < 100:
            raise ValidationError("Discount must be between 0 and 100.")
        self.amount = round(self.amount * (1 - percent / 100), 2)

    def is_category(self, category):
        return self.category.lower() == str(category).lower()

    def __str__(self):
        return (f"Expense(#{self.id} | {self.date} | {self.shop} | {self.category} | "
                f"{format_money(self.amount, self.currency)})")

    __repr__ = __str__
