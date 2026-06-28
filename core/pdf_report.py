# -*- coding: utf-8 -*-
"""بناء تقرير PDF كامل أو لقسم واحد، بما في ذلك صفحة الغلاف."""
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4

from core.pdf_engine import ensure_fonts_registered, draw_cover_page
from core.pdf_sections import (
    render_dashboard_section, render_classes_section, render_subjects_section,
    render_watchlist_section, render_students_section, render_single_student_page,
    render_anomalies_section, render_teacher_subject_report,
)

SECTION_RENDERERS = {
    "home": render_dashboard_section,
    "classes": render_classes_section,
    "subjects": render_subjects_section,
    "watchlist": render_watchlist_section,
    "anomalies": render_anomalies_section,
    "students": render_students_section,
}

SECTION_TITLES = {
    "home": "لوحة التحكم",
    "classes": "مقارنة الفصول",
    "subjects": "تحليل المواد",
    "watchlist": "طلاب يحتاجون دعم",
    "anomalies": "حالات شاذة",
    "students": "بيانات الطلاب",
}


def export_full_report(out_path, ctx, analysis, include_cover=True):
    """يصدّر تقريرًا شاملًا بكل الأقسام، بدءًا بصفحة الغلاف."""
    ensure_fonts_registered()
    c = rl_canvas.Canvas(out_path, pagesize=A4)

    if include_cover:
        draw_cover_page(c, ctx)

    page_num_holder = [1]
    order = ["home", "classes", "subjects", "watchlist", "anomalies", "students"]
    for i, key in enumerate(order):
        renderer = SECTION_RENDERERS[key]
        renderer(c, ctx, analysis, page_num_holder, first_page=(i == 0))

    c.save()
    return out_path


def export_single_section(out_path, ctx, analysis, section_key, include_cover=True):
    """يصدّر قسمًا واحدًا فقط (مع أو بدون غلاف)."""
    ensure_fonts_registered()
    c = rl_canvas.Canvas(out_path, pagesize=A4)

    if include_cover:
        draw_cover_page(c, ctx)

    renderer = SECTION_RENDERERS.get(section_key)
    if renderer is None:
        raise ValueError(f"Unknown section: {section_key}")

    page_num_holder = [1]
    renderer(c, ctx, analysis, page_num_holder, first_page=True)

    c.save()
    return out_path


def export_single_student_report(out_path, ctx, analysis, student, include_cover=False):
    """يصدّر تقرير طالب واحد (صفحة واحدة)، بدون غلاف افتراضيًا (مناسب للطباعة المباشرة لولي الأمر)."""
    ensure_fonts_registered()
    c = rl_canvas.Canvas(out_path, pagesize=A4)

    if include_cover:
        draw_cover_page(c, ctx)

    page_num_holder = [1]
    render_single_student_page(c, ctx, analysis, student, page_num_holder, first_page=True)

    c.save()
    return out_path


def export_all_students_reports(out_path, ctx, analysis, include_cover=True, progress_cb=None):
    """
    يصدّر ملف PDF واحد فيه صفحة مستقلة لكل طالب (مرتبين حسب المعدل تنازليًا).
    progress_cb(done, total) اختياري لعرض شريط تقدم بالواجهة.
    """
    ensure_fonts_registered()
    c = rl_canvas.Canvas(out_path, pagesize=A4)

    if include_cover:
        draw_cover_page(c, ctx)

    page_num_holder = [1]
    students_sorted = sorted(analysis.students, key=lambda s: s["average"], reverse=True)
    total = len(students_sorted)

    for i, student in enumerate(students_sorted):
        render_single_student_page(
            c, ctx, analysis, student, page_num_holder,
            first_page=(i == 0)
        )
        if progress_cb:
            progress_cb(i + 1, total)

    c.save()
    return out_path


def export_teacher_subject_report(out_path, ctx, analysis, subject_name, include_cover=True):
    """يصدّر تقرير مادة دراسية واحدة (مخصص للمعلم)."""
    ensure_fonts_registered()
    c = rl_canvas.Canvas(out_path, pagesize=A4)

    if include_cover:
        draw_cover_page(c, ctx)

    page_num_holder = [1]
    render_teacher_subject_report(c, ctx, analysis, subject_name, page_num_holder, first_page=True)

    c.save()
    return out_path
