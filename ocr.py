"""Receipt OCR using EasyOCR.

Extracts shop name, date, total amount, currency and (best-effort) line items.
The EasyOCR model is loaded lazily on the first scan, so the app starts fast.
"""

import re

from utils import detect_currency, parse_date

_reader = None

AMOUNT_RE = re.compile(r"(\d{1,6}(?:[.,]\d{2})?)")

SHOP_SKIP_PREFIX = (
    "gstin", "tax", "bill no", "invoice", "cash", "card", "upi", "mob:",
    "tel:", "web", "www", "http", "email", "e-mail", "served", "thank",
    "visit", "phone", "ph:", "gst", "cst", "fssai", "order", "order no",
    "table", "server", "cashier",
)

ITEM_SKIP_WORDS = (
    "total", "subtotal", "sub total", "cash", "change", "balance", "gst",
    "tax", "vat", "round", "paid", "tender", "due", "card", "upi",
    "wallet", "grand", "amount", "discount", "net", "credit", "debit",
)


def get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def is_available():
    try:
        import easyocr  # noqa: F401
        return True
    except ImportError:
        return False


def scan(path):
    """OCR a receipt image. Returns a dict with shop, date, total, currency,
    items, text and an average confidence score (0-100)."""
    reader = get_reader()
    results = reader.readtext(path, detail=1)  # [(bbox, text, confidence), ...]
    lines, confidences = [], []
    for _, text, conf in results:
        if text and str(text).strip():
            lines.append(str(text).strip())
            confidences.append(float(conf))
    text = "\n".join(lines)
    avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0

    total = _extract_total(lines)
    return {
        "shop": _extract_shop(lines),
        "date": _extract_date(text),
        "total": total,
        "currency": detect_currency(text),
        "items": _extract_items(lines, total),
        "text": text,
        "confidence": round(avg_conf * 100, 1),
    }


def _to_float(s):
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _extract_shop(lines):
    """Usually the first plausible non-numeric line (the merchant name)."""
    for line in lines:
        s = line.strip()
        if len(s) < 2 or len(s) > 50:
            continue
        if re.fullmatch(r"[\d\W_ ]+", s):
            continue
        low = s.lower()
        if low.startswith(SHOP_SKIP_PREFIX):
            continue
        return s
    return ""


def _extract_date(text):
    d = parse_date(text)
    return d.isoformat() if d else ""


def _extract_total(lines):
    """Total: prefer the amount on a 'total'-like line, else the largest amount."""
    total_hint = None
    for line in lines:
        low = line.lower()
        if ("total" in low or "amount due" in low or "net amount" in low
                or "grand" in low):
            m = AMOUNT_RE.search(line)
            if m:
                total_hint = _to_float(m.group(1))
                if total_hint:
                    break
    amounts = []
    for line in lines:
        for m in AMOUNT_RE.finditer(line):
            v = _to_float(m.group(1))
            if v is not None and 0 < v < 1_000_000:
                amounts.append(v)
    if total_hint:
        return total_hint
    return max(amounts) if amounts else 0.0


def _extract_items(lines, total):
    """Best-effort item extraction: lines ending in a price, excluding totals."""
    items = []
    seen = set()
    for line in lines:
        m = re.search(r"(\d{1,6}(?:[.,]\d{2})?)\s*$", line.strip())
        if not m:
            continue
        price = _to_float(m.group(1))
        if price is None:
            continue
        name = line.strip()[: -len(m.group(1))].strip(" -\u2014:.,")
        if not name or len(name) < 2:
            continue
        low = name.lower()
        if any(w in low for w in ITEM_SKIP_WORDS):
            continue
        if re.fullmatch(r"[\d\W_ ]+", name):
            continue
        if total and price > total:
            continue
        key = (low, price)
        if key in seen:
            continue
        seen.add(key)
        items.append({"name": name, "price": price})
    return items
