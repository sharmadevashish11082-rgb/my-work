"""Light fintech theme: dark teal brand on white surfaces.

Palette follows the dashboard design spec:

    --background: #173D40   (page / dashboard chrome)
    --surface: #FFFFFF      --surface-soft: #F7F8F5
    --text-primary: #111111 --text-secondary: #6B6F70
    --teal: #063F44         --green: #16C784   --yellow: #F4C94E
    --border: #E8EBE9

Tkinter cannot do true rounded corners, so buttons/cards use flat
surfaces with generous padding for the same feel.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

PALETTE = {
    "bg": "#F7F8F5",           # app background (soft off-white)
    "page": "#173D40",         # dark teal page (dashboard container screen)
    "surface": "#FFFFFF",      # cards / panels
    "surface2": "#F7F8F5",     # inputs, rows, soft pills
    "border": "#E8EBE9",
    "accent": "#063F44",       # primary brand teal
    "positive": "#16C784",     # green (only for positive changes)
    "warning": "#D97706",      # amber (budget warnings)
    "error": "#EF4444",        # red
    "yellow": "#F4C94E",       # secondary chart data
    "text": "#111111",         # main text (near-black)
    "muted": "#6B6F70",        # secondary text (gray)
    "selection": "#CDE8E4",    # teal-tinted selected rows
    "today": "#D8EFEA",        # calendar "today" highlight
    "accent_dark": "#FFFFFF",  # text on teal buttons
}

FONT_FAMILY = "Segoe UI"

_FONT_CANDIDATES = ("Inter", "Manrope", "Plus Jakarta Sans", "Poppins",
                    "Segoe UI", "Helvetica", "Arial")


def _pick_font(root):
    try:
        families = set(tkfont.families(root))
    except Exception:
        families = set()
    for name in _FONT_CANDIDATES:
        if name in families:
            return name
    return "TkDefaultFont"


def apply_theme(root):
    global FONT_FAMILY
    FONT_FAMILY = _pick_font(root)

    # ----- Tk widget defaults (applies to widgets created afterwards) -----
    root.configure(bg=PALETTE["bg"])
    root.option_add("*background", PALETTE["bg"])
    root.option_add("*foreground", PALETTE["text"])
    root.option_add("*selectBackground", PALETTE["selection"])
    root.option_add("*selectForeground", "#0B3B40")
    root.option_add("*activeBackground", PALETTE["border"])
    root.option_add("*activeForeground", PALETTE["text"])
    root.option_add("*highlightBackground", PALETTE["bg"])
    root.option_add("*highlightColor", PALETTE["border"])

    # ----- ttk styles (clam is the most styleable base theme) -------------
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=PALETTE["bg"],
                    foreground=PALETTE["text"], font=(FONT_FAMILY, 10),
                    borderwidth=0)
    style.configure("TFrame", background=PALETTE["bg"])
    style.configure("TLabel", background=PALETTE["bg"],
                    foreground=PALETTE["text"])
    style.configure("TLabelframe", background=PALETTE["bg"],
                    bordercolor=PALETTE["border"], relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=PALETTE["bg"],
                    foreground=PALETTE["text"])

    style.configure("TButton",
                    background=PALETTE["surface"], foreground=PALETTE["text"],
                    bordercolor=PALETTE["border"], borderwidth=1,
                    focuscolor=PALETTE["accent"], focusthickness=0,
                    padding=(14, 8), relief="flat")
    style.map("TButton",
              background=[("active", PALETTE["border"]),
                          ("pressed", PALETTE["accent"])],
              foreground=[("active", PALETTE["text"]),
                          ("pressed", PALETTE["accent_dark"])])

    style.configure("Accent.TButton",
                    background=PALETTE["accent"],
                    foreground=PALETTE["accent_dark"],
                    bordercolor=PALETTE["accent"], borderwidth=0,
                    padding=(14, 8), relief="flat")
    style.map("Accent.TButton",
              background=[("active", "#0A4F55"), ("pressed", "#063F44")],
              foreground=[("active", PALETTE["accent_dark"]),
                          ("pressed", PALETTE["accent_dark"])])

    style.configure("Danger.TButton",
                    background="#FDECEC", foreground="#DC2626",
                    bordercolor="#F5C2C2", borderwidth=1,
                    padding=(14, 8), relief="flat")
    style.map("Danger.TButton",
              background=[("active", PALETTE["error"])],
              foreground=[("active", "#FFFFFF")])

    style.configure("TEntry",
                    fieldbackground=PALETTE["surface"],
                    foreground=PALETTE["text"],
                    bordercolor=PALETTE["border"],
                    insertcolor=PALETTE["text"],
                    lightcolor=PALETTE["surface"],
                    darkcolor=PALETTE["surface"],
                    padding=(8, 6), relief="flat")
    style.map("TEntry",
              bordercolor=[("focus", PALETTE["accent"])],
              lightcolor=[("focus", PALETTE["accent"])],
              darkcolor=[("focus", PALETTE["accent"])])

    style.configure("TCombobox",
                    fieldbackground=PALETTE["surface"],
                    background=PALETTE["surface"],
                    foreground=PALETTE["text"],
                    arrowcolor=PALETTE["muted"],
                    bordercolor=PALETTE["border"],
                    padding=(8, 6), relief="flat")
    style.map("TCombobox",
              fieldbackground=[("readonly", PALETTE["surface"])],
              foreground=[("readonly", PALETTE["text"])],
              bordercolor=[("focus", PALETTE["accent"])])

    style.configure("TNotebook", background=PALETTE["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", background=PALETTE["surface"],
                    foreground=PALETTE["muted"], padding=(18, 10), borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", "#E4EFEE")],
              foreground=[("selected", PALETTE["accent"])])

    style.configure("Treeview", background=PALETTE["surface"],
                    fieldbackground=PALETTE["surface"],
                    foreground=PALETTE["text"], rowheight=32, borderwidth=0)
    style.configure("Treeview.Heading", background=PALETTE["surface2"],
                    foreground=PALETTE["muted"], relief="flat", padding=(8, 7))
    style.map("Treeview.Heading", background=[("active", PALETTE["border"])])
    style.map("Treeview",
              background=[("selected", PALETTE["selection"])],
              foreground=[("selected", "#0B3B40")])

    style.configure("TProgressbar", background=PALETTE["positive"],
                    troughcolor=PALETTE["border"],
                    bordercolor=PALETTE["border"],
                    lightcolor=PALETTE["positive"],
                    darkcolor=PALETTE["positive"])

    style.configure("Vertical.TScrollbar", background=PALETTE["border"],
                    troughcolor=PALETTE["bg"], bordercolor=PALETTE["bg"],
                    arrowcolor=PALETTE["muted"], relief="flat")
    style.configure("Horizontal.TScrollbar", background=PALETTE["border"],
                    troughcolor=PALETTE["bg"], bordercolor=PALETTE["bg"],
                    arrowcolor=PALETTE["muted"], relief="flat")

    # Combobox dropdown list colors
    root.option_add("*TCombobox*Listbox.background", PALETTE["surface"])
    root.option_add("*TCombobox*Listbox.foreground", PALETTE["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", PALETTE["selection"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#0B3B40")

    apply_matplotlib_style()


def apply_matplotlib_style():
    """Minimal light styling for the matplotlib charts."""
    try:
        import matplotlib
        from cycler import cycler
        matplotlib.rcParams.update({
            "figure.facecolor": PALETTE["bg"],
            "axes.facecolor": PALETTE["bg"],
            "axes.edgecolor": PALETTE["border"],
            "axes.labelcolor": PALETTE["muted"],
            "axes.titlecolor": PALETTE["text"],
            "axes.titlesize": 12,
            "text.color": PALETTE["text"],
            "xtick.color": PALETTE["muted"],
            "ytick.color": PALETTE["muted"],
            "grid.color": PALETTE["border"],
            "axes.grid": False,
            "axes.prop_cycle": cycler(color=[
                "#063F44", "#16C784", "#F4C94E", "#3B82F6",
                "#8B5CF6", "#EC4899", "#F97316", "#9CA3AF"]),
            "font.family": "sans-serif",
            "font.sans-serif": ["Inter", "Manrope", "Plus Jakarta Sans",
                                "Poppins", "Segoe UI", "DejaVu Sans"],
            "savefig.facecolor": PALETTE["bg"],
        })
    except Exception:
        pass
