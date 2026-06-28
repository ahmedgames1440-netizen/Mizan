# -*- coding: utf-8 -*-
"""
محرك بناء تقارير PDF لبرنامج ميزان.
يستخدم reportlab + إعادة تشكيل عربي يدوي (مطلوب على كل الأنظمة لأن PDF
لا يعتمد على محرك تشكيل النظام كما يفعل Tkinter على Windows).
"""
import os
import sys
import datetime

import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

_reshaper = arabic_reshaper.ArabicReshaper({
    "delete_harakat": True,
    "support_ligatures": True,
})

_FONTS_REGISTERED = False
FONT_REGULAR = "NotoArabic"
FONT_BOLD = "NotoArabicBold"
FONT_NASKH_REGULAR = "NotoNaskhArabic"
FONT_NASKH_BOLD = "NotoNaskhArabicBold"


def _resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def ensure_fonts_registered():
    """يسجّل خطوط Noto Sans/Naskh Arabic المرفقة مع reportlab (مرة واحدة لكل تشغيل)."""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    fonts_dir = _resource_path(os.path.join("assets", "fonts"))
    regular_path = os.path.join(fonts_dir, "NotoSansArabic-Regular.ttf")
    bold_path = os.path.join(fonts_dir, "NotoSansArabic-Bold.ttf")
    naskh_regular_path = os.path.join(fonts_dir, "NotoNaskhArabic-Regular.ttf")
    naskh_bold_path = os.path.join(fonts_dir, "NotoNaskhArabic-Bold.ttf")
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, regular_path))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, bold_path))
    if os.path.exists(naskh_regular_path):
        pdfmetrics.registerFont(TTFont(FONT_NASKH_REGULAR, naskh_regular_path))
    if os.path.exists(naskh_bold_path):
        pdfmetrics.registerFont(TTFont(FONT_NASKH_BOLD, naskh_bold_path))
    _FONTS_REGISTERED = True


def ar(text):
    """يحوّل نص عربي/مختلط إلى شكل متصل وبترتيب عرض صحيح لاستخدامه في PDF."""
    if text is None:
        return ""
    text = str(text)
    try:
        reshaped = _reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def hex_to_color(hex_str):
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return colors.Color(r, g, b)


class ReportContext:
    """بيانات التقرير التي يدخلها المستخدم قبل التصدير (تُسأل كل مرة)."""
    def __init__(self, school_name="", grade_title="", semester="", academic_year="",
                 prepared_by_role="رائد النشاط", prepared_by_name="",
                 principal_name="", logo_path=None):
        self.school_name = school_name
        self.grade_title = grade_title
        self.semester = semester
        self.academic_year = academic_year
        self.prepared_by_role = prepared_by_role
        self.prepared_by_name = prepared_by_name
        self.principal_name = principal_name
        self.logo_path = logo_path


