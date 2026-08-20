"""Shared helpers: categories, currency, dates, validation."""

import re
from datetime import datetime

CATEGORIES = [
    "Food",
    "Groceries",
    "Transport",
    "Shopping",
    "Bills",
    "Education",
    "Entertainment",
    "Healthcare",
    "Travel",
    "Other",
]

CATEGORY_KEYWORDS = {
    "Food": ["restaurant", "cafe", "caf\u00e9", "starbucks", "burger", "pizza", "kfc",
             "mcdonald", "dominos", "zomato", "swiggy", "dhaba", "hotel", "tiffin",
             "bakery", "chaat", "canteen", "food", "barista", "subway"],
    "Groceries": ["dmart", "big bazaar", "reliance fresh", "more", "supermarket",
                  "grocery", "vegetable", "veg", "fruit", "kirana", "safal",
                  "spencers", "bigbasket", "zepto", "blinkit", "grofers", "fresh"],
    "Transport": ["uber", "ola", "rapido", "metro", "bus", "railway", "irctc",
                  "petrol", "fuel", "indian oil", "hp ", "bharat petroleum",
                  "parking", "taxi", "auto", "cab", "fuel", "flight", "airport"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "zara", "h&m", "mall",
                 "clothing", "apparel", "shoe", "footwear", "nykaa", "meesho",
                 "snapdeal", "walmart", "electronics", "mobile", "laptop"],
    "Bills": ["electricity", "water bill", "gas", "internet", "broadband", "jio",
              "airtel", "vi ", "bsnl", "recharge", "electric", "power", "bill",
              "rent", "maintenance"],
    "Education": ["udemy", "coursera", "book", "stationery", "tuition", "class",
                  "school", "college", "udacity", "academy", "notebook", "course"],
    "Entertainment": ["netflix", "prime", "hotstar", "bookmyshow", "cinema", "movie",
                      "theatre", "spotify", "game", "pubg", "youtube", "concert",
                      "play station", "xbox"],
    "Healthcare": ["apollo", "pharmacy", "medical", "medplus", "doctor", "hospital",
                   "clinic", "chemist", "medicine", "dental", "lab", "ayurveda"],
    "Travel": ["air india", "indigo", "goair", "makemytrip", "goibibo", "oyo",
               "airbnb", "train", "travel", "visa", "redbus", "yatra"],
}

CURRENCY_SYMBOLS = {"\u20b9": "\u20b9", "$": "$", "\u20ac": "\u20ac",
                    "\u00a3": "\u00a3", "\u00a5": "\u00a5"}

MONTH_ABBREVS = {name[:3].lower(): i for i, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}


def categorize(shop):
    """Guess a category from a shop/merchant name (keyword matching)."""
    shop = (shop or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in shop:
                return category
    return "Other"


def detect_currency(text):
    """Detect a currency from receipt text. Defaults to rupee (INR)."""
    if not text:
        return "\u20b9"
    low = text.lower()
    if "\u20b9" in text or "rs." in low or "inr" in low or "rupee" in low:
        return "\u20b9"
    if "$" in text or "usd" in low:
        return "$"
    if "\u20ac" in text or "eur" in low:
        return "\u20ac"
    if "\u00a3" in text or "gbp" in low:
        return "\u00a3"
    if "\u00a5" in text or "jpy" in low:
        return "\u00a5"
    return "\u20b9"


def format_money(amount, currency="\u20b9"):
    """Format a number with a currency symbol, e.g. \u20b91,248.00."""
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def valid_amount(value):
    """Return the rounded float amount if valid (> 0, finite), else None."""
    try:
        amount = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    if not (amount > 0) or amount > 1_000_000_000:
        return None
    return round(amount, 2)


def _month_from_name(name):
    return MONTH_ABBREVS.get(name.strip().lower()[:3])


def parse_date(text):
    """Best-effort date parsing from receipt text. Returns date or None."""
    if not text:
        return None
    text = text.strip()
    patterns = [
        (r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", "ymd"),
        (r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})", "dmy"),
        (r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2})(?!\d)", "dmy_short"),
        (r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})", "month_day_year"),
        (r"(\d{1,2})\s+([A-Za-z]{3,9}),?\s+(\d{4})", "day_month_year"),
    ]
    for pat, kind in patterns:
        m = re.search(pat, text)
        if not m:
            continue
        try:
            if kind == "dmy":
                d = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            elif kind == "dmy_short":
                d = datetime(int(m.group(3)) + 2000, int(m.group(2)), int(m.group(1)))
            elif kind == "ymd":
                d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            elif kind == "month_day_year":
                month = _month_from_name(m.group(1))
                if not month:
                    continue
                d = datetime(int(m.group(3)), month, int(m.group(2)))
            else:  # day_month_year
                month = _month_from_name(m.group(2))
                if not month:
                    continue
                d = datetime(int(m.group(3)), month, int(m.group(1)))
            return d.date()
        except ValueError:
            continue
    return None


def today_iso():
    return datetime.now().date().isoformat()


def parse_iso_date(text):
    """Parse a YYYY-MM-DD string into a date, or None if invalid/empty."""
    if not text:
        return None
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
