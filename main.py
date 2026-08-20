"""Expense Tracker — a pure-Python desktop app.

Tkinter GUI + SQLite storage + EasyOCR receipt scanning + matplotlib charts.

Run:  python main.py
"""

import calendar
import os
import shutil
import threading
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import database as db
import ocr
import theme
from dashboard import DashboardPanel
from expense import Expense, ValidationError
from utils import (CATEGORIES, categorize, format_money, parse_iso_date,
                   today_iso, valid_amount)

try:
    import charts
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIPTS_DIR = os.path.join(BASE_DIR, "receipts")
CURRENCIES = ["\u20b9", "$", "\u20ac", "\u00a3", "\u00a5"]

PERIODS = ["Today", "Yesterday", "Last 7 days", "This month", "Last month",
           "This year", "All time", "Custom range"]

CHART_TYPES = [
    "Spending by category (pie)",
    "Monthly spending (bar)",
    "Daily spending (line)",
    "Category comparison (actual vs budget)",
    "Period comparison (this vs previous)",
    "Top merchants (bar)",
    "Spending trend (cumulative)",
]


class CalendarDialog(tk.Toplevel):
    """A small month-view calendar for picking an expense date."""

    def __init__(self, parent, initial=None, on_select=None):
        super().__init__(parent)
        self.title("Select date")
        self.resizable(False, False)
        self.transient(parent)
        self.on_select = on_select
        initial = initial or date.today()
        self._year, self._month = initial.year, initial.month
        self._header = tk.Label(self, text="", font=("Segoe UI", 11, "bold"))
        self._header.pack(padx=8, pady=(8, 2))
        nav = tk.Frame(self)
        nav.pack()
        tk.Button(nav, text="\u25c0", width=3,
                  command=lambda: self._shift(-1)).pack(side="left", padx=4)
        tk.Button(nav, text="Today", width=6, command=self._today).pack(side="left", padx=4)
        tk.Button(nav, text="\u25b6", width=3,
                  command=lambda: self._shift(1)).pack(side="left", padx=4)
        self._grid = tk.Frame(self)
        self._grid.pack(padx=8, pady=8)
        self._draw()

    def _shift(self, delta):
        m = self._month + delta
        y = self._year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        self._month, self._year = m, y
        self._draw()

    def _today(self):
        t = date.today()
        self._year, self._month = t.year, t.month
        self._draw()

    def _draw(self):
        for w in self._grid.winfo_children():
            w.destroy()
        self._header.config(text=f"{calendar.month_name[self._month]} {self._year}")
        for i, name in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            tk.Label(self._grid, text=name,
                     font=("Segoe UI", 9, "bold")).grid(row=0, column=i, padx=2, pady=2)
        start_col = date(self._year, self._month, 1).weekday()  # Monday = 0
        num_days = calendar.monthrange(self._year, self._month)[1]
        today = date.today()
        r, c = 1, 0
        for _ in range(start_col):
            c += 1
        for day in range(1, num_days + 1):
            d = date(self._year, self._month, day)
            btn = tk.Button(
                self._grid, text=str(day), width=3,
                command=lambda dd=d: self._pick(dd),
                bg=theme.PALETTE["surface2"], fg=theme.PALETTE["text"],
                activebackground=theme.PALETTE["accent"],
                activeforeground=theme.PALETTE["accent_dark"], relief="flat")
            if d == today:
                btn.config(bg=theme.PALETTE["today"])
            btn.grid(row=r, column=c, padx=1, pady=1)
            c += 1
            if c > 6:
                c = 0
                r += 1

    def _pick(self, d):
        if self.on_select:
            self.on_select(d.isoformat())
        self.destroy()


class BudgetDialog(tk.Toplevel):
    """Dialog to set the overall + per-category monthly budgets."""

    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Set budgets (monthly)")
        self.transient(parent)
        self.resizable(False, False)
        self.on_save = on_save
        current = db.get_budgets()
        self.vars = {}
        body = ttk.Frame(self)
        body.pack(padx=10, pady=10)
        rows = [("Overall", "Overall (all categories)")] + [(c, c) for c in CATEGORIES]
        for i, (key, label) in enumerate(rows):
            ttk.Label(body, text=label).grid(row=i, column=0, sticky="w",
                                             padx=4, pady=2)
            var = tk.StringVar(value=f"{current.get(key):.2f}"
                               if current.get(key) else "")
            self.vars[key] = var
            ttk.Entry(body, textvariable=var, width=12).grid(row=i, column=1,
                                                             padx=4, pady=2)
        btns = ttk.Frame(self)
        btns.pack(pady=(0, 10))
        ttk.Button(btns, text="Save", command=self._save,
                   style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=4)

    def _save(self):
        for key, var in self.vars.items():
            raw = var.get().strip()
            if not raw:
                db.delete_budget(key)
                continue
            amount = valid_amount(raw)
            if amount is None:
                messagebox.showwarning(
                    "Invalid amount",
                    f"'{raw}' is not a valid budget for '{key}'.")
                return
            db.set_budget(key, amount)
        if self.on_save:
            self.on_save()
        self.destroy()


