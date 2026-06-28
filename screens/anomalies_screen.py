# -*- coding: utf-8 -*-
"""شاشة كشف الحالات الشاذة — تطبيق الجوال."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from widgets import ALabel, Card, build_table
import theme


def build_anomalies_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    if app.analysis is None:
        from screens.empty_screen import build_empty_screen
        root.add_widget(build_empty_screen())
        scroll.add_widget(root)
        return scroll

    analysis = app.analysis

    intro = Card()
    intro.body.add_widget(ALabel(
        text="طلاب بتفاوت كبير وغير متوقع بمادة معينة مقارنة بمتوسط أدائهم "
             "الشخصي بباقي المواد — قد يشير ذلك لخطأ بإدخال الدرجة أو فجوة "
             "تعليمية محددة تحتاج متابعة.",
        font_size="11sp", color=theme.hex_to_rgba(theme.COLOR_TEXT_SECONDARY),
        size_hint_y=None, height=dp(70),
    ))
    root.add_widget(intro)

    anomalies = analysis.anomalies[:20]

    if not anomalies:
        notice = Card()
        notice.body.add_widget(ALabel(
            text="✓ لم يتم رصد أي حالات شاذة لافتة",
            font_size="13sp", bold=True, color=theme.hex_to_rgba(theme.COLOR_GREEN_FG),
            size_hint_y=None, height=dp(40)))
        root.add_widget(notice)
        scroll.add_widget(root)
        return scroll

    card = Card(title="الحالات الأبرز", subtitle=f"{len(analysis.anomalies)} حالة — أعلى {len(anomalies)} معروضة")
    headers = ["الاتجاه", "الفرق", "متوسطه", "درجته", "المادة", "الاسم"]
    rows = []
    for a in anomalies:
        s = a["student"]
        direction_text = "ضعف لافت" if a["direction"] == "drop" else "تميّز لافت"
        rows.append([direction_text, f"{a['gap']:+.1f}", f"{a['personal_avg']}%",
                     f"{a['subject_pct']}%", a["subject"], s["name_ar"]])

    col_widths = [0.16, 0.12, 0.12, 0.12, 0.22, 0.26]
    table_scroll, container = build_table(headers, rows, col_widths=col_widths)
    container.bind(minimum_height=lambda inst, val: setattr(table_scroll, "height", val))
    table_scroll.size_hint_y = None
    table_scroll.height = dp(min(450, 50 * (len(rows) + 1)))
    card.body.add_widget(table_scroll)
    root.add_widget(card)

    scroll.add_widget(root)
    return scroll
