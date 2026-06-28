# -*- coding: utf-8 -*-
"""مُنشئ شهادات التكريم — تصميم رسمي أفقي (Landscape) جاهز للطباعة."""
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas

from core.pdf_engine import (
    ar, ensure_fonts_registered, FONT_REGULAR, FONT_BOLD,
    FONT_NASKH_REGULAR, FONT_NASKH_BOLD,
)
from reportlab.pdfbase import pdfmetrics

CERT_W, CERT_H = landscape(A4)


def _naskh_or_fallback_regular():
    return FONT_NASKH_REGULAR if FONT_NASKH_REGULAR in pdfmetrics.getRegisteredFontNames() else FONT_REGULAR


def _naskh_or_fallback_bold():
    return FONT_NASKH_BOLD if FONT_NASKH_BOLD in pdfmetrics.getRegisteredFontNames() else FONT_BOLD


def draw_certificate(c, ctx, student_name, rank_text, subtitle_text, accent_hex="#1E9E6B"):
    """
    يرسم شهادة تكريم واحدة (صفحة أفقية كاملة) على الكانفاس الممرر.
    rank_text: مثل "المركز الأول" أو "الأول على الفصل".
    subtitle_text: مثل "الصف الثالث المتوسط — الفصل 1".
    """
    accent = colors.HexColor(accent_hex)
    naskh_regular = _naskh_or_fallback_regular()
    naskh_bold = _naskh_or_fallback_bold()

    # خلفية فاتحة
    c.setFillColor(colors.HexColor("#FCFCFA"))
    c.rect(0, 0, CERT_W, CERT_H, fill=1, stroke=0)

    # إطار خارجي مزدوج
    margin = 10 * mm
    c.setStrokeColor(accent)
    c.setLineWidth(2.2)
    c.rect(margin, margin, CERT_W - 2 * margin, CERT_H - 2 * margin, fill=0, stroke=1)
    inner_margin = margin + 4 * mm
    c.setLineWidth(0.7)
    c.rect(inner_margin, inner_margin, CERT_W - 2 * inner_margin, CERT_H - 2 * inner_margin, fill=0, stroke=1)

    # زخرفة زوايا بسيطة (دوائر صغيرة بكل زاوية)
    corner_offset = margin + 2 * mm
    for cx, cy in [(corner_offset, corner_offset), (CERT_W - corner_offset, corner_offset),
                   (corner_offset, CERT_H - corner_offset), (CERT_W - corner_offset, CERT_H - corner_offset)]:
        c.setFillColor(accent)
        c.circle(cx, cy, 2.2 * mm, fill=1, stroke=0)

    # الشعار
    y = CERT_H - 30 * mm
    if ctx.logo_path and os.path.exists(ctx.logo_path):
        try:
            logo_h = 20 * mm
            logo_w = logo_h * 1.3
            c.drawImage(ctx.logo_path, (CERT_W - logo_w) / 2, y - logo_h + 6 * mm,
                        width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
            y -= (logo_h - 2 * mm)
        except Exception:
            pass

    y -= 8 * mm
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(colors.HexColor("#5C6773"))
    c.drawCentredString(CERT_W / 2, y, ar("المملكة العربية السعودية"))
    y -= 6 * mm
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(colors.HexColor("#16213A"))
    c.drawCentredString(CERT_W / 2, y, ar(ctx.school_name or ""))

    # عنوان الشهادة
    y -= 18 * mm
    c.setFont(naskh_bold, 30)
    c.setFillColor(accent)
    c.drawCentredString(CERT_W / 2, y, ar("شهادة تقدير وتكريم"))

    # نص تمهيدي
    y -= 14 * mm
    c.setFont(FONT_REGULAR, 13)
    c.setFillColor(colors.HexColor("#3A4250"))
    c.drawCentredString(CERT_W / 2, y, ar("تتقدم متوسطة"))

    # اسم الطالب (الأبرز بالشهادة)
    y -= 16 * mm
    c.setFont(naskh_bold, 26)
    c.setFillColor(colors.HexColor("#16213A"))
    c.drawCentredString(CERT_W / 2, y, ar(student_name))

    # نص الإنجاز
    y -= 14 * mm
    c.setFont(FONT_REGULAR, 13)
    c.setFillColor(colors.HexColor("#3A4250"))
    achievement_line = f"تقديرًا لتميّزه وحصوله على {rank_text}"
    c.drawCentredString(CERT_W / 2, y, ar(achievement_line))

    y -= 8 * mm
    c.setFont(FONT_BOLD, 12)
    c.setFillColor(accent)
    c.drawCentredString(CERT_W / 2, y, ar(subtitle_text))

    # تذييل: التاريخ + التوقيعات
    sig_y = margin + 22 * mm
    c.setFont(FONT_REGULAR, 10)
    c.setFillColor(colors.HexColor("#6B7785"))

    sig_w = (CERT_W - 2 * inner_margin) / 2
    left_x = inner_margin + sig_w / 2
    right_x = CERT_W - inner_margin - sig_w / 2

    c.line(right_x - 28 * mm, sig_y, right_x + 28 * mm, sig_y)
    c.drawCentredString(right_x, sig_y - 6 * mm, ar("مدير المدرسة"))
    if ctx.principal_name:
        c.setFont(FONT_BOLD, 10)
        c.setFillColor(colors.HexColor("#16213A"))
        c.drawCentredString(right_x, sig_y + 2 * mm, ar(ctx.principal_name))

    c.setFont(FONT_REGULAR, 10)
    c.setFillColor(colors.HexColor("#6B7785"))
    c.line(left_x - 28 * mm, sig_y, left_x + 28 * mm, sig_y)
    c.drawCentredString(left_x, sig_y - 6 * mm, ar("رائد النشاط"))
    if ctx.prepared_by_name:
        c.setFont(FONT_BOLD, 10)
        c.setFillColor(colors.HexColor("#16213A"))
        c.drawCentredString(left_x, sig_y + 2 * mm, ar(ctx.prepared_by_name))

    import datetime
    c.setFont(FONT_REGULAR, 9)
    c.setFillColor(colors.HexColor("#9AA5BD"))
    c.drawCentredString(CERT_W / 2, margin + 6 * mm, datetime.date.today().strftime("%Y/%m/%d"))


def export_top_students_certificates(out_path, ctx, analysis, top_n=3, scope="class"):
    """
    يصدّر ملف PDF فيه شهادة لكل طالب من أعلى top_n طلاب.
    scope='class': أعلى top_n لكل فصل على حدة.
    scope='grade': أعلى top_n على مستوى الصف كامل (كل الفصول).
    """
    ensure_fonts_registered()
    c = rl_canvas.Canvas(out_path, pagesize=landscape(A4))

    rank_labels_ar = ["المركز الأول", "المركز الثاني", "المركز الثالث",
                      "المركز الرابع", "المركز الخامس"]

    def rank_label(idx):
        if idx < len(rank_labels_ar):
            return rank_labels_ar[idx]
        return f"المركز {idx + 1}"

    first = True
    if scope == "grade":
        top_students = sorted(analysis.students, key=lambda s: s["average"], reverse=True)[:top_n]
        for i, s in enumerate(top_students):
            if not first:
                c.showPage()
            first = False
            subtitle = ctx.grade_title or ""
            draw_certificate(c, ctx, s["name_ar"], rank_label(i), subtitle)
    else:
        classes_sorted = sorted(analysis.class_stats.keys(), key=str)
        for cls in classes_sorted:
            class_students = [s for s in analysis.students if s.get("class") == cls]
            top_students = sorted(class_students, key=lambda s: s["average"], reverse=True)[:top_n]
            for i, s in enumerate(top_students):
                if not first:
                    c.showPage()
                first = False
                subtitle = f"{ctx.grade_title or ''} — الفصل {cls}".strip(" —")
                draw_certificate(c, ctx, s["name_ar"], rank_label(i), subtitle)

    c.save()
    return out_path
