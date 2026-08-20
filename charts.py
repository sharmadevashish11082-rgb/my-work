"""Chart helpers for the dashboard (matplotlib)."""

import matplotlib

matplotlib.use("TkAgg")


def category_totals(expenses):
    totals = {}
    for e in expenses:
        totals[e.category] = totals.get(e.category, 0.0) + e.amount
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def monthly_totals(expenses):
    totals = {}
    for e in expenses:
        month = (e.date or "")[:7]
        if month:
            totals[month] = totals.get(month, 0.0) + e.amount
    return dict(sorted(totals.items()))


def draw_category_pie(figure, expenses):
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    data = category_totals(expenses)
    if not data:
        ax.text(0.5, 0.5, "No expenses yet", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        return figure
    ax.pie(list(data.values()), labels=list(data.keys()),
           autopct="%1.1f%%", startangle=90)
    ax.set_title("Spending by Category")
    return figure


def draw_monthly_bar(figure, expenses):
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    data = monthly_totals(expenses)
    if not data:
        ax.text(0.5, 0.5, "No expenses yet", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        return figure
    months = list(data.keys())
    values = list(data.values())
    ax.bar(months, values)
    ax.set_title("Monthly Spending")
    ax.set_ylabel("Amount")
    ax.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    return figure


def _no_data(ax):
    ax.text(0.5, 0.5, "No expenses in this period",
            ha="center", va="center", fontsize=12)
    ax.set_axis_off()


def _minimal(ax):
    """Hide the top/right spines for a cleaner look."""
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def daily_totals(expenses):
    totals = {}
    for e in expenses:
        day = (e.date or "")[:10]
        if day:
            totals[day] = totals.get(day, 0.0) + e.amount
    return dict(sorted(totals.items()))


def top_merchants(expenses, limit=10):
    totals = {}
    for e in expenses:
        shop = (e.shop or "Unknown").strip() or "Unknown"
        totals[shop] = totals.get(shop, 0.0) + e.amount
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:limit])


def cumulative_totals(expenses):
    total = 0.0
    out = {}
    for day, amount in daily_totals(expenses).items():
        total += amount
        out[day] = total
    return out


def draw_daily_line(figure, expenses):
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    data = daily_totals(expenses)
    if not data:
        _no_data(ax)
        return figure
    ax.plot(list(data.keys()), list(data.values()), marker="o",
            linestyle="-", linewidth=1.5)
    ax.set_title("Daily Spending")
    ax.set_ylabel("Amount")
    ax.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    return figure


def draw_category_comparison(figure, expenses, budgets=None):
    """Grouped bar: actual spend vs budget per category."""
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    budgets = budgets or {}
    actual = category_totals(expenses)
    cats = sorted(set(list(actual.keys()) + [c for c in budgets if c != "Overall"]))
    if not cats:
        _no_data(ax)
        return figure
    x = list(range(len(cats)))
    act = [actual.get(c, 0.0) for c in cats]
    bud = [budgets.get(c) for c in cats]
    width = 0.35
    ax.bar([i - width / 2 for i in x], act, width, label="Actual")
    if any(b is not None for b in bud):
        ax.bar([i + width / 2 for i in x], [b or 0.0 for b in bud], width,
               label="Budget", alpha=0.6)
        ax.legend()
    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=45, ha="right")
    ax.set_title("Category Comparison (actual vs budget)")
    ax.set_ylabel("Amount")
    figure.tight_layout()
    return figure


def draw_period_comparison(figure, current_expenses, previous_expenses):
    """Grouped bar: this period vs the previous equivalent period per category."""
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    cur = category_totals(current_expenses)
    prev = category_totals(previous_expenses)
    cats = sorted(set(list(cur.keys()) + list(prev.keys())))
    if not cats:
        _no_data(ax)
        return figure
    x = list(range(len(cats)))
    width = 0.35
    ax.bar([i - width / 2 for i in x], [cur.get(c, 0.0) for c in cats], width,
           label="This period")
    ax.bar([i + width / 2 for i in x], [prev.get(c, 0.0) for c in cats], width,
           label="Previous period", alpha=0.6)
    ax.legend()
    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=45, ha="right")
    ax.set_title("Period Comparison (this vs previous)")
    ax.set_ylabel("Amount")
    figure.tight_layout()
    return figure


def draw_top_merchants(figure, expenses):
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    data = top_merchants(expenses)
    if not data:
        _no_data(ax)
        return figure
    names = list(data.keys())
    values = list(data.values())
    ax.barh(names[::-1], values[::-1])
    ax.set_title("Top Merchants")
    ax.set_xlabel("Amount")
    figure.tight_layout()
    return figure


def draw_spending_trend(figure, expenses):
    """Cumulative spending over time."""
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    data = cumulative_totals(expenses)
    if not data:
        _no_data(ax)
        return figure
    ax.plot(list(data.keys()), list(data.values()), linewidth=2)
    ax.set_title("Spending Trend (cumulative)")
    ax.set_ylabel("Cumulative amount")
    ax.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    return figure


