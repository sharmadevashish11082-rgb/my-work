"""Premium fintech dashboard (pure Tkinter implementation of the design spec).

The spec is web-oriented (CSS Grid, Recharts, viewport units, rounded
corners), so this adapts it faithfully:

  * dark-teal page (#173D40) with a large centered white container,
  * header navigation, greeting, filter/utility row, key-stat strip,
  * a three-column grid (31/34/35) that stacks into one column on narrow
    windows,
  * matplotlib mini-charts (income line, expense bars, budget donut,
    money-flow line) that are decorative but data-driven,
  * real interactions: period filter, search, CSV download, New Payment,
    add-card modal, notification/settings dropdowns, expandable wealth tree.

Income history and wealth figures are not tracked by the app, so those
cards show the spec's sample values until real data exists.
"""

import math
import os
import re
import tkinter as tk
from collections import Counter
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox, ttk

import database as db
import theme
from utils import CATEGORIES, parse_iso_date, valid_amount

try:
    import charts
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MPL = True
except Exception:
    HAS_MPL = False

# ---- design tokens (from the spec) -------------------------------------
PAGE_BG = "#173D40"       # --background
PAGE_SHADOW = "#0F2C2F"   # subtle shadow under the container
TEAL = "#063F44"          # --teal
TEAL_LIGHT = "#0A4F55"
GREEN = "#16C784"         # --green
YELLOW = "#F4C94E"        # --yellow
RED = "#EF4444"
TEXT = "#111111"          # --text-primary
MUTED = "#6B6F70"         # --text-secondary
SOFT = "#F7F8F5"          # --surface-soft
CARD_BORDER = "#EEEEEE"
CORNER = 26               # container corner radius (Tkinter approximates)

PERIODS = ["Today", "Yesterday", "Last 7 days", "This month", "Last month",
           "This year", "All time"]

DEFAULT_INCOME = 2200.0

# Demo wealth overview (sample data straight from the design mockup)
WEALTH_ROWS = [
    ("Wealth Overview", 16531.54, "", True),
    ("Banking", 9681.49, "Wealth Overview", True),
    ("Checking Accounts", 7583.00, "Banking", True),
    ("Visa", 5299.52, "Checking Accounts", False),
    ("Save Target", 958.00, "Checking Accounts", False),
    ("Current balance", 7602.15, "Checking Accounts", False),
]


def compute_stats(expenses, start=None, end=None):
    """Dashboard statistics from a list of Expense objects.

    ``start``/``end`` are the selected analysis period (dates); when given,
    the average-daily figure is computed over that period's length.
    """
    today = date.today()
    total = sum(e.amount for e in expenses)
    today_total = sum(e.amount for e in expenses if e.date == today.isoformat())
    week_start = today - timedelta(days=today.weekday())
    week_total = sum(e.amount for e in expenses
                     if week_start.isoformat() <= e.date <= today.isoformat())
    month_total = sum(e.amount for e in expenses
                      if e.date.startswith(today.strftime("%Y-%m")))
    if start is not None and end is not None:
        avg_daily = total / max((end - start).days + 1, 1)
    else:
        dates = sorted({e.date for e in expenses if e.date})
        if dates:
            first = datetime.strptime(dates[0], "%Y-%m-%d").date()
            avg_daily = total / max((today - first).days + 1, 1)
        else:
            avg_daily = 0.0
    counts = Counter(e.category for e in expenses)
    return {"total": total, "today": today_total, "week": week_total,
            "month": month_total, "count": len(expenses),
            "avg_daily": avg_daily,
            "top_category": counts.most_common(1)[0][0] if counts else "\u2014"}


def _round_rect(c, x1, y1, x2, y2, r, **kw):
    """A smooth polygon that reads as a rounded rectangle."""
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def _fmt(v, cur):
    """Format money without forcing decimals on round numbers."""
    v = float(v)
    if abs(v - round(v)) < 0.005:
        return f"{cur}{v:,.0f}"
    return f"{cur}{v:,.2f}"


def _compact(v, cur):
    """Compact money: 25k / 4.4M style (large financial numbers)."""
    a = abs(v)
    sign = "-" if v < 0 else ""
    if a >= 1_000_000:
        return f"{sign}{cur}{a / 1_000_000:.1f}M"
    if a >= 1000:
        return f"{sign}{cur}{a / 1000:.1f}k"
    return f"{sign}{cur}{a:,.0f}"


