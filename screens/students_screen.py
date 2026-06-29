# -*- coding: utf-8 -*-
"""شاشة بيانات الطلاب — تطبيق الجوال."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from widgets import ALabel, AButton, Card, build_table
from core.arabic_text import ar
import theme


def build_students_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    if app.analysis is None:
        from screens.empty_screen import build_empty_screen
        root.add_widget(build_empty_screen())
        scroll.add_widget(root)
        return scroll

    analysis = app.analysis
    card = Card(title="بيانات جميع الطلاب", subtitle=f"{analysis.count} طالب")

    headers = ["التقدير", "المعدل", "الفصل", "الاسم"]
    table_rows = analysis.student_table_rows()
    rows = []
    for row in table_rows:
        rows.append([row["التقدير"] or "-", f"{row['المعدل']}%",
                     str(row["الفصل"] or "-"), row["الاسم"]])
    raw_grades = [row["التقدير"] for row in table_rows]
    col_widths = [0.18, 0.16, 0.12, 0.40, 0.14]

    def _on_row_action(idx):
        row = table_rows[idx]
        student = analysis.find_student(row["الاسم"], row["الفصل"])
        if student:
            _export_student_report(app, student)

    table_scroll, container = build_table(
        headers, rows, col_widths=col_widths, grade_col_index=0, raw_grades=raw_grades,
        row_action_label="تقرير", row_action_callback=_on_row_action,
    )
    container.bind(minimum_height=lambda inst, val: setattr(table_scroll, "height", val))
    table_scroll.size_hint_y = None
    table_scroll.height = dp(38 * (len(rows) + 1))
    card.body.add_widget(table_scroll)
    root.add_widget(card)

    scroll.add_widget(root)
    return scroll


def _export_student_report(app, student):
    """يصدّر تقرير PDF لطالب واحد ويحفظه بمجلد بيانات التطبيق (قابل للمشاركة)."""
    import os
    from core.optional_deps import HAS_PDF, UNAVAILABLE_PDF_MESSAGE
    if not HAS_PDF:
        _show_success(UNAVAILABLE_PDF_MESSAGE)
        return
    from core.pdf_engine import ReportContext
    from core.pdf_report import export_single_student_report
    from core.school_settings import load_school_settings

    settings = load_school_settings()
    ctx = ReportContext(
        school_name=settings.get("school_name", ""),
        principal_name=settings.get("principal_name", ""),
        logo_path=settings.get("logo_path") or None,
    )

    try:
        out_dir = app.user_data_dir
    except Exception:
        out_dir = os.path.expanduser("~")
    safe_name = student["name_ar"].replace(" ", "_")
    out_path = os.path.join(out_dir, f"تقرير_{safe_name}.pdf")

    try:
        export_single_student_report(out_path, ctx, app.analysis, student)
        _show_success(f"تم حفظ التقرير:\n{out_path}")
    except Exception as e:
        _show_success(f"تعذّر إنشاء التقرير:\n{e}")


def _show_success(message):
    from kivy.uix.popup import Popup
    popup = Popup(title=ar("النتيجة"), content=ALabel(text=message, font_size="12sp"),
                   size_hint=(0.85, 0.35))
    popup.open()
