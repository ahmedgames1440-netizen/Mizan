# -*- coding: utf-8 -*-
"""شاشة طلاب يحتاجون دعم — تطبيق الجوال."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from widgets import ALabel, Card, build_table
from core.arabic_text import ar
import theme


def build_watchlist_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    if app.analysis is None:
        from screens.empty_screen import build_empty_screen
        root.add_widget(build_empty_screen())
        scroll.add_widget(root)
        return scroll

    analysis = app.analysis

    if analysis.at_risk:
        risk_card = Card(title=f"طلاب تحت خط الخطر ({analysis.risk_threshold}%)",
                          subtitle=f"{len(analysis.at_risk)} طالب")
        headers = ["التقدير", "المعدل", "الفصل", "الاسم"]
        rows = [[s.get("general_grade") or "-", f"{s['average']}%",
                 str(s.get("class") or "-"), s["name_ar"]] for s in analysis.at_risk]
        raw_grades = [s.get("general_grade") for s in analysis.at_risk]
        col_widths = [0.18, 0.16, 0.12, 0.54]
        table_scroll, container = _bound_table(headers, rows, col_widths, grade_col_index=0, raw_grades=raw_grades)
        risk_card.body.add_widget(table_scroll)
        root.add_widget(risk_card)
    else:
        notice = Card()
        notice.body.add_widget(ALabel(
            text=f"✓ لا يوجد طالب تحت خط الخطر ({analysis.risk_threshold}%) — أداء الصف مطمئن",
            font_size="13sp", bold=True, color=theme.hex_to_rgba(theme.COLOR_GREEN_FG),
            size_hint_y=None, height=dp(50)))
        root.add_widget(notice)

    watch_card = Card(title="قائمة متابعة وقائية", subtitle="أدنى 15 معدلاً")
    headers = ["الغياب", "التقدير", "المعدل", "الفصل", "الاسم"]
    rows = [[str(s.get("absence") or 0), s.get("general_grade") or "-", f"{s['average']}%",
             str(s.get("class") or "-"), s["name_ar"]] for s in analysis.watch_list]
    raw_grades = [s.get("general_grade") for s in analysis.watch_list]
    col_widths = [0.12, 0.18, 0.16, 0.12, 0.42]
    table_scroll, container = _bound_table(headers, rows, col_widths, grade_col_index=1, raw_grades=raw_grades)
    watch_card.body.add_widget(table_scroll)
    root.add_widget(watch_card)

    scroll.add_widget(root)
    return scroll


def _bound_table(headers, rows, col_widths, **kwargs):
    table_scroll, container = build_table(headers, rows, col_widths=col_widths, **kwargs)
    container.bind(minimum_height=lambda inst, val: setattr(table_scroll, "height", val))
    table_scroll.size_hint_y = None
    table_scroll.height = dp(min(400, 38 * (len(rows) + 1)))
    return table_scroll, container