def draw_page_header(c, ctx, page_title=""):
    """يرسم ترويسة موحّدة (شعار صغير + اسم المدرسة) وخط تسطير علوي في كل صفحة."""
    c.saveState()
    y_top = PAGE_H - 12 * mm

    if ctx.logo_path and os.path.exists(ctx.logo_path):
        try:
            logo_h = 9 * mm
            logo_w = logo_h * 1.3
            c.drawImage(ctx.logo_path, MARGIN, y_top - logo_h + 3 * mm,
                        width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
        except Exception:
            pass

    c.setFont(FONT_BOLD, 10)
    c.setFillColor(colors.HexColor("#16213A"))
    c.drawRightString(PAGE_W - MARGIN, y_top, ar(ctx.school_name or "ميزان — تحليل نتائج الطلاب"))
    if page_title:
        c.setFont(FONT_REGULAR, 8.5)
        c.setFillColor(colors.HexColor("#6B7785"))
        c.drawRightString(PAGE_W - MARGIN, y_top - 5 * mm, ar(page_title))

    # خط تسطير الصفحة (تحت الترويسة)
    c.setStrokeColor(colors.HexColor("#2E6DA4"))
    c.setLineWidth(1.1)
    c.line(MARGIN, PAGE_H - 20 * mm, PAGE_W - MARGIN, PAGE_H - 20 * mm)
    c.restoreState()


def draw_page_footer(c, ctx, page_num, total_pages=None):
    """يرسم تذييلًا بخط تسطير وترقيم صفحات."""
    c.saveState()
    y = 12 * mm
    c.setStrokeColor(colors.HexColor("#D8DEE5"))
    c.setLineWidth(0.8)
    c.line(MARGIN, y + 5 * mm, PAGE_W - MARGIN, y + 5 * mm)

    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(colors.HexColor("#9aa3ad"))
    c.drawCentredString(PAGE_W / 2, y, ar("تم إنشاء هذا التقرير عبر برنامج ميزان لتحليل نتائج الطلاب"))

    page_text = f"{page_num}" if total_pages is None else f"{page_num} / {total_pages}"
    c.drawString(MARGIN, y, page_text)

    date_str = datetime.date.today().strftime("%Y/%m/%d")
    c.drawRightString(PAGE_W - MARGIN, y, date_str)
    c.restoreState()


def draw_cover_page(c, ctx):
    """يرسم صفحة الغلاف الرسمية كأول صفحة بالتقرير."""
    c.saveState()

    # شريط علوي متدرج (نحاكيه بخط عريض بسيط لأن reportlab الأساسي لا يدعم تدرج سهل)
    c.setFillColor(colors.HexColor("#2E6DA4"))
    c.rect(MARGIN, PAGE_H - 26 * mm, (PAGE_W - 2 * MARGIN) * 0.55, 2.2 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#3FA66B"))
    c.rect(MARGIN + (PAGE_W - 2 * MARGIN) * 0.55, PAGE_H - 26 * mm,
           (PAGE_W - 2 * MARGIN) * 0.45, 2.2 * mm, fill=1, stroke=0)

    # الشعار
    logo_drawn = False
    if ctx.logo_path and os.path.exists(ctx.logo_path):
        try:
            logo_h = 32 * mm
            logo_w = logo_h * 1.3
            c.drawImage(ctx.logo_path, (PAGE_W - logo_w) / 2, PAGE_H - 70 * mm,
                        width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
            logo_drawn = True
        except Exception:
            pass

    y = PAGE_H - 78 * mm if logo_drawn else PAGE_H - 50 * mm

    c.setFont(FONT_BOLD, 11)
    c.setFillColor(colors.HexColor("#5C6773"))
    c.drawCentredString(PAGE_W / 2, y, ar("المملكة العربية السعودية"))
    y -= 6 * mm
    c.setFont(FONT_BOLD, 12.5)
    c.setFillColor(colors.HexColor("#16213A"))
    c.drawCentredString(PAGE_W / 2, y, ar(ctx.school_name or ""))

    y -= 24 * mm
    c.setFont(FONT_BOLD, 21)
    c.setFillColor(colors.HexColor("#16213A"))
    title_line1 = ar("تقرير تحليل نتائج الطلاب")
    c.drawCentredString(PAGE_W / 2, y, title_line1)
    y -= 9 * mm
    c.setFont(FONT_BOLD, 16)
    title_line2 = ar(ctx.grade_title or "")
    c.drawCentredString(PAGE_W / 2, y, title_line2)

    y -= 11 * mm
    c.setFont(FONT_BOLD, 12.5)
    c.setFillColor(colors.HexColor("#2E6DA4"))
    sub = ar(f"{ctx.semester} — العام الدراسي {ctx.academic_year}".strip(" —"))
    c.drawCentredString(PAGE_W / 2, y, sub)

    # صندوق المعلومات الوصفية بالأسفل
    box_h = 42 * mm
    box_y = 32 * mm
    box_x = MARGIN
    box_w = PAGE_W - 2 * MARGIN
    c.setFillColor(colors.HexColor("#F6F8FB"))
    c.setStrokeColor(colors.HexColor("#E8ECF2"))
    c.roundRect(box_x, box_y, box_w, box_h, 4 * mm, fill=1, stroke=1)

    rows = [
        ("إعداد", f"{ctx.prepared_by_name} — {ctx.prepared_by_role}".strip(" —")),
        ("مدير المدرسة", ctx.principal_name),
        ("تاريخ الإصدار", datetime.date.today().strftime("%Y/%m/%d")),
    ]
    row_y = box_y + box_h - 11 * mm
    for label, value in rows:
        if not value:
            row_y -= 11 * mm
            continue
        c.setFont(FONT_REGULAR, 9)
        c.setFillColor(colors.HexColor("#8893A1"))
        c.drawRightString(box_x + box_w - 10 * mm, row_y, ar(label))
        c.setFont(FONT_BOLD, 11.5)
        c.setFillColor(colors.HexColor("#16213A"))
        c.drawRightString(box_x + box_w - 10 * mm, row_y - 5.2 * mm, ar(value))
        row_y -= 11 * mm

    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(colors.HexColor("#A4ADBA"))
    c.drawCentredString(PAGE_W / 2, 18 * mm,
                        ar("تم إنشاء هذا التقرير تلقائيًا عبر برنامج ميزان لتحليل نتائج الطلاب"))

    c.restoreState()
    c.showPage()
