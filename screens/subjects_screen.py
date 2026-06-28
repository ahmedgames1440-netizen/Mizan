# -*- coding: utf-8 -*-
"""شاشة تحليل المواد — تطبيق الجوال."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import theme
from widgets import Card, safe_chart_widget
from core.arabic_text import ar
from screens.home_screen import _fig_to_kivy_image

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def build_subjects_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    if app.analysis is None:
        from screens.empty_screen import build_empty_screen
        root.add_widget(build_empty_screen())
        scroll.add_widget(root)
        return scroll

    analysis = app.analysis
    subj_avg = analysis.subject_averages_academic_only

    card = Card(title="متوسط أداء الطلاب في كل مادة", subtitle="الأخضر الأعلى، الأحمر يحتاج تعزيز")
    if subj_avg:
        img = safe_chart_widget(_build_chart, subj_avg)
        img.size_hint_y = None
        img.height = dp(max(280, 32 * len(subj_avg)))
        card.body.add_widget(img)
    root.add_widget(card)

    scroll.add_widget(root)
    return scroll


def _build_chart(subj_avg):
    items = sorted(subj_avg.items(), key=lambda kv: kv[1])
    labels = [ar(k) for k, _ in items]
    values = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(5.6, max(3.5, 0.5 * len(items))), dpi=120)
    fig.patch.set_facecolor(theme.COLOR_CARD_BG)
    ax.set_facecolor(theme.COLOR_CARD_BG)

    colors = []
    for v in values:
        if v < 65:
            colors.append(theme.COLOR_RED_FG)
        elif v < 80:
            colors.append(theme.COLOR_GOLD_FG)
        else:
            colors.append(theme.COLOR_CHART_GREEN_LIGHT)

    bars = ax.barh(range(len(labels)), values, color=colors, height=0.55)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    for bar, val in zip(bars, values):
        ax.text(val + 2, bar.get_y() + bar.get_height() / 2, ar(f"{val}%"), va="center", fontsize=9)
    ax.set_xlim(0, 115)
    ax.invert_yaxis()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    return _fig_to_kivy_image(fig, allow_stretch=True, keep_ratio=True)
