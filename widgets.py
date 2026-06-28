# -*- coding: utf-8 -*-
"""مكوّنات واجهة قابلة لإعادة الاستخدام لتطبيق الجوال، بدعم تلقائي للنص العربي."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

import theme
from core.arabic_text import ar


def ALabel(text="", **kwargs):
    """Label يعيد تشكيل النص العربي تلقائيًا، بمحاذاة يمين افتراضية (RTL)."""
    kwargs.setdefault("halign", "right")
    kwargs.setdefault("valign", "middle")
    kwargs.setdefault("font_name", theme.FONT_REGULAR)
    kwargs.setdefault("color", theme.hex_to_rgba(theme.COLOR_TEXT_PRIMARY))
    lbl = Label(text=ar(text), **kwargs)
    lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
    return lbl


def AButton(text="", **kwargs):
    """Button يعيد تشكيل النص العربي تلقائيًا."""
    kwargs.setdefault("font_name", theme.FONT_REGULAR)
    btn = Button(text=ar(text), **kwargs)
    return btn


def safe_chart_widget(build_fn, *args, **kwargs):
    """
    يستدعي دالة بناء رسم بياني (تستخدم matplotlib) بأمان. لو فشلت (مثلاً
    matplotlib غير متاح بشكل صحيح على بعض أجهزة أندرويد)، يرجع تنبيه نصي
    بدل تعطّل الشاشة كاملة. استخدم هذا الغلاف بكل مكان يُبنى فيه رسم بياني.
    """
    try:
        return build_fn(*args, **kwargs)
    except Exception as e:
        box = ColoredBoxLayout(bg_hex="#FBE9E9", radius=dp(8), padding=dp(10),
                                size_hint_y=None, height=dp(60))
        box.add_widget(ALabel(text=f"تعذّر عرض الرسم البياني ({e})", font_size="10sp",
                               color=theme.hex_to_rgba(theme.COLOR_RED_FG)))
        return box


class ColoredBoxLayout(BoxLayout):
    """BoxLayout بخلفية لون مصمتة (Kivy لا يدعم هذا افتراضيًا)."""
    def __init__(self, bg_hex="#FFFFFF", radius=0, **kwargs):
        super().__init__(**kwargs)
        self._bg_hex = bg_hex
        self._radius = radius
        with self.canvas.before:
            self._color = Color(*theme.hex_to_rgba(bg_hex))
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def set_bg(self, hex_color):
        self._color.rgba = theme.hex_to_rgba(hex_color)


class Card(ColoredBoxLayout):
    """بطاقة بحدود وعنوان اختياري، تحتوي محتوى ديناميكي بالأسفل."""
    def __init__(self, title=None, subtitle=None, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", dp(14))
        kwargs.setdefault("spacing", dp(8))
        super().__init__(bg_hex=theme.COLOR_CARD_BG, radius=dp(12), **kwargs)
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))

        if title:
            header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
            title_lbl = ALabel(text=title, font_size="16sp", bold=True)
            header.add_widget(title_lbl)
            self.add_widget(header)
            if subtitle:
                sub_lbl = ALabel(text=subtitle, font_size="11sp",
                                  color=theme.hex_to_rgba(theme.COLOR_TEXT_MUTED),
                                  size_hint_y=None, height=dp(18))
                self.add_widget(sub_lbl)

        self.body = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.body.bind(minimum_height=self.body.setter("height"))
        self.add_widget(self.body)


class KPICard(ColoredBoxLayout):
    """بطاقة مؤشر رقمي صغيرة (قيمة + تسمية)."""
    PALETTES = {
        "green": (theme.COLOR_GREEN_BG, theme.COLOR_GREEN_FG),
        "gold": (theme.COLOR_GOLD_BG, theme.COLOR_GOLD_FG),
        "red": (theme.COLOR_RED_BG, theme.COLOR_RED_FG),
        "blue": (theme.COLOR_BLUE_BG, theme.COLOR_BLUE_FG),
    }

    def __init__(self, value, label, palette="green", **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("padding", dp(12))
        kwargs.setdefault("spacing", dp(2))
        super().__init__(bg_hex=theme.COLOR_CARD_BG, radius=dp(10), **kwargs)
        self.size_hint_y = None
        self.height = dp(76)

        bg, fg = self.PALETTES.get(palette, self.PALETTES["green"])
        value_lbl = ALabel(text=str(value), font_size="20sp", bold=True,
                            color=theme.hex_to_rgba(theme.COLOR_TEXT_PRIMARY),
                            size_hint_y=0.6, halign="right")
        label_lbl = ALabel(text=label, font_size="11sp",
                            color=theme.hex_to_rgba(theme.COLOR_TEXT_SECONDARY),
                            size_hint_y=0.4, halign="right")
        self.add_widget(value_lbl)
        self.add_widget(label_lbl)


def build_table(headers, rows, col_widths=None, grade_col_index=None, raw_grades=None,
                 row_action_label=None, row_action_callback=None):
    """
    يبني جدول بسيط داخل ScrollView. headers/rows بترتيب القراءة من اليمين لليسار
    (نفس ترتيب نسخة سطح المكتب) — لذلك نعكسهم هنا لأن BoxLayout بـ Kivy يرصف
    من اليسار افتراضيًا.

    تنبيه مهم: مرّر كل النصوص بـ headers/rows **خامًا بدون تشكيل مسبق**
    (بدون استدعاء ar() عليها بنفسك). هذي الدالة تستخدم ALabel داخليًا لكل
    خلية، وALabel يطبّق ar() تلقائيًا. تطبيق ar() مرتين على نفس النص (مرة
    من المستدعي ومرة هنا) يكسر النص ويعرضه معكوسًا أو مشوّهًا.
    """
    from core.grade_colors import get_grade_color

    n_cols = len(headers) + (1 if row_action_callback else 0)
    if col_widths is None:
        col_widths = [1.0 / n_cols] * n_cols

    container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
    container.bind(minimum_height=container.setter("height"))

    header_row = ColoredBoxLayout(bg_hex=theme.COLOR_SIDEBAR_BG, orientation="horizontal",
                                   size_hint_y=None, height=dp(34), padding=(dp(4), 0))
    display_headers = list(reversed(headers))
    display_widths = list(reversed(col_widths[:len(headers)]))
    if row_action_callback:
        display_headers = [""] + display_headers
        display_widths = [col_widths[-1]] + display_widths
    for h, w in zip(display_headers, display_widths):
        header_row.add_widget(ALabel(text=h, font_size="11sp", bold=True,
                                      color=theme.hex_to_rgba("#FFFFFF"),
                                      size_hint_x=w, halign="center"))
    container.add_widget(header_row)

    for i, row_vals in enumerate(rows):
        bg = "#FAFBFC" if i % 2 == 0 else theme.COLOR_CARD_BG
        row_box = ColoredBoxLayout(bg_hex=bg, orientation="horizontal",
                                    size_hint_y=None, height=dp(38), padding=(dp(4), 0))
        display_vals = list(reversed(row_vals))
        display_widths_row = list(reversed(col_widths[:len(row_vals)]))

        if row_action_callback:
            btn = AButton(text=row_action_label or "تقرير", font_size="10sp",
                          size_hint_x=col_widths[-1],
                          background_color=theme.hex_to_rgba(theme.COLOR_ACCENT),
                          on_release=lambda inst, idx=i: row_action_callback(idx))
            display_vals = [btn] + display_vals
            display_widths_row = [col_widths[-1]] + display_widths_row

        n_data_cols = len(headers)
        for col_idx, (val, w) in enumerate(zip(display_vals, display_widths_row)):
            real_col_idx = n_data_cols - 1 - (col_idx - (1 if row_action_callback else 0))
            if row_action_callback and col_idx == 0:
                row_box.add_widget(val)
                continue
            fg_color = theme.COLOR_TEXT_PRIMARY
            bold = False
            if grade_col_index is not None and real_col_idx == grade_col_index:
                raw_grade = raw_grades[i] if raw_grades else val
                fg_color = get_grade_color(raw_grade, "fg")
                bold = True
            row_box.add_widget(ALabel(text=str(val), font_size="11sp", halign="center",
                                       bold=bold, color=theme.hex_to_rgba(fg_color),
                                       size_hint_x=w))
        container.add_widget(row_box)

    scroll = ScrollView(size_hint=(1, None))
    scroll.add_widget(container)
    return scroll, container
