# -*- coding: utf-8 -*-
"""شاشة مقارنة الفصول — تطبيق الجوال."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import theme
from widgets import ALabel, Card, build_table, safe_chart_widget
from core.arabic_text import ar
from screens.home_screen import _fig_to_kivy_image

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def build_classes_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    if app.analysis is None:
        from screens.empty_screen import build_empty_screen
        root.add_widget(build_empty_screen())
        scroll.add_widget(root)
        return scroll

    analysis = app.analysis

    chart_card = Card(title="مقارنة متوسط المعدل بين الفصول")
    img = safe_chart_widget(_build_chart, analysis)
    img.size_hint_y = None
    img.height = dp(220)
    chart_card.body.add_widget(img)
    root.add_widget(chart_card)

    table_card = Card(title="تفاصيل كل فصل")
    classes_sorted = sorted(analysis.class_stats.items(), key=lambda kv: kv[1]["mean"], reverse=True)
    headers = ["عدد الطلاب", "أعلى معدل", "أدنى معدل", "المتوسط", "الفصل"]
    rows = []
    for cls, stats in classes_sorted:
        rows.append([str(stats["count"]), f"{stats['max']}%", f"{stats['min']}%",
                     f"{stats['mean']}%", f"الفصل {cls}"])
    col_widths = [0.16, 0.21, 0.21, 0.18, 0.24]
    table_scroll, container = build_table(headers, rows, col_widths=col_widths)
    container.bind(minimum_height=lambda inst, val: setattr(table_scroll, "height", val))
    table_scroll.size_hint_y = None
    table_card.body.add_widget(table_scroll)
    table_card.body.bind(minimum_height=lambda inst, val: None)
    root.add_widget(table_card)

    scroll.add_widget(root)
    return scroll


def _build_chart(analysis):
    classes_sorted = sorted(analysis.class_stats.items(), key=lambda kv: str(kv[0]))
    labels = [ar(f"الفصل {cl}") for cl, _ in classes_sorted]
    means = [v["mean"] for _, v in classes_sorted]
    mins = [v["min"] for _, v in classes_sorted]
    maxs = [v["max"] for _, v in classes_sorted]

    fig, ax = plt.subplots(figsize=(5.6, 3.6), dpi=120)
    fig.patch.set_facecolor(theme.COLOR_CARD_BG)
    ax.set_facecolor(theme.COLOR_CARD_BG)
    x = range(len(labels))
    bars = ax.bar(x, means, color=theme.COLOR_CHART_GREEN_LIGHT, width=0.45,
                   edgecolor=theme.COLOR_CHART_GREEN_DARK, label=ar("المتوسط"))
    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2.5, ar(f"{val}%"), ha="center", fontsize=10)
    ax.scatter(x, maxs, color=theme.COLOR_GOLD_FG, zorder=5, label=ar("أعلى معدل"), s=45)
    ax.scatter(x, mins, color=theme.COLOR_RED_FG, zorder=5, label=ar("أدنى معدل"), s=45)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 122)
    ax.legend(fontsize=9, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _fig_to_kivy_image(fig, allow_stretch=True, keep_ratio=True)
