# -*- coding: utf-8 -*-
"""ثيم بصري لتطبيق ميزان - الجوال. نفس ألوان نسخة سطح المكتب (ميزان الأصلي)."""

COLOR_SIDEBAR_BG = "#0D3B2E"
COLOR_SIDEBAR_TEXT = "#CFE6D9"
COLOR_SIDEBAR_TEXT_MUTED = "#7FA690"
COLOR_ACCENT = "#1E9E6B"
COLOR_ACCENT_DARK = "#168249"
COLOR_ACCENT_FG = "#FFFFFF"

COLOR_BG = "#F7F8FA"
COLOR_CARD_BG = "#FFFFFF"
COLOR_CARD_BORDER = "#EAEDF1"
COLOR_TEXT_PRIMARY = "#1B2330"
COLOR_TEXT_SECONDARY = "#6B7785"
COLOR_TEXT_MUTED = "#9aa3ad"

COLOR_GREEN_BG = "#E5F6ED"
COLOR_GREEN_FG = "#1E9E6B"
COLOR_GOLD_BG = "#FCF1DC"
COLOR_GOLD_FG = "#C8932B"
COLOR_RED_BG = "#FBE9E9"
COLOR_RED_FG = "#D6453D"
COLOR_BLUE_BG = "#E7F0FC"
COLOR_BLUE_FG = "#2A6FD6"

COLOR_CHART_GREEN_DARK = "#0D3B2E"
COLOR_CHART_GREEN_LIGHT = "#3DBE8B"
COLOR_CHART_GRAY_LIGHT = "#C8E6D6"

FONT_REGULAR = "NotoArabic"
FONT_BOLD = "NotoArabicBold"


def hex_to_rgba(hex_color, alpha=1.0):
    """يحوّل '#RRGGBB' إلى tuple (r,g,b,a) بمدى 0-1 المستخدم في Kivy."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b, alpha)