# ---------------------------------------------------------------- dashboard


def _smooth(values, window=3):
    """Light moving-average smoothing (no numpy needed)."""
    if len(values) < 3:
        return list(values)
    out = []
    half = window // 2
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


def _arc_patch(ax, center, radius, theta1, theta2, width, color, alpha=1.0,
               dashes=None):
    """A thick arc with rounded caps, used for the donut ring segments."""
    import math
    from matplotlib.path import Path
    import matplotlib.patches as mpatches

    sweep = abs(theta2 - theta1)
    n = max(int(sweep / 2) + 2, 8)
    angles = [math.radians(theta1 + (theta2 - theta1) * i / (n - 1))
              for i in range(n)]
    verts = [(center[0] + radius * math.cos(a),
              center[1] + radius * math.sin(a)) for a in angles]
    codes = [Path.MOVETO] + [Path.LINETO] * (n - 1)
    patch = mpatches.PathPatch(Path(verts, codes), lw=width, edgecolor=color,
                               facecolor="none", alpha=alpha, capstyle="round")
    if dashes:
        patch.set_dashes(dashes)
    ax.add_patch(patch)


def draw_smooth_line(figure, values, color="#063F44", marker_index=None):
    """Minimal smooth line with a pale fill, guide lines and an optional
    vertical marker. No axes \u2014 decorative but sized to the data."""
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    if not values:
        _no_data(ax)
        return figure
    ys = _smooth(list(values))
    xs = list(range(len(ys)))
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1.0
    floor = lo - span * 0.25
    ax.fill_between(xs, ys, floor, color=color, alpha=0.10)
    ax.plot(xs, ys, color=color, linewidth=2)
    for f in (0.25, 0.5, 0.75):
        ax.axhline(lo + span * f, color="#E8EBE9", linewidth=0.8)
    if marker_index is not None and 0 <= marker_index < len(xs):
        ax.axvline(xs[marker_index], color=color, linewidth=1,
                   linestyle=(0, (4, 3)), alpha=0.55)
    ax.set_xlim(-0.4, len(xs) - 0.6)
    ax.set_ylim(floor - span * 0.1, hi + span * 0.2)
    figure.tight_layout()
    return figure


def draw_expense_bars(figure, labels, values, value_labels=None,
                      change_pct=None, colors=None, hatch_last=True):
    """Expense insight bars. The last bar uses a light hatched placeholder
    style; an optional circular badge shows the period change."""
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    if not values:
        _no_data(ax)
        return figure
    colors = colors or ["#063F44", "#2F7A80", "#B7CDCB"]
    ax.tick_params(left=False, labelleft=False)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#E8EBE9")
    n = len(values)
    max_v = max(values)
    for i, v in enumerate(values):
        color = colors[i] if i < len(colors) else colors[-1]
        hatch = "////" if (hatch_last and i == n - 1 and n >= 3) else None
        ax.bar(i, v, width=0.5, color=color,
               edgecolor="#063F44" if hatch else "none",
               linewidth=0.9, hatch=hatch)
        label = (value_labels[i] if value_labels else f"{v:,.0f}")
        ax.text(i, v + max_v * 0.03, label, ha="center", va="bottom",
                fontsize=8.5, color="#6B6F70")
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(0, max_v * 1.30)
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, fontsize=9, color="#6B6F70")
    if change_pct is not None and n >= 2:
        from matplotlib.patches import Circle
        good = change_pct <= 0
        cx, cy = 0.5, max_v * 0.62
        r = max_v * 0.10
        ax.add_patch(Circle((cx, cy), r,
                            facecolor="#E6F2EF" if good else "#FDEBEB",
                            edgecolor="none"))
        ax.text(cx, cy, f"{change_pct:+.0f}%", ha="center", va="center",
                fontsize=9.5, fontweight="bold",
                color="#16C784" if good else "#EF4444")
    figure.tight_layout()
    return figure


def draw_overview_donut(figure, segments, center_text, center_label):
    """Segmented ring with thick rounded arcs and gaps between segments.
    ``segments`` is a list of (value, color)."""
    figure.clear()
    ax = figure.add_subplot(111)
    _minimal(ax)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    total = sum(v for v, _ in segments)
    if total <= 0:
        ax.text(0, 0, "No data yet", ha="center", va="center", fontsize=11,
                color="#6B6F70")
        return figure
    start = 90.0
    gap = 3.0
    for value, color in segments:
        sweep = value / total * 360.0
        if sweep <= 0:
            continue
        draw = max(sweep - gap, 1.0)
        _arc_patch(ax, (0, 0), 0.88, start - draw, start, 0.30, color)
        start -= sweep
    _arc_patch(ax, (0, 0), 0.50, 0, 360, 0.02, "#063F44", alpha=0.45,
               dashes=(1, 3))
    ax.text(0, 0.10, center_text, ha="center", va="center", fontsize=18,
            fontweight="bold", color="#111111")
    ax.text(0, -0.14, center_label, ha="center", va="center", fontsize=9,
            color="#6B6F70")
    figure.tight_layout()
    return figure