class DashboardPanel(tk.Frame):
    """The home screen: fintech dashboard inside a white rounded container."""

    def __init__(self, master, app):
        super().__init__(master, bg=PAGE_BG)
        self.app = app
        self.root = app.root
        self._flash_job = None
        self._last_geom = None

        # canvas that draws the teal page + rounded white container
        self.rect_canvas = tk.Canvas(self, bg=PAGE_BG, highlightthickness=0,
                                     bd=0)
        self.rect_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.container = tk.Frame(self, bg="#FFFFFF")
        self._build_content()

        self.bind("<Configure>", lambda e: self.after_idle(self._place_container))
        self.after(60, self._place_container)
        self.after(120, self.refresh)

    # ------------------------------------------------------------- build

    def _card(self, parent):
        return tk.Frame(parent, bg="#FFFFFF", highlightthickness=1,
                        highlightbackground=CARD_BORDER, padx=16, pady=12)

    def _card_header(self, parent, title, action_text, action_cmd):
        row = tk.Frame(parent, bg="#FFFFFF")
        row.pack(fill="x")
        tk.Label(row, text=title, font=(theme.FONT_FAMILY, 16, "bold"),
                 bg="#FFFFFF", fg=TEXT).pack(side="left")
        if action_text:
            lbl = tk.Label(row, text=action_text, font=(theme.FONT_FAMILY, 11),
                           bg="#FFFFFF", fg=MUTED, cursor="hand2")
            lbl.pack(side="right")
            lbl.bind("<Button-1>", lambda e: action_cmd())

    def _nav_hover(self, lbl, active, entering):
        if active:
            return
        lbl.config(bg="#F0F3F1" if entering else "#FFFFFF")

    def _build_content(self):
        c = self.container

        # ---- header / navigation
        header = tk.Frame(c, bg="#FFFFFF")
        header.pack(fill="x", padx=26, pady=(14, 0))

        logo = tk.Canvas(header, width=30, height=30, bg="#FFFFFF",
                         highlightthickness=0)
        logo.create_oval(2, 2, 28, 28, fill="#111111", outline="")
        logo.create_text(15, 15, text="$", fill="#ffffff",
                         font=(theme.FONT_FAMILY, 13, "bold"))
        logo.pack(side="left")

        nav = tk.Frame(header, bg="#FFFFFF")
        nav.pack(side="left", padx=(14, 0))
        nav_items = [("Dashboard", True, None),
                     ("Transaction", False, lambda: self.app.show_tab("expenses")),
                     ("Payments", False, self.app.new_expense_dialog),
                     ("Exchange", False, lambda: self.flash("Exchange \u2014 coming soon.")),
                     ("Support", False, lambda: self.flash("Support \u2014 coming soon."))]
        for label, active, cmd in nav_items:
            lbl = tk.Label(nav, text=label,
                           bg="#111111" if active else "#FFFFFF",
                           fg="#ffffff" if active else TEXT,
                           font=(theme.FONT_FAMILY, 11,
                                 "bold" if active else "normal"),
                           padx=16, pady=6, cursor="hand2")
            lbl.pack(side="left", padx=3)
            if cmd:
                lbl.bind("<Button-1>", lambda e, f=cmd: f())
                lbl.bind("<Enter>",
                         lambda e, l=lbl, a=active: self._nav_hover(l, a, True))
                lbl.bind("<Leave>",
                         lambda e, l=lbl, a=active: self._nav_hover(l, a, False))

        right = tk.Frame(header, bg="#FFFFFF")
        right.pack(side="right")

        gear = tk.Label(right, text="\u2699\ufe0f",
                        font=(theme.FONT_FAMILY, 14), bg="#FFFFFF", fg=TEXT,
                        cursor="hand2")
        gear.pack(side="left", padx=8)
        gear.bind("<Button-1>", lambda e: self._menu_settings(gear))

        bell_wrap = tk.Frame(right, bg="#FFFFFF")
        bell_wrap.pack(side="left", padx=8)
        bell = tk.Label(bell_wrap, text="\U0001f514",
                        font=(theme.FONT_FAMILY, 13), bg="#FFFFFF", fg=TEXT,
                        cursor="hand2")
        bell.pack()
        bell.bind("<Button-1>", lambda e: self._menu_notify(bell))
        badge = tk.Label(bell_wrap, text="\u25cf", fg=RED, bg="#FFFFFF",
                         font=(theme.FONT_FAMILY, 8))
        badge.place(relx=1.0, x=-6, rely=0.0, y=-2)

        avatar = tk.Canvas(right, width=34, height=34, bg="#FFFFFF",
                           highlightthickness=0)
        avatar.create_oval(1, 1, 33, 33, fill=TEAL, outline="")
        avatar.create_text(17, 17, text="J", fill="#ffffff",
                           font=(theme.FONT_FAMILY, 13, "bold"))
        avatar.pack(side="left", padx=8)

        # ---- greeting
        greet = tk.Frame(c, bg="#FFFFFF")
        greet.pack(fill="x", padx=26, pady=(12, 0))
        hour = datetime.now().hour
        greeting = ("Good morning" if hour < 12
                    else "Good afternoon" if hour < 17 else "Good evening")
        name = db.get_setting("user_name", "James")
        tk.Label(greet, text=f"{greeting}, {name}",
                 font=(theme.FONT_FAMILY, 30, "bold"),
                 bg="#FFFFFF", fg=TEXT).pack(side="left")
        tk.Button(greet, text="+ New Payments",
                  command=self.app.new_expense_dialog,
                  bg=TEAL, fg="#ffffff", relief="flat",
                  activebackground=TEAL_LIGHT, activeforeground="#ffffff",
                  font=(theme.FONT_FAMILY, 12, "bold"),
                  padx=22, pady=10, cursor="hand2").pack(side="right")

        # ---- filter / utility row
        filters = tk.Frame(c, bg="#FFFFFF")
        filters.pack(fill="x", padx=26, pady=(12, 0))
        self.period_label = tk.StringVar(value=self.app.period_var.get())

        def pill(text, cmd, **kw):
            return tk.Button(filters, text=text, command=cmd, bg=SOFT, fg=TEXT,
                             activebackground="#E8EBE9", activeforeground=TEXT,
                             relief="flat", font=(theme.FONT_FAMILY, 11),
                             padx=16, pady=8, cursor="hand2", **kw)

        pill("Filter", lambda: self._menu_period(filters)).pack(side="left")
        pill("", lambda: self._menu_period(filters),
             textvariable=self.period_label).pack(side="left", padx=(8, 0))
        pill("Download", self.export_csv).pack(side="left", padx=(8, 0))

        right_f = tk.Frame(filters, bg="#FFFFFF")
        right_f.pack(side="right")
        search = tk.Frame(right_f, bg=SOFT, padx=10, pady=2)
        search.pack(side="left")
        tk.Label(search, text="\U0001f50d", bg=SOFT, fg=MUTED,
                 font=(theme.FONT_FAMILY, 10)).pack(side="left")
        self.search_var = tk.StringVar()
        entry = tk.Entry(search, textvariable=self.search_var, width=20,
                         bg=SOFT, fg=TEXT, relief="flat",
                         insertbackground=TEXT, highlightthickness=0,
                         font=(theme.FONT_FAMILY, 11))
        entry.pack(side="left", padx=(6, 0), ipady=4)
        entry.bind("<Return>", self._do_search)
        dots = tk.Button(right_f, text="\u22ee",
                         command=lambda: self._menu_settings(dots),
                         bg=SOFT, fg=TEXT, activebackground="#E8EBE9",
                         activeforeground=TEXT, relief="flat",
                         font=(theme.FONT_FAMILY, 12), padx=12, pady=6,
                         cursor="hand2")
        dots.pack(side="left", padx=(8, 0))

        # ---- key stats strip
        stats = tk.Frame(c, bg="#FFFFFF")
        stats.pack(fill="x", padx=26, pady=(10, 0))
        self.stat_labels = {}
        specs = [("Today", "today"), ("This week", "week"),
                 ("This month", "month"), ("Transactions", "count"),
                 ("Avg daily", "avg_daily"), ("Top category", "top_category")]
        for i, (label, key) in enumerate(specs):
            stats.columnconfigure(i, weight=1)
            card = tk.Frame(stats, bg=SOFT, padx=12, pady=8)
            card.grid(row=0, column=i, sticky="nsew", padx=4)
            tk.Label(card, text=label, bg=SOFT, fg=MUTED,
                     font=(theme.FONT_FAMILY, 9)).pack(anchor="w")
            val = tk.Label(card, text="\u2014", bg=SOFT, fg=TEXT,
                           font=(theme.FONT_FAMILY, 14, "bold"), anchor="w")
            val.pack(anchor="w", pady=(2, 0))
            self.stat_labels[key] = val

        # ---- three-column grid
        self.cols = tk.Frame(c, bg="#FFFFFF")
        self.cols.pack(fill="both", expand=True, padx=22, pady=(8, 4))
        self.col_left = tk.Frame(self.cols, bg="#FFFFFF")
        self.col_center = tk.Frame(self.cols, bg="#FFFFFF")
        self.col_right = tk.Frame(self.cols, bg="#FFFFFF")
        self._build_left()
        self._build_center()
        self._build_right()
        self.cols.bind("<Configure>", lambda e: self._relayout_cols())

        # ---- status line
        self.status_var = tk.StringVar()
        tk.Label(c, textvariable=self.status_var, bg="#FFFFFF", fg=MUTED,
                 font=(theme.FONT_FAMILY, 10)).pack(anchor="w", padx=30,
                                                    pady=(0, 10))

    def _build_left(self):
        # Income
        card = self._card(self.col_left)
        card.pack(fill="x", pady=6)
        self._card_header(card, "Income", "Past 30 days \u203a", None)
        row = tk.Frame(card, bg="#FFFFFF")
        row.pack(fill="x", pady=(10, 0))
        self.inc_value = tk.Label(row, text="\u2014",
                                  font=(theme.FONT_FAMILY, 30, "bold"),
                                  bg="#FFFFFF", fg=TEXT, cursor="hand2")
        self.inc_value.pack(side="left")
        self.inc_value.bind("<Button-1>", lambda e: self._set_income())
        self.inc_growth = tk.Label(row, text="", font=(theme.FONT_FAMILY, 12),
                                   bg="#FFFFFF", fg=GREEN)
        self.inc_growth.pack(side="left", padx=(12, 0), pady=(12, 0))
        self.holder_income = tk.Frame(card, bg="#FFFFFF", height=105)
        self.holder_income.pack(fill="both", expand=True, pady=(4, 0))
        self.holder_income.pack_propagate(False)

        # Expense Strategy
        card2 = self._card(self.col_left)
        card2.pack(fill="x", pady=6)
        self._card_header(card2, "Expense Strategy", "View details \u203a",
                          lambda: self.app.show_tab("charts"))
        self.exp_value = tk.Label(card2, text="\u2014",
                                  font=(theme.FONT_FAMILY, 26, "bold"),
                                  bg="#FFFFFF", fg=TEXT)
        self.exp_value.pack(anchor="w", pady=(10, 0))
        tk.Label(card2, text="Monthly Expense Insight",
                 font=(theme.FONT_FAMILY, 11),
                 bg="#FFFFFF", fg=MUTED).pack(anchor="w")
        self.holder_expense = tk.Frame(card2, bg="#FFFFFF", height=140)
        self.holder_expense.pack(fill="both", expand=True, pady=(4, 0))
        self.holder_expense.pack_propagate(False)

    def _build_center(self):
        # Overview (budget donut)
        card = self._card(self.col_center)
        card.pack(fill="x", pady=6)
        self._card_header(card, "Overview", "View details \u203a",
                          self.app.edit_budgets)
        self.holder_overview = tk.Frame(card, bg="#FFFFFF", height=185)
        self.holder_overview.pack(fill="both", expand=True, pady=(4, 0))
        self.holder_overview.pack_propagate(False)
        self.ov_legend = tk.Frame(card, bg="#FFFFFF")
        self.ov_legend.pack(fill="x", pady=(2, 0))
        self.ov_hint = tk.Label(card, text="", font=(theme.FONT_FAMILY, 10),
                                bg="#FFFFFF", fg=MUTED, wraplength=330,
                                justify="left")
        self.ov_hint.pack(anchor="w", pady=(4, 0))

        # Money Flow
        card2 = self._card(self.col_center)
        card2.pack(fill="x", pady=6)
        self._card_header(card2, "Money Flow", "Past 30 days \u203a", None)
        row = tk.Frame(card2, bg="#FFFFFF")
        row.pack(fill="x", pady=(10, 0))
        self.mf_value = tk.Label(row, text="\u2014",
                                 font=(theme.FONT_FAMILY, 28, "bold"),
                                 bg="#FFFFFF", fg=TEXT)
        self.mf_value.pack(side="left")
        self.mf_growth = tk.Label(row, text="", font=(theme.FONT_FAMILY, 12),
                                  bg="#FFFFFF", fg=GREEN)
        self.mf_growth.pack(side="left", padx=(12, 0), pady=(10, 0))
        self.holder_moneyflow = tk.Frame(card2, bg="#FFFFFF", height=120)
        self.holder_moneyflow.pack(fill="both", expand=True, pady=(4, 0))
        self.holder_moneyflow.pack_propagate(False)

    def _build_right(self):
        head = tk.Frame(self.col_right, bg="#FFFFFF")
        head.pack(fill="x", pady=6)
        tk.Label(head, text="My Finances",
                 font=(theme.FONT_FAMILY, 16, "bold"),
                 bg="#FFFFFF", fg=TEXT).pack(side="left")
        tk.Button(head, text="+ Add card",
                  command=lambda: AddCardDialog(self),
                  bg="#111111", fg="#ffffff", relief="flat",
                  activebackground="#333333", activeforeground="#ffffff",
                  font=(theme.FONT_FAMILY, 10, "bold"), padx=14, pady=6,
                  cursor="hand2").pack(side="right")

        self.card_canvas = tk.Canvas(self.col_right, width=264, height=172,
                                     bg="#FFFFFF", highlightthickness=0)
        self.card_canvas.pack(anchor="w", pady=6)
        self.card_canvas.bind("<Button-1>", lambda e: AddCardDialog(self))

        wealth = self._card(self.col_right)
        wealth.pack(fill="x", pady=6)
        self._card_header(wealth, "Wealth Overview", "", None)
        tree = ttk.Treeview(wealth, columns=("amount",), show="tree headings",
                            height=6)
        tree.heading("#0", text="")
        tree.heading("amount", text="")
        tree.column("#0", width=200, anchor="w", stretch=True)
        tree.column("amount", width=110, anchor="e", stretch=False)
        tree.tag_configure("main", foreground=TEXT,
                           font=(theme.FONT_FAMILY, 10, "bold"))
        tree.tag_configure("sub", foreground=MUTED)
        parents = {}
        for name, amount, parent, open_ in WEALTH_ROWS:
            tag = "main" if (parent or name == "Wealth Overview") else "sub"
            iid = tree.insert(parents.get(parent, ""), "end", text=name,
                              values=(f"${amount:,.2f}",), open=open_,
                              tags=(tag,))
            parents[name] = iid
        tree.pack(fill="x", pady=(6, 4))
        self.wealth_tree = tree

    # ------------------------------------------------------------- layout

    def _relayout_cols(self):
        w = self.cols.winfo_width()
        if w <= 0:
            return
        frames = (self.col_left, self.col_center, self.col_right)
        for f in frames:
            f.grid_forget()
        for i in range(3):
            self.cols.columnconfigure(i, weight=0)
            self.cols.rowconfigure(i, weight=0)
        self.cols.columnconfigure(0, weight=1)
        if w < 1150:
            # responsive: stack into a single column
            for i, f in enumerate(frames):
                self.cols.rowconfigure(i, weight=1)
                f.grid(row=i, column=0, sticky="nsew", padx=4, pady=4)
        else:
            self.cols.rowconfigure(0, weight=1)
            for i, (f, wt) in enumerate(zip(frames, (31, 34, 35))):
                self.cols.columnconfigure(i, weight=wt)
                f.grid(row=0, column=i, sticky="nsew", padx=6, pady=4)

    def _place_container(self):
        page_w, page_h = self.winfo_width(), self.winfo_height()
        if page_w < 60 or page_h < 60:
            return
        margin = max(22, int(page_w * 0.04))
        w = min(page_w - 2 * margin, 1280)
        x0 = int((page_w - w) / 2)
        y0 = margin
        self.update_idletasks()
        inner_h = self.container.winfo_reqheight()
        h = inner_h + 2 * CORNER
        geom = (x0, y0, w, h)
        if geom == self._last_geom:
            return
        self._last_geom = geom
        self.rect_canvas.delete("all")
        _round_rect(self.rect_canvas, x0 + 4, y0 + 8, x0 + w + 4, y0 + h + 8,
                    CORNER, fill=PAGE_SHADOW, outline="")
        _round_rect(self.rect_canvas, x0, y0, x0 + w, y0 + h,
                    CORNER, fill="#FFFFFF", outline="#E8EBE9")
        self.container.place(x=x0 + CORNER, y=y0 + CORNER,
                             width=w - 2 * CORNER,
                             height=max(h - 2 * CORNER, 80))

    # ------------------------------------------------------------ actions

    def flash(self, msg):
        self.status_var.set(msg)
        if self._flash_job is not None:
            try:
                self.root.after_cancel(self._flash_job)
            except Exception:
                pass
        self._flash_job = self.root.after(
            5000, lambda: self._clear_status(msg))

    def _clear_status(self, msg):
        if self.status_var.get() == msg:
            self.status_var.set("")

    def _do_search(self, event=None):
        self.app.set_dashboard_search(self.search_var.get().strip())

    def export_csv(self):
        start, end = self.app.period_bounds()
        expenses = self.app.expenses_for_range(start, end)
        if not expenses:
            messagebox.showinfo("Nothing to export",
                                "No expenses in the selected period.")
            return
        path = filedialog.asksaveasfilename(
            title="Export expenses", defaultextension=".csv",
            initialfile="expenses.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        n = db.export_csv(path, expenses)
        self.flash(f"Exported {n} expenses to {os.path.basename(path)}")

    def _set_income(self):
        SetIncomeDialog(self.root, on_save=self.refresh)

    def _about(self):
        messagebox.showinfo(
            "Expense Tracker",
            "Expense Tracker \u2014 pure Python (Tkinter + SQLite + EasyOCR)\n\n"
            "Dashboard layout follows the fintech design spec.\n"
            "Charts need:  pip install matplotlib\n"
            "OCR needs:    pip install easyocr")

    # ------------------------------------------------------------- menus

    def _menu_style(self):
        return dict(tearoff=0, bg="#FFFFFF", fg=TEXT,
                    activebackground="#E4EFEE", activeforeground=TEXT,
                    font=(theme.FONT_FAMILY, 10))

    def _post(self, m, w):
        try:
            m.tk_popup(w.winfo_rootx(), w.winfo_rooty() + w.winfo_height())
        finally:
            m.grab_release()

    def _menu_period(self, w):
        m = tk.Menu(self.root, **self._menu_style())
        for p in PERIODS:
            m.add_radiobutton(label=p, variable=self.app.period_var, value=p)
        m.add_separator()
        m.add_command(label="Custom range\u2026", command=self._custom_range_dialog)
        self._post(m, w)

    def _menu_settings(self, w):
        m = tk.Menu(self.root, **self._menu_style())
        m.add_command(label="Set monthly income\u2026", command=self._set_income)
        m.add_command(label="Edit budgets\u2026", command=self.app.edit_budgets)
        m.add_command(label="Export CSV\u2026", command=self.export_csv)
        m.add_separator()
        m.add_command(label="About\u2026", command=self._about)
        self._post(m, w)

    def _menu_notify(self, w):
        m = tk.Menu(self.root, **self._menu_style())
        msgs = self._notifications()
        if not msgs:
            msgs = ["No new notifications"]
        for msg in msgs:
            m.add_command(label=msg, state="disabled")
        self._post(m, w)

    def _notifications(self):
        msgs = []
        start, end = self.app.period_bounds()
        expenses = self.app.expenses_for_range(start, end)
        cur = self._main_currency()
        budgets = db.get_budgets()
        spent = sum(e.amount for e in expenses)
        overall = budgets.get("Overall")
        if overall:
            pct = spent / overall * 100 if overall else 0.0
            if pct > 100:
                msgs.append(f"\u26a0 Overall budget exceeded: "
                            f"{_fmt(spent, cur)} of {_fmt(overall, cur)}")
            elif pct >= 80:
                msgs.append(f"\u26a0 Approaching overall budget ({pct:.0f}% used)")
        for cat in CATEGORIES:
            b = budgets.get(cat)
            if not b:
                continue
            s = sum(e.amount for e in expenses if e.category == cat)
            if s > b:
                msgs.append(f"\u26a0 {cat} over budget: "
                            f"{_fmt(s, cur)} of {_fmt(b, cur)}")
            elif s >= 0.8 * b:
                msgs.append(f"\u26a0 {cat} approaching budget "
                            f"({s / b * 100:.0f}% used)")
        if not msgs:
            msgs.append("No new notifications")
        msgs.append("Demo dashboard \u2014 expenses are yours; "
                    "income & wealth are samples.")
        return msgs

    def _custom_range_dialog(self):
        CustomRangeDialog(self.root, app=self.app)

    # ------------------------------------------------------------- refresh

    def _main_currency(self):
        start, end = self.app.period_bounds()
        expenses = self.app.expenses_for_range(start, end)
        return (Counter(e.currency for e in expenses).most_common(1)[0][0]
                if expenses else "\u20b9")

    def _fig(self, w, h):
        fig = Figure(figsize=(w, h), dpi=100)
        fig.patch.set_facecolor("#FFFFFF")
        return fig

    def _chart_or_hint(self, holder, fig):
        for child in holder.winfo_children():
            child.destroy()
        if not HAS_MPL:
            tk.Label(holder, text="pip install matplotlib", bg="#FFFFFF",
                     fg=MUTED,
                     font=(theme.FONT_FAMILY, 10)).pack(pady=18)
            return
        canvas = FigureCanvasTkAgg(fig, master=holder)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()

    def refresh(self):
        self.period_label.set(self.app.period_var.get())
        self._refresh_stats()
        self._refresh_income()
        self._refresh_expense_strategy()
        self._refresh_overview()
        self._refresh_money_flow()
        self._refresh_card()
        self.after_idle(self._place_container)

    def _refresh_stats(self):
        start, end = self.app.period_bounds()
        expenses = self.app.expenses_for_range(start, end)
        stats = compute_stats(expenses, start, end)
        cur = self._main_currency()
        self.stat_labels["today"].config(text=_fmt(stats["today"], cur))
        self.stat_labels["week"].config(text=_fmt(stats["week"], cur))
        self.stat_labels["month"].config(text=_fmt(stats["month"], cur))
        self.stat_labels["count"].config(text=str(stats["count"]))
        self.stat_labels["avg_daily"].config(text=_fmt(stats["avg_daily"], cur))
        self.stat_labels["top_category"].config(text=stats["top_category"])

    def _refresh_income(self):
        cur = self._main_currency()
        try:
            income = float(db.get_setting("monthly_income", DEFAULT_INCOME))
        except (TypeError, ValueError):
            income = DEFAULT_INCOME
        self.inc_value.config(text=_fmt(income, cur))
        if abs(income - DEFAULT_INCOME) < 0.01:
            # spec's sample growth; no income history is tracked
            self.inc_growth.config(text="\u2197 8.25%", fg=GREEN)
        else:
            self.inc_growth.config(text="\u2014 no history yet", fg=MUTED)
        if HAS_MPL:
            pts = [income * (0.86 + 0.07 * math.sin(i / 3.0 + 1.7)
                             + 0.03 * math.sin(i / 1.3))
                   for i in range(30)]
            fig = self._fig(3.7, 1.35)
            charts.draw_smooth_line(fig, pts, color=TEAL, marker_index=15)
            self._chart_or_hint(self.holder_income, fig)

    def _refresh_expense_strategy(self):
        start, end = self.app.period_bounds()
        expenses = self.app.expenses_for_range(start, end)
        cur = self._main_currency()
        total = sum(e.amount for e in expenses)
        self.exp_value.config(text=_compact(total, cur) if expenses else "\u2014")
        cats = charts.category_totals(expenses) if HAS_MPL else {}
        labels = list(cats.keys())[:3]
        values = list(cats.values())[:3]
        pct = self._period_change()
        if HAS_MPL:
            fig = self._fig(3.7, 1.5)
            charts.draw_expense_bars(fig, labels, values,
                                     value_labels=[_compact(v, cur)
                                                   for v in values],
                                     change_pct=pct)
            self._chart_or_hint(self.holder_expense, fig)

    def _period_change(self):
        """% change of spending vs the previous equivalent period, or None."""
        start, end = self.app.period_bounds()
        if start is None or end is None:
            return None
        total = sum(e.amount
                    for e in self.app.expenses_for_range(start, end))
        prev_start, prev_end = self.app.previous_period_bounds()
        if prev_start is None:
            return None
        prev_total = sum(e.amount for e in
                         self.app.expenses_for_range(prev_start, prev_end))
        if prev_total <= 0:
            return None
        return (total - prev_total) / prev_total * 100

    def _refresh_overview(self):
        start, end = self.app.period_bounds()
        expenses = self.app.expenses_for_range(start, end)
        cur = self._main_currency()
        spent = sum(e.amount for e in expenses)
        overall = db.get_budgets().get("Overall")
        if overall:
            available = max(overall - spent, 0.0)
            planned = min(spent, overall)
            other = max(spent - overall, 0.0)
            segments = [(available, TEAL), (planned, GREEN), (other, YELLOW)]
            center_text = _compact(available, cur)
            center_label = "Available balance"
            legend = [("Available", available, TEAL),
                      ("Planned", planned, GREEN),
                      ("Other", other, YELLOW)]
            hint = ""
        else:
            segments = [(0.0, TEAL), (spent, GREEN), (0.0, YELLOW)]
            center_text = _compact(spent, cur) if spent else "\u2014"
            center_label = "Spent this period"
            legend = [("Spent", spent, GREEN)] if spent else []
            hint = ("No monthly budget set \u2014 click \u201cView details\u201d "
                    "to add one.")
        if HAS_MPL:
            fig = self._fig(2.7, 2.1)
            charts.draw_overview_donut(fig, segments, center_text, center_label)
            self._chart_or_hint(self.holder_overview, fig)
        for child in self.ov_legend.winfo_children():
            child.destroy()
        for name, val, color in legend:
            tk.Label(self.ov_legend, text="\u25cf", fg=color, bg="#FFFFFF",
                     font=(theme.FONT_FAMILY, 9)).pack(side="left", padx=(0, 4))
            tk.Label(self.ov_legend, text=f"{name}  {_compact(val, cur)}",
                     bg="#FFFFFF", fg=MUTED,
                     font=(theme.FONT_FAMILY, 10)).pack(side="left", padx=(0, 14))
        self.ov_hint.config(text=hint)

    def _refresh_money_flow(self):
        start, end = self.app.period_bounds()
        expenses = self.app.expenses_for_range(start, end)
        cur = self._main_currency()
        total = sum(e.amount for e in expenses)
        self.mf_value.config(text=_fmt(total, cur) if expenses else "\u2014")
        pct = self._period_change()
        if pct is None:
            self.mf_growth.config(text="\u2014", fg=MUTED)
        elif pct <= 0:
            self.mf_growth.config(
                text=f"\u2198 {abs(pct):.1f}% vs previous period", fg=GREEN)
        else:
            self.mf_growth.config(
                text=f"\u2197 {pct:.1f}% vs previous period", fg=RED)
        if HAS_MPL:
            fig = self._fig(3.9, 1.45)
            days = charts.daily_totals(expenses)
            charts.draw_smooth_line(fig, list(days.values()), color=TEAL,
                                    marker_index=len(days) - 1)
            self._chart_or_hint(self.holder_moneyflow, fig)

    def _refresh_card(self):
        cards = db.get_cards()
        if cards:
            brand = cards[0]["brand"]
            last4 = cards[0]["last4"]
            holder = cards[0]["holder"]
            expiry = cards[0]["expiry"]
        else:
            brand, last4, holder, expiry = "VISA", "5491", "James Smith", "12/2030"
        self._draw_card(brand, last4, holder, expiry)

    def _draw_card(self, brand, last4, holder, expiry):
        c = self.card_canvas
        c.delete("all")
        w, h = 264, 172
        _round_rect(c, 4, 4, w - 4, h - 4, 16, fill=TEAL, outline="")
        c.create_text(22, 30, text=brand,
                      font=(theme.FONT_FAMILY, 19, "bold italic"),
                      fill="#ffffff", anchor="w")
        c.create_text(22, 92, text=f"****  ****  ****  {last4}",
                      font=(theme.FONT_FAMILY, 13), fill="#ffffff", anchor="w")
        c.create_text(22, 118, text="EXPIRES   END",
                      font=(theme.FONT_FAMILY, 7), fill="#BFD7D6", anchor="w")
        c.create_text(22, 132, text=expiry,
                      font=(theme.FONT_FAMILY, 11, "bold"),
                      fill="#ffffff", anchor="w")
        c.create_text(22, 152, text=holder,
                      font=(theme.FONT_FAMILY, 10), fill="#ffffff", anchor="w")
        # Mastercard-style overlapping circles (bottom-right)
        c.create_oval(w - 58, h - 46, w - 24, h - 12, fill="#EB001B", outline="")
        c.create_oval(w - 44, h - 46, w - 10, h - 12, fill="#F79E1B", outline="")


# ------------------------------------------------------------------ dialogs


class SetIncomeDialog(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Monthly income")
        self.resizable(False, False)
        self.transient(parent)
        self.on_save = on_save
        body = tk.Frame(self, bg=theme.PALETTE["bg"])
        body.pack(padx=12, pady=12)
        tk.Label(body, text="Your monthly income (shown on the Income card):",
                 bg=theme.PALETTE["bg"], fg=theme.PALETTE["text"],
                 font=(theme.FONT_FAMILY, 10)).pack(anchor="w")
        current = db.get_setting("monthly_income", DEFAULT_INCOME)
        self.var = tk.StringVar(value=f"{current}")
        self.entry = ttk.Entry(body, textvariable=self.var, width=16)
        self.entry.pack(anchor="w", pady=(8, 0))
        btns = tk.Frame(body, bg=theme.PALETTE["bg"])
        btns.pack(pady=(10, 0))
        ttk.Button(btns, text="Save", style="Accent.TButton",
                   command=self._save).pack(side="left", padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.entry.focus_set()
        self.bind("<Return>", lambda e: self._save())

    def _save(self):
        amount = valid_amount(self.var.get())
        if amount is None:
            messagebox.showwarning("Invalid amount",
                                   "Enter a positive number.")
            return
        db.set_setting("monthly_income", f"{amount:.2f}")
        if self.on_save:
            self.on_save()
        self.destroy()


class CustomRangeDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Custom date range")
        self.resizable(False, False)
        self.transient(parent)
        body = tk.Frame(self, bg=theme.PALETTE["bg"])
        body.pack(padx=12, pady=12)
        tk.Label(body, text="From (YYYY-MM-DD):",
                 bg=theme.PALETTE["bg"], fg=theme.PALETTE["text"],
                 font=(theme.FONT_FAMILY, 10)).grid(row=0, column=0, sticky="w", pady=2)
        self.f = tk.StringVar(value=app.custom_from.get())
        ttk.Entry(body, textvariable=self.f, width=12).grid(row=0, column=1,
                                                            padx=6, pady=2)
        tk.Label(body, text="To (YYYY-MM-DD):",
                 bg=theme.PALETTE["bg"], fg=theme.PALETTE["text"],
                 font=(theme.FONT_FAMILY, 10)).grid(row=1, column=0, sticky="w", pady=2)
        self.t = tk.StringVar(value=app.custom_to.get())
        ttk.Entry(body, textvariable=self.t, width=12).grid(row=1, column=1,
                                                            padx=6, pady=2)
        btns = tk.Frame(body, bg=theme.PALETTE["bg"])
        btns.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btns, text="Apply", style="Accent.TButton",
                   command=self._apply).pack(side="left", padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=4)

    def _apply(self):
        f = parse_iso_date(self.f.get().strip())
        t = parse_iso_date(self.t.get().strip())
        if not f or not t:
            messagebox.showwarning("Invalid date",
                                   "Dates must be YYYY-MM-DD.")
            return
        self.app.custom_from.set(min(f, t).isoformat())
        self.app.custom_to.set(max(f, t).isoformat())
        self.app.period_var.set("Custom range")
        self.destroy()


class AddCardDialog(tk.Toplevel):
    def __init__(self, panel):
        super().__init__(panel.root)
        self.panel = panel
        self.title("Credit cards")
        self.transient(panel.root)
        self.resizable(False, False)
        body = tk.Frame(self, bg=theme.PALETTE["bg"])
        body.pack(padx=12, pady=12)
        tk.Label(body, text="Add a card", font=(theme.FONT_FAMILY, 11, "bold"),
                 bg=theme.PALETTE["bg"], fg=theme.PALETTE["text"]).pack(anchor="w")
        form = tk.Frame(body, bg=theme.PALETTE["bg"])
        form.pack(fill="x", pady=(6, 0))
        self.brand = tk.StringVar(value="VISA")
        tk.Label(form, text="Brand:", bg=theme.PALETTE["bg"],
                 fg=theme.PALETTE["text"],
                 font=(theme.FONT_FAMILY, 10)).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Combobox(form, textvariable=self.brand, width=10,
                     values=["VISA", "Mastercard", "RuPay", "Amex"],
                     state="readonly").grid(row=0, column=1, padx=6, pady=2)
        tk.Label(form, text="Last 4 digits:", bg=theme.PALETTE["bg"],
                 fg=theme.PALETTE["text"],
                 font=(theme.FONT_FAMILY, 10)).grid(row=1, column=0, sticky="w", pady=2)
        self.last4 = tk.StringVar()
        ttk.Entry(form, textvariable=self.last4, width=10).grid(row=1, column=1,
                                                                padx=6, pady=2)
        tk.Label(form, text="Card holder:", bg=theme.PALETTE["bg"],
                 fg=theme.PALETTE["text"],
                 font=(theme.FONT_FAMILY, 10)).grid(row=2, column=0, sticky="w", pady=2)
        self.holder = tk.StringVar()
        ttk.Entry(form, textvariable=self.holder, width=14).grid(row=2, column=1,
                                                                 padx=6, pady=2)
        tk.Label(form, text="Expiry (MM/YYYY):", bg=theme.PALETTE["bg"],
                 fg=theme.PALETTE["text"],
                 font=(theme.FONT_FAMILY, 10)).grid(row=3, column=0, sticky="w", pady=2)
        self.expiry = tk.StringVar()
        ttk.Entry(form, textvariable=self.expiry, width=10).grid(row=3, column=1,
                                                                 padx=6, pady=2)
        ttk.Button(form, text="Add card", style="Accent.TButton",
                   command=self._add).grid(row=4, column=0, columnspan=2,
                                           pady=(8, 0))
        tk.Label(body, text="Saved cards:", bg=theme.PALETTE["bg"],
                 fg=theme.PALETTE["text"],
                 font=(theme.FONT_FAMILY, 10)).pack(anchor="w", pady=(10, 2))
        cols = ("brand", "number", "holder", "expiry")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=4)
        for c, label, w in (("brand", "Brand", 80), ("number", "Number", 130),
                            ("holder", "Holder", 110), ("expiry", "Expiry", 80)):
            self.tree.heading(c, text=label)
            self.tree.column(c, width=w)
        self.tree.pack(fill="x")
        btns = tk.Frame(body, bg=theme.PALETTE["bg"])
        btns.pack(fill="x", pady=(8, 0))
        ttk.Button(btns, text="Delete selected", style="Danger.TButton",
                   command=self._delete).pack(side="left")
        ttk.Button(btns, text="Close", command=self.destroy).pack(side="right")
        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        for card in db.get_cards():
            self.tree.insert("", "end", iid=str(card["id"]),
                             values=(card["brand"], f"**** {card['last4']}",
                                     card["holder"], card["expiry"]))

    def _add(self):
        brand = self.brand.get()
        last4 = self.last4.get().strip()
        holder = self.holder.get().strip()
        expiry = self.expiry.get().strip()
        if not re.fullmatch(r"\d{4}", last4):
            messagebox.showwarning("Invalid number",
                                   "Last 4 digits must be 4 numbers.")
            return
        if not holder:
            messagebox.showwarning("Missing name",
                                   "Enter the card holder name.")
            return
        if not re.fullmatch(r"\d{2}/\d{4}", expiry):
            messagebox.showwarning("Invalid expiry",
                                   "Expiry must be in MM/YYYY format.")
            return
        db.add_card(brand, last4, holder, expiry)
        self.last4.set("")
        self.holder.set("")
        self.expiry.set("")
        self._load()
        self.panel.refresh()

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        db.delete_card(int(sel[0]))
        self._load()
        self.panel.refresh()