class ExpenseApp:
    def __init__(self, root):
        self.root = root
        root.title("Expense Tracker \u2014 Pure Python")
        root.geometry("1280x820")
        root.minsize(1040, 720)
        os.makedirs(RECEIPTS_DIR, exist_ok=True)

        self.current_expense_id = None
        self.last_receipt = None
        self.last_receipt_image = None
        self.expenses = []
        self._thumb_photo = None
        self._cam_photo = None
        self.period_var = tk.StringVar(value="This month")
        self.custom_from = tk.StringVar()
        self.custom_to = tk.StringVar()
        self.chart_var = tk.StringVar(value=CHART_TYPES[0])
        self._period_entries = []
        self._ready = False

        theme.apply_theme(root)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)
        self._build_dashboard()
        self._build_expenses_tab()
        self._build_receipt_tab()
        self._build_charts_tab()
        self.period_var.trace_add("write", self._on_period_changed)
        self.chart_var.trace_add("write", self._on_chart_changed)
        self._ready = True
        self.refresh_expenses()

    # ------------------------------------------------------------------ tabs

    def _build_dashboard(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="\U0001f4ca Dashboard")
        self.dashboard = DashboardPanel(tab, app=self)
        self.dashboard.pack(fill="both", expand=True)

    def _build_expenses_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="\U0001f9fe Expenses")

        # ---------------------------- filters
        filters = ttk.LabelFrame(tab, text="Search & filters")
        filters.pack(fill="x", padx=8, pady=(8, 4))

        self.f_search = tk.StringVar()
        self.f_category = tk.StringVar(value="All categories")
        self.f_month = tk.StringVar(value="All months")
        self.f_shop = tk.StringVar()
        self.f_notes = tk.StringVar()
        self.f_amt_min = tk.StringVar()
        self.f_amt_max = tk.StringVar()
        self.f_date_from = tk.StringVar()
        self.f_date_to = tk.StringVar()

        row1 = ttk.Frame(filters)
        row1.pack(fill="x", padx=6, pady=(6, 2))
        ttk.Label(row1, text="Search:").pack(side="left")
        search_entry = ttk.Entry(row1, textvariable=self.f_search, width=20)
        search_entry.pack(side="left", padx=(2, 8))
        search_entry.bind("<Return>", lambda ev: self.apply_filters())
        ttk.Label(row1, text="Category:").pack(side="left")
        ttk.Combobox(row1, textvariable=self.f_category,
                     values=["All categories"] + CATEGORIES,
                     state="readonly", width=13).pack(side="left", padx=(2, 8))
        ttk.Label(row1, text="Month:").pack(side="left")
        self.month_combo = ttk.Combobox(row1, textvariable=self.f_month,
                                        values=["All months"], state="readonly", width=10)
        self.month_combo.pack(side="left", padx=(2, 8))
        ttk.Label(row1, text="Shop:").pack(side="left")
        ttk.Entry(row1, textvariable=self.f_shop, width=14).pack(side="left", padx=(2, 8))
        ttk.Label(row1, text="Notes:").pack(side="left")
        ttk.Entry(row1, textvariable=self.f_notes, width=14).pack(side="left", padx=(2, 8))

        row2 = ttk.Frame(filters)
        row2.pack(fill="x", padx=6, pady=(2, 6))
        ttk.Label(row2, text="Amount:").pack(side="left")
        ttk.Entry(row2, textvariable=self.f_amt_min, width=8).pack(side="left", padx=(2, 2))
        ttk.Label(row2, text="to").pack(side="left")
        ttk.Entry(row2, textvariable=self.f_amt_max, width=8).pack(side="left", padx=(2, 8))
        ttk.Label(row2, text="Date:").pack(side="left")
        ttk.Entry(row2, textvariable=self.f_date_from, width=10).pack(side="left", padx=(2, 2))
        ttk.Label(row2, text="to").pack(side="left")
        ttk.Entry(row2, textvariable=self.f_date_to, width=10).pack(side="left", padx=(2, 8))
        ttk.Button(row2, text="Apply", command=self.apply_filters).pack(side="left", padx=2)
        ttk.Button(row2, text="Clear", command=self.clear_filters).pack(side="left", padx=2)

        # ---------------------------- list
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill="both", expand=True, padx=8, pady=4)
        cols = ("id", "date", "shop", "category", "amount", "notes", "receipt")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings",
                                 selectmode="browse")
        headings = {"id": "ID", "date": "Date", "shop": "Shop/Merchant",
                    "category": "Category", "amount": "Amount",
                    "notes": "Notes", "receipt": "Rcpt"}
        widths = {"id": 55, "date": 95, "shop": 180, "category": 110,
                  "amount": 95, "notes": 210, "receipt": 45}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            anchor = "w" if c in ("shop", "notes", "category") else "center"
            self.tree.column(c, width=widths[c], anchor=anchor)
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", lambda ev: self.edit_selected())
        self.tree.bind("<Delete>", lambda ev: self.delete_selected())

        self.result_label = ttk.Label(tab, text="")
        self.result_label.pack(anchor="w", padx=10)

        actions = ttk.Frame(tab)
        actions.pack(fill="x", padx=8, pady=4)
        ttk.Button(actions, text="\u2795 Add", command=self.reset_form).pack(side="left", padx=2)
        ttk.Button(actions, text="\u270f\ufe0f Edit", command=self.edit_selected).pack(side="left", padx=2)
        ttk.Button(actions, text="\U0001f5d1 Delete", command=self.delete_selected,
                   style="Danger.TButton").pack(side="left", padx=2)
        ttk.Button(actions, text="\U0001f4ce View Receipt",
                   command=self.view_selected_receipt).pack(side="left", padx=2)

        # ---------------------------- add / edit form
        form = ttk.LabelFrame(tab, text="Add / Edit Expense")
        form.pack(fill="x", padx=8, pady=(0, 8))
        self.form_shop = tk.StringVar()
        self.form_category = tk.StringVar(value="Other")
        self.form_amount = tk.StringVar()
        self.form_date = tk.StringVar(value=today_iso())
        self.form_currency = tk.StringVar(value="\u20b9")
        self.form_notes = tk.StringVar()

        frow1 = ttk.Frame(form)
        frow1.pack(fill="x", padx=6, pady=(6, 2))
        ttk.Label(frow1, text="Shop/Merchant:").pack(side="left")
        self.form_shop_entry = ttk.Entry(frow1, textvariable=self.form_shop,
                                         width=20)
        self.form_shop_entry.pack(side="left", padx=(2, 10))
        ttk.Label(frow1, text="Category:").pack(side="left")
        ttk.Combobox(frow1, textvariable=self.form_category, values=CATEGORIES,
                     state="readonly", width=13).pack(side="left", padx=(2, 10))
        ttk.Label(frow1, text="Amount:").pack(side="left")
        ttk.Entry(frow1, textvariable=self.form_amount, width=10).pack(side="left", padx=(2, 10))
        ttk.Label(frow1, text="Currency:").pack(side="left")
        ttk.Combobox(frow1, textvariable=self.form_currency, values=CURRENCIES,
                     state="readonly", width=4).pack(side="left", padx=(2, 10))

        frow2 = ttk.Frame(form)
        frow2.pack(fill="x", padx=6, pady=2)
        ttk.Label(frow2, text="Date:").pack(side="left")
        ttk.Entry(frow2, textvariable=self.form_date, width=12).pack(side="left", padx=(2, 4))
        ttk.Button(frow2, text="Pick\u2026", command=self.pick_date_for_form).pack(side="left", padx=2)
        ttk.Button(frow2, text="Today",
                   command=lambda: self.form_date.set(today_iso())).pack(side="left", padx=2)
        ttk.Label(frow2, text="   Notes:").pack(side="left")
        ttk.Entry(frow2, textvariable=self.form_notes, width=30).pack(side="left", padx=(2, 10))

        frow3 = ttk.Frame(form)
        frow3.pack(fill="x", padx=6, pady=(2, 6))
        self.save_btn = ttk.Button(frow3, text="Add Expense", command=self.save_form,
                                   style="Accent.TButton")
        self.save_btn.pack(side="left", padx=2)
        ttk.Button(frow3, text="Clear", command=self.reset_form).pack(side="left", padx=2)
        self.form_status = tk.Label(frow3, text="", fg=theme.PALETTE["positive"])
        self.form_status.pack(side="left", padx=10)

    def _build_receipt_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="\U0001f5a8\ufe0f Receipt Scanner")

        top = ttk.Frame(tab)
        top.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Button(top, text="\U0001f4c1 Upload Receipt\u2026",
                   command=self.upload_receipt).pack(side="left", padx=2)
        ttk.Button(top, text="\U0001f4f7 Capture from Camera",
                   command=self.capture_from_camera).pack(side="left", padx=2)
        ttk.Button(top, text="\U0001f501 Scan Again", command=self.rescan).pack(side="left", padx=2)
        ttk.Button(top, text="\U0001f441 View Receipt",
                   command=self.view_current_receipt).pack(side="left", padx=2)
        self.r_status = tk.StringVar(value="Upload a receipt image to start.")
        tk.Label(top, textvariable=self.r_status,
                 fg=theme.PALETTE["muted"]).pack(side="left", padx=12)

        body = ttk.Frame(tab)
        body.pack(fill="both", expand=True, padx=8, pady=4)
        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        self.r_preview = tk.Label(left, text="No image", width=34, height=14,
                                  relief="flat", bg=theme.PALETTE["surface2"],
                                  fg=theme.PALETTE["muted"])
        self.r_preview.pack()
        conf = ttk.Frame(left)
        conf.pack(fill="x", pady=6)
        ttk.Label(conf, text="OCR confidence:").pack(side="left")
        self.r_conf_bar = ttk.Progressbar(conf, length=110, maximum=100)
        self.r_conf_bar.pack(side="left", padx=6)
        self.r_conf_label = tk.Label(conf, text="\u2014")
        self.r_conf_label.pack(side="left")

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        ttk.Label(right, text="Raw OCR text:").pack(anchor="w")
        txt_frame = ttk.Frame(right)
        txt_frame.pack(fill="both", expand=True)
        self.r_ocr_text = tk.Text(txt_frame, height=11, wrap="word",
                                  bg=theme.PALETTE["surface2"],
                                  fg=theme.PALETTE["text"],
                                  insertbackground=theme.PALETTE["text"],
                                  relief="flat", highlightthickness=1,
                                  highlightbackground=theme.PALETTE["border"],
                                  highlightcolor=theme.PALETTE["accent"],
                                  font=(theme.FONT_FAMILY, 10))
        vsb = ttk.Scrollbar(txt_frame, command=self.r_ocr_text.yview)
        self.r_ocr_text.configure(yscrollcommand=vsb.set)
        self.r_ocr_text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        fields = ttk.LabelFrame(tab, text="Extracted information \u2014 review & correct before saving")
        fields.pack(fill="x", padx=8, pady=4)
        self.r_shop = tk.StringVar()
        self.r_date = tk.StringVar()
        self.r_total = tk.StringVar()
        self.r_currency = tk.StringVar(value="\u20b9")
        self.r_category = tk.StringVar(value="Other")
        self.r_notes = tk.StringVar()

        g1 = ttk.Frame(fields)
        g1.pack(fill="x", padx=6, pady=(6, 2))
        ttk.Label(g1, text="Shop/Merchant:").pack(side="left")
        ttk.Entry(g1, textvariable=self.r_shop, width=24).pack(side="left", padx=(2, 10))
        ttk.Label(g1, text="Date:").pack(side="left")
        ttk.Entry(g1, textvariable=self.r_date, width=12).pack(side="left", padx=(2, 4))
        ttk.Button(g1, text="Pick\u2026", command=self.pick_receipt_date).pack(side="left", padx=2)
        ttk.Label(g1, text="Total:").pack(side="left", padx=(10, 0))
        ttk.Entry(g1, textvariable=self.r_total, width=10).pack(side="left", padx=(2, 10))
        ttk.Label(g1, text="Currency:").pack(side="left")
        ttk.Combobox(g1, textvariable=self.r_currency, values=CURRENCIES,
                     state="readonly", width=4).pack(side="left", padx=(2, 10))

        g2 = ttk.Frame(fields)
        g2.pack(fill="x", padx=6, pady=2)
        ttk.Label(g2, text="Category:").pack(side="left")
        ttk.Combobox(g2, textvariable=self.r_category, values=CATEGORIES,
                     state="readonly", width=13).pack(side="left", padx=(2, 10))
        ttk.Label(g2, text="Notes:").pack(side="left")
        ttk.Entry(g2, textvariable=self.r_notes, width=30).pack(side="left", padx=(2, 10))

        items_frame = ttk.LabelFrame(tab, text="Detected items (best effort)")
        items_frame.pack(fill="x", padx=8, pady=4)
        self.r_items = tk.Listbox(items_frame, height=4,
                                  bg=theme.PALETTE["surface2"],
                                  fg=theme.PALETTE["text"],
                                  selectbackground=theme.PALETTE["selection"],
                                  selectforeground=theme.PALETTE["text"],
                                  highlightthickness=0, relief="flat",
                                  font=(theme.FONT_FAMILY, 10))
        self.r_items.pack(fill="x", padx=6, pady=6)

        bottom = ttk.Frame(tab)
        bottom.pack(fill="x", padx=8, pady=(4, 8))
        ttk.Button(bottom, text="\U0001f4be Save as Expense",
                   command=self.save_receipt,
                   style="Accent.TButton").pack(side="left", padx=2)
        self.r_saved_label = tk.Label(bottom, text="", fg=theme.PALETTE["positive"])
        self.r_saved_label.pack(side="left", padx=10)

    # -------------------------------------------------- time-based analysis

    def _build_period_panel(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Period:").pack(side="left")
        ttk.Combobox(frame, textvariable=self.period_var, values=PERIODS,
                     state="readonly", width=14).pack(side="left", padx=(2, 8))
        ttk.Label(frame, text="From:").pack(side="left")
        from_e = ttk.Entry(frame, textvariable=self.custom_from, width=10)
        from_e.pack(side="left", padx=(2, 2))
        ttk.Label(frame, text="to").pack(side="left")
        to_e = ttk.Entry(frame, textvariable=self.custom_to, width=10)
        to_e.pack(side="left", padx=(2, 8))
        from_e.config(state="disabled")
        to_e.config(state="disabled")
        self._period_entries.extend([from_e, to_e])
        return frame

    def period_bounds(self):
        """(start, end) dates for the selected period, or (None, None) for
        an unbounded period ('All time')."""
        today = date.today()
        p = self.period_var.get()
        if p == "Today":
            return today, today
        if p == "Yesterday":
            y = today - timedelta(days=1)
            return y, y
        if p == "Last 7 days":
            return today - timedelta(days=6), today
        if p == "This month":
            return today.replace(day=1), today
        if p == "Last month":
            end = today.replace(day=1) - timedelta(days=1)
            return end.replace(day=1), end
        if p == "This year":
            return today.replace(month=1, day=1), today
        if p == "All time":
            return None, None
        # Custom range
        f = parse_iso_date(self.custom_from.get())
        t = parse_iso_date(self.custom_to.get())
        if f and t:
            return min(f, t), max(f, t)
        if f:
            return f, today
        if t:
            return self._earliest_date() or today, t
        return None, None

    def previous_period_bounds(self):
        start, end = self.period_bounds()
        if start is None or end is None:
            return None, None
        length = (end - start).days + 1
        return start - timedelta(days=length), end - timedelta(days=length)

    def _earliest_date(self):
        dates = [e.date for e in db.get_all_expenses() if e.date]
        if not dates:
            return None
        try:
            return datetime.strptime(min(dates), "%Y-%m-%d").date()
        except ValueError:
            return None

    def expenses_for_range(self, start, end):
        """Expenses dated inside [start, end]; None bounds = open."""
        if start is None or end is None:
            return db.get_all_expenses()
        s, e = start.isoformat(), end.isoformat()
        return [x for x in db.get_all_expenses() if s <= x.date <= e]

    def expenses_in_period(self):
        return self.expenses_for_range(*self.period_bounds())

    def _on_period_changed(self, *_):
        custom = self.period_var.get() == "Custom range"
        for entry in self._period_entries:
            entry.config(state="normal" if custom else "disabled")
        if self._ready:
            self.refresh_dashboard()
            self.redraw_charts()

    def _on_chart_changed(self, *_):
        if self._ready:
            self.redraw_charts()

    # ------------------------------------------------------- charts tab

    def _build_charts_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="\U0001f4c8 Charts & Analytics")
        top = ttk.Frame(tab)
        top.pack(fill="x", padx=8, pady=(8, 4))
        self._build_period_panel(top).pack(side="left")
        ttk.Label(top, text="Chart:").pack(side="left", padx=(16, 0))
        self.chart_combo = ttk.Combobox(top, textvariable=self.chart_var,
                                        values=CHART_TYPES, state="readonly",
                                        width=34)
        self.chart_combo.pack(side="left", padx=(2, 8))
        if HAS_MATPLOTLIB:
            self.charts_fig = Figure(figsize=(8, 4.8), dpi=100)
            self.charts_canvas = FigureCanvasTkAgg(self.charts_fig, master=tab)
            self.charts_canvas.get_tk_widget().pack(
                fill="both", expand=True, padx=8, pady=4)
        else:
            ttk.Label(tab, text="Install matplotlib to see charts:  "
                      "pip install matplotlib").pack(pady=30)

    def redraw_charts(self):
        if not HAS_MATPLOTLIB:
            return
        kind = self.chart_var.get()
        start, end = self.period_bounds()
        expenses = self.expenses_for_range(start, end)
        if kind == CHART_TYPES[0]:
            charts.draw_category_pie(self.charts_fig, expenses)
        elif kind == CHART_TYPES[1]:
            charts.draw_monthly_bar(self.charts_fig, expenses)
        elif kind == CHART_TYPES[2]:
            charts.draw_daily_line(self.charts_fig, expenses)
        elif kind == CHART_TYPES[3]:
            charts.draw_category_comparison(self.charts_fig, expenses,
                                            db.get_budgets())
        elif kind == CHART_TYPES[4]:
            prev_start, prev_end = self.previous_period_bounds()
            previous = (self.expenses_for_range(prev_start, prev_end)
                        if prev_start is not None else [])
            charts.draw_period_comparison(self.charts_fig, expenses, previous)
        elif kind == CHART_TYPES[5]:
            charts.draw_top_merchants(self.charts_fig, expenses)
        else:
            charts.draw_spending_trend(self.charts_fig, expenses)
        self.charts_canvas.draw_idle()

    # ------------------------------------------------------- budgets

    def edit_budgets(self):
        BudgetDialog(self.root, on_save=self.refresh_dashboard)

    def show_tab(self, name):
        index = {"dashboard": 0, "expenses": 1, "receipts": 2,
                 "charts": 3}.get(name)
        if index is not None:
            self.notebook.select(index)

    def new_expense_dialog(self):
        """'New Payments' \u2014 jump to the expense form, ready to add."""
        self.show_tab("expenses")
        self.reset_form()
        if getattr(self, "form_shop_entry", None) is not None:
            self.form_shop_entry.focus_set()

    def set_dashboard_search(self, text):
        self.f_search.set(text)
        self.show_tab("expenses")
        self.apply_filters()

    # ------------------------------------------------------- dashboard logic

    def refresh_dashboard(self):
        if getattr(self, "dashboard", None) is not None:
            self.dashboard.refresh()

    # ------------------------------------------------------- expenses logic

    def refresh_expenses(self):
        self.refresh_month_combo()
        self.apply_filters()
        self.refresh_dashboard()
        self.redraw_charts()

    def refresh_month_combo(self):
        months = sorted({e.date[:7] for e in db.get_all_expenses()
                         if e.date and len(e.date) >= 7}, reverse=True)
        values = ["All months"] + months
        self.month_combo["values"] = values
        if self.f_month.get() not in values:
            self.f_month.set("All months")

    def apply_filters(self):
        query = self.f_search.get().strip()
        category = self.f_category.get()
        if category == "All categories":
            category = ""
        month = self.f_month.get()
        if month in ("", "All months"):
            month = ""
        amt_min = valid_amount(self.f_amt_min.get()) if self.f_amt_min.get().strip() else None
        amt_max = valid_amount(self.f_amt_max.get()) if self.f_amt_max.get().strip() else None
        date_from = self.f_date_from.get().strip() or None
        date_to = self.f_date_to.get().strip() or None
        self.expenses = db.search_expenses(
            query=query, category=category, month=month,
            amount_min=amt_min, amount_max=amt_max,
            date_from=date_from, date_to=date_to,
            shop=self.f_shop.get().strip(), notes=self.f_notes.get().strip())
        self.populate_tree(self.expenses)
        self.result_label.config(text=f"{len(self.expenses)} expense(s)")

    def clear_filters(self):
        for var in (self.f_search, self.f_shop, self.f_notes, self.f_amt_min,
                    self.f_amt_max, self.f_date_from, self.f_date_to):
            var.set("")
        self.f_category.set("All categories")
        self.f_month.set("All months")
        self.apply_filters()

    def populate_tree(self, expenses):
        self.tree.delete(*self.tree.get_children())
        for e in expenses:
            receipt = "\U0001f4ce" if e.receipt_path else ""
            self.tree.insert("", "end", values=(
                e.id, e.date, e.shop, e.category,
                format_money(e.amount, e.currency), e.notes, receipt))

    # ------------------------------------------------------- add / edit form

    def save_form(self):
        try:
            exp = Expense(
                shop=self.form_shop.get(),
                category=self.form_category.get(),
                amount=valid_amount(self.form_amount.get()),
                date=self.form_date.get().strip(),
                notes=self.form_notes.get(),
                currency=self.form_currency.get(),
            )
            if self.current_expense_id is not None:
                existing = db.get_expense(self.current_expense_id)
                if existing:
                    exp.id = existing.id
                    exp.receipt_path = existing.receipt_path
                    exp.receipt_confidence = existing.receipt_confidence
                db.update_expense(exp)
                self.form_status.config(text=f"Updated expense #{exp.id} \u2714")
            else:
                new_id = db.add_expense(exp)
                self.form_status.config(text=f"Added expense #{new_id} \u2714")
        except ValidationError as e:
            messagebox.showerror("Invalid expense", str(e))
            return
        self.reset_form()
        self.refresh_expenses()

    def reset_form(self):
        self.current_expense_id = None
        self.form_shop.set("")
        self.form_category.set("Other")
        self.form_amount.set("")
        self.form_date.set(today_iso())
        self.form_currency.set("\u20b9")
        self.form_notes.set("")
        self.save_btn.config(text="Add Expense")
        self.form_status.config(text="")

    def pick_date_for_form(self):
        initial = self.form_date.get().strip()
        try:
            initial = datetime.strptime(initial, "%Y-%m-%d").date()
        except ValueError:
            initial = date.today()
        CalendarDialog(self.root, initial=initial,
                       on_select=lambda iso: self.form_date.set(iso))

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing selected", "Select an expense in the list first.")
            return
        eid = self.tree.item(sel[0])["values"][0]
        exp = db.get_expense(eid)
        if not exp:
            return
        self.current_expense_id = exp.id
        self.form_shop.set(exp.shop)
        self.form_category.set(exp.category)
        self.form_amount.set(f"{exp.amount:.2f}".rstrip("0").rstrip("."))
        self.form_date.set(exp.date)
        self.form_currency.set(exp.currency or "\u20b9")
        self.form_notes.set(exp.notes)
        self.save_btn.config(text="Update Expense")
        self.form_status.config(text=f"Editing #{exp.id}")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing selected", "Select an expense in the list first.")
            return
        eid = self.tree.item(sel[0])["values"][0]
        exp = db.get_expense(eid)
        if not exp:
            return
        if not messagebox.askyesno(
                "Delete expense",
                f"Delete expense #{eid} ({exp.shop}, "
                f"{format_money(exp.amount, exp.currency)})?"):
            return
        db.delete_expense(eid)
        if (exp.receipt_path and exp.receipt_path.startswith(RECEIPTS_DIR)
                and os.path.exists(exp.receipt_path)):
            if messagebox.askyesno("Receipt image",
                                   "Delete the saved receipt image too?"):
                try:
                    os.remove(exp.receipt_path)
                except OSError:
                    pass
        if self.current_expense_id == eid:
            self.reset_form()
        self.refresh_expenses()

    def view_selected_receipt(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing selected", "Select an expense in the list first.")
            return
        eid = self.tree.item(sel[0])["values"][0]
        exp = db.get_expense(eid)
        if not exp or not exp.receipt_path:
            messagebox.showinfo("No receipt", "This expense has no linked receipt image.")
            return
        if not os.path.exists(exp.receipt_path):
            messagebox.showerror("Missing file", "The receipt image file was not found.")
            return
        self.show_receipt_preview(exp.receipt_path)

    # ------------------------------------------------------- receipt scanner

    def upload_receipt(self):
        path = filedialog.askopenfilename(
            title="Select a receipt image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                       ("All files", "*.*")])
        if path:
            self.load_receipt(path)

    def load_receipt(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Not found", f"Image not found:\n{path}")
            return
        self.last_receipt_image = path
        self.last_receipt = None
        self._set_preview(path)
        self.r_status.set(
            "Scanning\u2026 this can take a few seconds (first run loads the OCR model).")
        threading.Thread(target=self._scan_worker, args=(path,), daemon=True).start()

    def _scan_worker(self, path):
        try:
            info = ocr.scan(path)
        except Exception as e:
            self.root.after(0, lambda: self._scan_failed(str(e)))
            return
        self.root.after(0, lambda: self._apply_scan(path, info))

    def _scan_failed(self, msg):
        self.r_status.set("Scan failed")
        messagebox.showerror("OCR error", msg)

    def _apply_scan(self, path, info):
        self.last_receipt_image = path
        self.last_receipt = info
        self._set_preview(path)
        self.r_ocr_text.delete("1.0", "end")
        self.r_ocr_text.insert("1.0", info.get("text", ""))
        self.r_shop.set(info.get("shop") or "")
        self.r_date.set(info.get("date") or "")
        total = info.get("total") or 0.0
        self.r_total.set(f"{total:.2f}" if total else "")
        self.r_currency.set(info.get("currency") or "\u20b9")
        self.r_category.set(categorize(info.get("shop")) or "Other")
        self.r_items.delete(0, "end")
        currency = info.get("currency") or "\u20b9"
        for item in info.get("items") or []:
            self.r_items.insert(
                "end", f"{item['name']} \u2014 {format_money(item['price'], currency)}")
        conf = info.get("confidence") or 0.0
        self.r_conf_bar["value"] = conf
        if conf >= 80:
            color, note = theme.PALETTE["positive"], "high"
        elif conf >= 50:
            color, note = theme.PALETTE["warning"], "medium"
        else:
            color, note = theme.PALETTE["error"], "low \u2014 please double-check"
        self.r_conf_label.config(text=f"{conf:.0f}% ({note})", foreground=color)
        self.r_status.set("Scan complete \u2014 review the fields, then save.")

    def _set_preview(self, path, max_w=300, max_h=330):
        if not HAS_PIL:
            self.r_preview.config(image="", text="Pillow not installed\npip install pillow")
            return
        try:
            img = Image.open(path)
            img.thumbnail((max_w, max_h))
            photo = ImageTk.PhotoImage(img)
            self._thumb_photo = photo
            self.r_preview.config(image=photo, text="")
        except Exception as e:
            self.r_preview.config(image="", text=f"Could not preview:\n{e}")

    def rescan(self):
        if not self.last_receipt_image or not os.path.exists(self.last_receipt_image):
            messagebox.showinfo("No image", "Upload or capture a receipt first.")
            return
        self.load_receipt(self.last_receipt_image)

    def save_receipt(self):
        shop = self.r_shop.get().strip()
        if not shop:
            messagebox.showwarning("Missing info", "Enter the shop/merchant name.")
            return
        amount = valid_amount(self.r_total.get())
        if amount is None:
            messagebox.showwarning("Invalid amount", "Total must be a positive number.")
            return
        day = self.r_date.get().strip()
        try:
            datetime.strptime(day, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("Invalid date", "Date must be in YYYY-MM-DD format.")
            return

        src = self.last_receipt_image
        dest = ""
        if src and os.path.exists(src):
            ext = os.path.splitext(src)[1].lower() or ".jpg"
            dest = os.path.join(RECEIPTS_DIR,
                                f"expense_{datetime.now():%Y%m%d_%H%M%S}{ext}")
            try:
                shutil.copy2(src, dest)
            except OSError as e:
                messagebox.showerror("Copy failed", str(e))
                dest = ""

        conf = (self.last_receipt or {}).get("confidence")
        try:
            exp = Expense(
                shop=shop, category=self.r_category.get(), amount=amount,
                date=day, notes=self.r_notes.get().strip(),
                currency=self.r_currency.get(),
                receipt_path=dest, receipt_confidence=conf)
        except ValidationError as e:
            messagebox.showerror("Invalid expense", str(e))
            return
        new_id = db.add_expense(exp)
        self.r_saved_label.config(text=f"Saved as expense #{new_id} \u2714")
        self.reset_receipt_form()
        self.refresh_expenses()

    def reset_receipt_form(self):
        self.last_receipt = None
        self.last_receipt_image = None
        self._thumb_photo = None
        for var in (self.r_shop, self.r_date, self.r_total, self.r_notes):
            var.set("")
        self.r_currency.set("\u20b9")
        self.r_category.set("Other")
        self.r_items.delete(0, "end")
        self.r_ocr_text.delete("1.0", "end")
        self.r_preview.config(image="", text="No image")
        self.r_conf_bar["value"] = 0
        self.r_conf_label.config(text="\u2014")
        self.r_status.set("Upload a receipt image to start.")

    def pick_receipt_date(self):
        initial = self.r_date.get().strip()
        try:
            initial = datetime.strptime(initial, "%Y-%m-%d").date()
        except ValueError:
            initial = date.today()
        CalendarDialog(self.root, initial=initial,
                       on_select=lambda iso: self.r_date.set(iso))

    def view_current_receipt(self):
        path = self.last_receipt_image
        if not path or not os.path.exists(path):
            messagebox.showinfo("No image", "Upload or capture a receipt first.")
            return
        self.show_receipt_preview(path)

    def show_receipt_preview(self, path):
        if not HAS_PIL:
            messagebox.showwarning(
                "Missing dependency",
                "Pillow is required to preview images.\nInstall it with:  pip install pillow")
            return
        win = tk.Toplevel(self.root)
        win.title("Receipt")
        try:
            img = Image.open(path)
        except Exception as e:
            messagebox.showerror("Cannot open image", str(e))
            win.destroy()
            return
        img.thumbnail((760, 580))
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(win, image=photo)
        label.image = photo
        label.pack(padx=8, pady=8)

        def open_external():
            try:
                if os.name == "nt":
                    os.startfile(path)  # noqa: S606
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", path])
            except Exception as e:
                messagebox.showerror("Open failed", str(e))

        ttk.Button(win, text="Open in default viewer",
                   command=open_external).pack(pady=(0, 8))

    # ------------------------------------------------------- camera capture

    def capture_from_camera(self):
        try:
            import cv2
        except ImportError:
            messagebox.showerror(
                "Missing dependency",
                "Camera capture needs OpenCV.\nInstall it with:  pip install opencv-python")
            return
        if not HAS_PIL:
            messagebox.showerror(
                "Missing dependency",
                "Camera preview needs Pillow.\nInstall it with:  pip install pillow")
            return
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Camera", "Could not open the camera (index 0).")
            return
        win = tk.Toplevel(self.root)
        win.title("Camera \u2014 press SPACE to capture, ESC to cancel")
        win.resizable(False, False)
        ttk.Label(win, text="Press SPACE to capture \u00b7 ESC to cancel").pack()
        label = tk.Label(win, bg="black")
        label.pack(padx=6, pady=6)
        self._cam_photo = None
        running = {"stop": False}

        def update():
            if running["stop"]:
                return
            ok, frame = cap.read()
            if ok:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                img.thumbnail((640, 480))
                photo = ImageTk.PhotoImage(img)
                self._cam_photo = photo
                label.config(image=photo)
            win.after(50, update)

        def finish(path):
            if running["stop"]:
                return
            running["stop"] = True
            cap.release()
            win.destroy()
            if path:
                self.load_receipt(path)

        def on_key(event):
            if event.keysym == "Escape":
                finish(None)
            elif event.keysym in ("space", "Return"):
                ok, frame = cap.read()
                if ok:
                    path = os.path.join(
                        RECEIPTS_DIR, f"camera_{datetime.now():%Y%m%d_%H%M%S}.jpg")
                    cv2.imwrite(path, frame)
                    finish(path)

        win.bind("<KeyPress>", on_key)
        win.protocol("WM_DELETE_WINDOW", lambda: finish(None))
        win.focus_force()
        update()

    # ---------------------------------------------------------------- run

    def run(self):
        self.root.mainloop()


def main():
    db.init()
    root = tk.Tk()
    app = ExpenseApp(root)
    app.run()


if __name__ == "__main__":
    main()
