# -*- coding: utf-8 -*-
"""
نظام ألوان موحّد للتقديرات، يُستخدم في كل الجداول والرسوم البيانية والتقارير
بحيث يكون لكل تقدير لون ثابت ومميّز بغض النظر عن الثيم البصري النشط.
"""

GRADE_COLORS = {
    "ممتاز":     {"bg": "#E5F6ED", "fg": "#168249", "chart": "#1E9E6B"},
    "جيد جداً":   {"bg": "#EAF6E8", "fg": "#5B9C2F", "chart": "#7CC142"},
    "جيد جدا":   {"bg": "#EAF6E8", "fg": "#5B9C2F", "chart": "#7CC142"},
    "جيد":       {"bg": "#FCF6DC", "fg": "#B8932A", "chart": "#D4AF37"},
    "مقبول":     {"bg": "#FDEEDC", "fg": "#C8702A", "chart": "#E08A3C"},
    "ضعيف":      {"bg": "#FBE9E9", "fg": "#C0392B", "chart": "#D6453D"},
}

DEFAULT_COLOR = {"bg": "#F0F1F3", "fg": "#6B7785", "chart": "#9aa3ad"}

# ترتيب التقديرات من الأعلى للأدنى (لاستخدامه في الفرز والرسوم البيانية)
GRADE_ORDER = ["ممتاز", "جيد جداً", "جيد", "مقبول", "ضعيف"]


def _normalize(grade_label):
    if not grade_label:
        return None
    g = str(grade_label).strip()
    # توحيد الكتابتين الشائعتين لـ "جيد جداً"
    if g in ("جيد جدا", "جيد جداً"):
        return "جيد جداً"
    return g


def get_grade_color(grade_label, kind="fg"):
    """
    يرجع لون التقدير المطلوب: kind = 'bg' | 'fg' | 'chart'.
    لو التقدير غير معروف، يرجع لون افتراضي رمادي محايد.
    """
    g = _normalize(grade_label)
    palette = GRADE_COLORS.get(g, DEFAULT_COLOR)
    return palette.get(kind, DEFAULT_COLOR[kind])


def grade_sort_key(grade_label):
    """مفتاح فرز يضع 'ممتاز' أولاً و'ضعيف' أخيرًا؛ تقديرات غير معروفة تُوضع بالنهاية."""
    g = _normalize(grade_label)
    try:
        return GRADE_ORDER.index(g)
    except ValueError:
        return len(GRADE_ORDER)
