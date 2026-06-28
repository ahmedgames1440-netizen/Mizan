# -*- coding: utf-8 -*-
"""شاشة مقارنة فصلين دراسيين — تطبيق الجوال."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import theme
from widgets import ALabel, AButton, KPICard, Card, build_table, safe_chart_widget
from core.arabic_text import ar
from core.comparison import ComparisonResult
from core.parser import parse_grades_file, FORMAT_UNKNOWN
from core.analysis import AnalysisResult
from screens.home_screen import _fig_to_kivy_image

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def build_comparison_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    if app.analysis is None:
        from screens.empty_screen import build_empty_screen
        root.add_widget(build_empty_screen())
        scroll.add_widget(root)
        return scroll

    if app.comparison is None:
        root.add_widget(_build_upload_prompt(app))
        scroll.add_widget(root)
        return scroll

    _build_comparison_content(root, app)
    scroll.add_widget(root)
    return scroll


def _build_upload_prompt(app):
    box = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, height=dp(320))
    box.add_widget(ALabel(text="▤ ↔ ▤", font_size="30sp", halign="center",
                           size_hint_y=None, height=dp(50), font_name="Roboto"))
    box.add_widget(ALabel(text="قارن أداء الطلاب بين فصلين دراسيين", font_size="15sp", bold=True,
                           halign="center", size_hint_y=None, height=dp(30)))
    current_name = ""
    if app.current_filepath:
        import os
        current_name = os.path.basename(app.current_filepath)
    box.add_widget(ALabel(
        text=f"الملف الحالي ({current_name}) سيُعتبر الفترة الأولى. ارفع ملف نتائج آخر للمقارنة.",
        font_size="11sp", color=theme.hex_to_rgba(theme.COLOR_TEXT_SECONDARY),
        halign="center", size_hint_y=None, height=dp(60)))

    btn = AButton(text="رفع ملف الفترة الثانية  ⛁", size_hint_y=None, height=dp(46),
                  background_color=theme.hex_to_rgba(theme.COLOR_ACCENT),
                  color=theme.hex_to_rgba("#FFFFFF"))
    btn.bind(on_release=lambda *a: _pick_comparison_file(app))
    box.add_widget(btn)
    return box


def _pick_comparison_file(app):
    try:
        from plyer import filechooser

        def _on_selection(selection):
            if selection:
                _process_comparison_file(app, selection[0])

        filechooser.open_file(on_selection=_on_selection, filters=[("Excel files", "*.xlsx", "*.xls")])
    except Exception:
        import os
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.popup import Popup

        chooser = FileChooserListView(filters=["*.xlsx", "*.xls"], path=os.path.expanduser("~"))
        popup = Popup(title=ar("اختر ملف الفترة الثانية"), content=chooser, size_hint=(0.9, 0.9))

        def _on_submit(instance, selection, touch):
            if selection:
                popup.dismiss()
                _process_comparison_file(app, selection[0])

        chooser.bind(on_submit=_on_submit)
        popup.open()


def _process_comparison_file(app, filepath):
    try:
        students, fmt = parse_grades_file(filepath)
    except Exception:
        return
    if fmt == FORMAT_UNKNOWN or not students:
        return
    analysis_after = AnalysisResult(students, risk_threshold=65.0)
    app.comparison = ComparisonResult(app.analysis, analysis_after)
    app.switch_screen("comparison")


def _build_comparison_content(root, app):
    comparison = app.comparison

    change_btn = AButton(text="تغيير ملف المقارنة", size_hint_y=None, height=dp(40),
                          background_color=theme.hex_to_rgba(theme.COLOR_CARD_BG),
                          color=theme.hex_to_rgba(theme.COLOR_TEXT_PRIMARY))
    change_btn.bind(on_release=lambda *a: _pick_comparison_file(app))
    root.add_widget(change_btn)

    kpi_row1 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(80), spacing=dp(8))
    diff_sign = "+" if comparison.overall_diff >= 0 else ""
    kpi_row1.add_widget(KPICard(f"{diff_sign}{comparison.overall_diff}", "التغيّر بالمتوسط",
                                  palette="green" if comparison.overall_diff >= 0 else "red"))
    kpi_row1.add_widget(KPICard(str(comparison.matched_count), "طالب تمت مطابقته", palette="blue"))
    root.add_widget(kpi_row1)

    kpi_row2 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(80), spacing=dp(8))
    kpi_row2.add_widget(KPICard(str(len(comparison.improved)), "تحسّن أداءه", palette="green"))
    kpi_row2.add_widget(KPICard(str(len(comparison.declined)), "تراجع أداءه", palette="red"))
    root.add_widget(kpi_row2)

    chart_card = Card(title="مقارنة متوسط كل فصل بين الفترتين")
    img = safe_chart_widget(_build_class_comparison_chart, comparison)
    img.size_hint_y = None
    img.height = dp(220)
    chart_card.body.add_widget(img)
    root.add_widget(chart_card)

    improved_card = Card(title="الأكثر تحسّنًا", subtitle="أعلى 10")
    _add_diff_table(improved_card.body, comparison.most_improved)
    root.add_widget(improved_card)

    declined_card = Card(title="الأكثر تراجعًا", subtitle="أعلى 10")
    _add_diff_table(declined_card.body, comparison.most_declined)
    root.add_widget(declined_card)


def _add_diff_table(body, rows_data):
    headers = ["الفرق", "بعد", "قبل", "الفصل", "الاسم"]
    rows = []
    for m in rows_data:
        diff_text = f"{'+' if m['diff'] >= 0 else ''}{m['diff']}"
        rows.append([diff_text, f"{m['avg_after']}%", f"{m['avg_before']}%",
                     str(m.get("class_after") or m.get("class_before") or "-"), m["name_ar"]])
    col_widths = [0.14, 0.16, 0.16, 0.12, 0.42]
    table_scroll, container = build_table(headers, rows, col_widths=col_widths)
    container.bind(minimum_height=lambda inst, val: setattr(table_scroll, "height", val))
    table_scroll.size_hint_y = None
    table_scroll.height = dp(38 * (len(rows) + 1))
    body.add_widget(table_scroll)


def _build_class_comparison_chart(comparison):
    fig, ax = plt.subplots(figsize=(5.6, 3.2), dpi=120)
    fig.patch.set_facecolor(theme.COLOR_CARD_BG)
    ax.set_facecolor(theme.COLOR_CARD_BG)

    classes_sorted = sorted(comparison.class_comparison.items(), key=lambda kv: str(kv[0]))
    labels = [ar(f"الفصل {cl}") for cl, _ in classes_sorted]
    before_vals = [v["before"] or 0 for _, v in classes_sorted]
    after_vals = [v["after"] or 0 for _, v in classes_sorted]

    x = range(len(labels))
    width = 0.32
    ax.bar([p - width / 2 for p in x], before_vals, width=width,
           color=theme.COLOR_CHART_GRAY_LIGHT, edgecolor=theme.COLOR_CHART_GREEN_DARK,
           label=ar(comparison.label_before))
    ax.bar([p + width / 2 for p in x], after_vals, width=width,
           color=theme.COLOR_CHART_GREEN_LIGHT, edgecolor=theme.COLOR_CHART_GREEN_DARK,
           label=ar(comparison.label_after))
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=9, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.18), ncol=2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _fig_to_kivy_image(fig, allow_stretch=True, keep_ratio=True)
