# -*- coding: utf-8 -*-
"""شاشة تقرير المعلم بمادته — تطبيق الجوال."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.metrics import dp

from core.optional_deps import plt, HAS_CHARTS

import theme
from widgets import ALabel, KPICard, Card, build_table, safe_chart_widget
from core.arabic_text import ar
from core.grade_colors import get_grade_color, grade_sort_key
from screens.home_screen import _fig_to_kivy_image


def build_teacher_report_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    if app.analysis is None:
        from screens.empty_screen import build_empty_screen
        root.add_widget(build_empty_screen())
        scroll.add_widget(root)
        return scroll

    analysis = app.analysis
    subjects = analysis.available_subjects()

    selector_card = Card(title="تقرير المعلم بمادته", subtitle="اختر المادة")
    spinner = Spinner(
        text=ar(subjects[0]) if subjects else "", values=[ar(s) for s in subjects],
        font_name=theme.FONT_REGULAR, size_hint_y=None, height=dp(44),
        background_color=theme.hex_to_rgba(theme.COLOR_CARD_BG),
        color=theme.hex_to_rgba(theme.COLOR_TEXT_PRIMARY),
    )
    selector_card.body.add_widget(spinner)
    root.add_widget(selector_card)

    content_holder = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
    content_holder.bind(minimum_height=content_holder.setter("height"))
    root.add_widget(content_holder)

    # تحويل عكسي من النص المُشكَّل بالـ Spinner للاسم الأصلي بقائمة subjects
    shaped_to_original = {ar(s): s for s in subjects}

    def render_subject(*_args):
        content_holder.clear_widgets()
        subj = shaped_to_original.get(spinner.text, subjects[0] if subjects else None)
        if not subj:
            return
        report = analysis.subject_report(subj)
        if report is None:
            content_holder.add_widget(ALabel(text="لا توجد بيانات لهذه المادة", font_size="12sp",
                                               size_hint_y=None, height=dp(30)))
            return
        _build_subject_content(content_holder, report)

    spinner.bind(text=render_subject)
    render_subject()

    scroll.add_widget(root)
    return scroll


def _build_subject_content(content_holder, report):
    kpi_row1 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(80), spacing=dp(8))
    kpi_row1.add_widget(KPICard(f"{report['overall_avg']}%", "المتوسط العام", palette="green"))
    kpi_row1.add_widget(KPICard(str(report["count"]), "عدد الطلاب", palette="blue"))
    content_holder.add_widget(kpi_row1)

    kpi_row2 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(80), spacing=dp(8))
    kpi_row2.add_widget(KPICard(f"{report['highest']}%", "أعلى درجة", palette="gold"))
    kpi_row2.add_widget(KPICard(f"{report['lowest']}%", "أدنى درجة", palette="red"))
    content_holder.add_widget(kpi_row2)

    chart_card = Card(title="متوسط المادة لكل فصل")
    img = safe_chart_widget(_build_class_chart, report)
    img.size_hint_y = None
    img.height = dp(200)
    chart_card.body.add_widget(img)
    content_holder.add_widget(chart_card)

    grade_card = Card(title="توزيع التقديرات بالمادة")
    donut = safe_chart_widget(_build_grade_chart, report)
    donut.size_hint_y = None
    donut.height = dp(220)
    grade_card.body.add_widget(donut)
    content_holder.add_widget(grade_card)

    weak_card = Card(title="أضعف 5 طلاب بهذه المادة")
    headers = ["التقدير", "الدرجة", "الفصل", "الاسم"]
    rows = [[r["grade_label"] or "-", f"{r['pct']}%", str(r["student"].get("class") or "-"),
             r["student"]["name_ar"]] for r in report["weakest"]]
    raw_grades = [r["grade_label"] for r in report["weakest"]]
    col_widths = [0.18, 0.16, 0.12, 0.54]
    table_scroll, container = build_table(headers, rows, col_widths=col_widths,
                                           grade_col_index=0, raw_grades=raw_grades)
    container.bind(minimum_height=lambda inst, val: setattr(table_scroll, "height", val))
    table_scroll.size_hint_y = None
    table_scroll.height = dp(38 * (len(rows) + 1))
    weak_card.body.add_widget(table_scroll)
    content_holder.add_widget(weak_card)


def _build_class_chart(report):
    fig, ax = plt.subplots(figsize=(5.6, 3.0), dpi=120)
    fig.patch.set_facecolor(theme.COLOR_CARD_BG)
    ax.set_facecolor(theme.COLOR_CARD_BG)
    classes_sorted = sorted(report["class_stats"].items(), key=lambda kv: str(kv[0]))
    labels = [ar(f"الفصل {cl}") for cl, _ in classes_sorted]
    values = [v["mean"] for _, v in classes_sorted]
    bars = ax.bar(labels, values, color=theme.COLOR_CHART_GREEN_LIGHT, width=0.5,
                   edgecolor=theme.COLOR_CHART_GREEN_DARK, linewidth=0.8)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2, ar(f"{val}%"), ha="center", fontsize=10)
    ax.set_ylim(0, 112)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _fig_to_kivy_image(fig, allow_stretch=True, keep_ratio=True)


def _build_grade_chart(report):
    fig, ax = plt.subplots(figsize=(4.2, 4.6), dpi=120)
    fig.patch.set_facecolor(theme.COLOR_CARD_BG)
    dist = report["grade_distribution"]
    sorted_items = sorted(dist.items(), key=lambda kv: grade_sort_key(kv[0]))
    labels = [k for k, _ in sorted_items]
    values = [v for _, v in sorted_items]
    colors_palette = [get_grade_color(l, "chart") for l in labels]
    wedges, _ = ax.pie(values, colors=colors_palette, startangle=90, wedgeprops=dict(width=0.38))
    ax.legend(wedges, [ar(f"{l} — {v}") for l, v in zip(labels, values)],
              loc="center", bbox_to_anchor=(0.5, -0.1), frameon=False, fontsize=10)
    fig.tight_layout()
    return _fig_to_kivy_image(fig, allow_stretch=True, keep_ratio=True)
